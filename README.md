# homelab-dns

[![Ansible Quality](https://github.com/fjacquet/homelab-dns/actions/workflows/lint.yml/badge.svg)](https://github.com/fjacquet/homelab-dns/actions/workflows/lint.yml)
[![Deploy docs](https://github.com/fjacquet/homelab-dns/actions/workflows/docs.yml/badge.svg)](https://github.com/fjacquet/homelab-dns/actions/workflows/docs.yml)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://fjacquet.github.io/homelab-dns)
![Ansible](https://img.shields.io/badge/Ansible-2.17+-EE0000?logo=ansible&logoColor=white)
![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04_LTS-E95420?logo=ubuntu&logoColor=white)
![Technitium](https://img.shields.io/badge/DNS-Technitium-0078D4)
![Traefik](https://img.shields.io/badge/Proxy-Traefik_v3-24A1C1?logo=traefikproxy&logoColor=white)
![WireGuard](https://img.shields.io/badge/VPN-WireGuard-88171A?logo=wireguard&logoColor=white)
![Let's Encrypt](https://img.shields.io/badge/TLS-Let's_Encrypt-003A70?logo=letsencrypt&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Prometheus](https://img.shields.io/badge/Metrics-Prometheus-E6522C?logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Dashboards-Grafana-F46800?logo=grafana&logoColor=white)
![Checkmk](https://img.shields.io/badge/Monitoring-Checkmk-15D1A0)
![n8n](https://img.shields.io/badge/Automation-n8n-EA4B71?logo=n8n&logoColor=white)
![FastAPI](https://img.shields.io/badge/Webhook-FastAPI-009688?logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

Ansible-automated homelab infrastructure on 5 Dell Optiplex Micro machines: HA DNS, HTTPS reverse proxy with wildcard certs, WireGuard VPN, DHCP, ad blocking, monitoring stack, and event-driven automation via n8n + Ansible webhook engine.

## Architecture

```mermaid
graph TD
    WAN["<b>Wingo IB4</b><br/>172.16.86.1<br/>WAN / NAT<br/>UDP 51820 → infra2"]

    WAN -->|172.16.86.0/24| infra1
    WAN -->|172.16.86.0/24| infra2
    WAN -->|172.16.86.0/24| MC

    subgraph infra1["infra1 — .11 (opt1)"]
        I1_DNS["DNS PRIMARY"]
        I1_TRAEFIK["Traefik HA"]
        I1_KA["keepalived"]
        I1_DHCP["DHCP 80%"]
        I1_DDNS["DDNS cron"]
    end

    subgraph infra2["infra2 — .12 (opt2)"]
        I2_DNS["DNS SECONDARY"]
        I2_TRAEFIK["Traefik HA"]
        I2_KA["keepalived"]
        I2_DHCP["DHCP 20%"]
        I2_WG["WireGuard"]
    end

    I1_TRAEFIK <-->|"VIP .20"| I2_TRAEFIK

    subgraph MC["MicroCloud — .13/.14/.15"]
        MC_PROM["Prometheus"]
        MC_GRAF["Grafana"]
        MC_CHK["Checkmk"]
        MC_N8N["n8n"]
        MC_WH["ansible-webhook"]
        MC_OVN["OVN + NFS"]
    end

    MC_OVN --> NAS

    subgraph NAS["Synology DS923+ — .10"]
        NAS_NFS["NFS storage"]
        NAS_APPS["HA / apps"]
    end

    style WAN fill:#f9f,stroke:#333,stroke-width:2px
    style infra1 fill:#e6f3ff,stroke:#0078D4,stroke-width:2px
    style infra2 fill:#e6f3ff,stroke:#0078D4,stroke-width:2px
    style MC fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style NAS fill:#fff3e0,stroke:#ff9800,stroke-width:2px
```

## Quick Start

```bash
# Prerequisites
brew install ansible
ssh-copy-id fjacquet@172.16.86.{11,12,13,14,15}

# Configure secrets
echo 'your-vault-password' > ~/.vault_pass && chmod 600 ~/.vault_pass
ansible-vault edit group_vars/all/vault.yml

# Deploy infrastructure (infra1 + infra2)
ansible-playbook -i inventory.yml site.yml

# Deploy MicroCloud nodes
ansible-playbook -i inventory.yml microcloud-prepare.yml
ssh fjacquet@172.16.86.13 "sudo microcloud init"  # interactive
ansible-playbook -i inventory.yml microcloud-services.yml
```

## Playbooks

```mermaid
graph LR
    subgraph Playbooks
        SITE["<b>site.yml</b>"]
        MCP["<b>microcloud-prepare.yml</b>"]
        MCS["<b>microcloud-services.yml</b>"]
    end

    subgraph Targets
        I1I2["infra1 + infra2"]
        OPT["opt3 / opt4 / opt5"]
        MC1["mc-node-01"]
    end

    SITE -->|"DNS, DHCP, Traefik,<br/>keepalived, WireGuard,<br/>monitoring exporters"| I1I2
    MCP -->|"Base setup, snaps,<br/>NFS mounts, node_exporter"| OPT
    MCS -->|"Prometheus, Grafana, Checkmk,<br/>n8n, ansible-webhook"| MC1

    style SITE fill:#e6f3ff,stroke:#0078D4
    style MCP fill:#e8f5e9,stroke:#4caf50
    style MCS fill:#fff3e0,stroke:#ff9800
```

### Phase-by-Phase Deployment

```bash
# Infrastructure
ansible-playbook -i inventory.yml site.yml --tags base
ansible-playbook -i inventory.yml site.yml --tags docker
ansible-playbook -i inventory.yml site.yml --tags technitium
ansible-playbook -i inventory.yml site.yml --tags dns_records
ansible-playbook -i inventory.yml site.yml --tags traefik
ansible-playbook -i inventory.yml site.yml --tags keepalived
ansible-playbook -i inventory.yml site.yml --tags iptables
ansible-playbook -i inventory.yml site.yml --tags dhcp
ansible-playbook -i inventory.yml site.yml --tags wireguard
ansible-playbook -i inventory.yml site.yml --tags cron
ansible-playbook -i inventory.yml site.yml --tags monitoring
ansible-playbook -i inventory.yml site.yml --tags verify

# Dry-run
ansible-playbook -i inventory.yml site.yml --check --diff
```

## Services

All services behind Traefik HA (VIP `172.16.86.20`) with Let's Encrypt wildcard cert `*.evlab.ch`.

```mermaid
graph TD
    TRAEFIK["<b>Traefik HA</b><br/>VIP 172.16.86.20<br/>*.evlab.ch wildcard cert"]

    subgraph infra["Infrastructure"]
        DNS1["Technitium DNS<br/>dns.evlab.ch<br/><i>infra1</i>"]
        DNS2["Technitium DNS<br/>dns2.evlab.ch<br/><i>infra2</i>"]
    end

    subgraph synology["Synology DS923+"]
        HA["Home Assistant<br/>homeassistant.evlab.ch"]
        STASH["Stash<br/>stash.evlab.ch"]
        PGA["pgAdmin<br/>pgadmin.evlab.ch"]
        DSM["NAS DSM<br/>nas.evlab.ch"]
    end

    subgraph microcloud["MicroCloud (mc-node-01)"]
        GRAF["Grafana<br/>grafana.evlab.ch"]
        PROM["Prometheus<br/>prometheus.evlab.ch"]
        CHK["Checkmk<br/>checkmk.evlab.ch"]
        N8N["n8n<br/>n8n.evlab.ch"]
        AW["Ansible Webhook<br/>ansible.evlab.ch"]
    end

    TRAEFIK --> DNS1 & DNS2
    TRAEFIK --> HA & STASH & PGA & DSM
    TRAEFIK --> GRAF & PROM & CHK & N8N & AW

    style TRAEFIK fill:#24A1C1,stroke:#333,color:#fff,stroke-width:2px
    style infra fill:#e6f3ff,stroke:#0078D4,stroke-width:2px
    style synology fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    style microcloud fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
```

## Key Design Decisions

- **No Ceph** — NFS from Synology for MicroCloud storage (simple, sufficient for homelab)
- **WireGuard native** — kernel module, not Docker (simpler, more reliable)
- **Technitium in Docker** — no .deb package available, `network_mode: host` for DHCP broadcast
- **keepalived VIP** — sub-10s failover vs DNS round-robin (minutes)
- **Dual monitoring** — Prometheus/Grafana (metrics) + Checkmk (SNMP, auto-discovery, alerting)
- **Event-driven automation** — n8n + FastAPI webhook engine on MicroCloud; n8n calls `POST /run` to trigger any Ansible playbook asynchronously
- **Separate patch playbooks** — `update.yml` (OS + reboot) and `update-containers.yml` (images + node_exporter) run independently

See [Architecture Decision Records](https://fjacquet.github.io/homelab-dns/adr/index/) for full rationale.

## Documentation

```mermaid
graph LR
    DOCS["<b>Documentation</b>"]

    PRD["<b>PRD</b><br/>Product Requirements<br/>Goals, functional &<br/>non-functional requirements"]
    ARD["<b>ARD</b><br/>Architecture Decisions<br/>9 key decisions<br/>with rationale"]
    UG["<b>User Guide</b><br/>Operations, maintenance,<br/>troubleshooting,<br/>day-2 procedures"]

    DOCS --> PRD & ARD & UG

    click PRD "docs/PRD.md"
    click ARD "docs/ARD.md"
    click UG "docs/USER-GUIDE.md"

    style DOCS fill:#f5f5f5,stroke:#333,stroke-width:2px
    style PRD fill:#e6f3ff,stroke:#0078D4
    style ARD fill:#e8f5e9,stroke:#4caf50
    style UG fill:#fff3e0,stroke:#ff9800
```

## Project Structure

```mermaid
graph TD
    ROOT["<b>homelab-dns/</b>"]

    ROOT --- CFG["ansible.cfg<br/>inventory.yml<br/>.gitignore"]
    ROOT --- PB["<b>Playbooks</b>"]
    ROOT --- GV["<b>group_vars/all/</b>"]
    ROOT --- TPL["<b>templates/</b>"]
    ROOT --- DOC["<b>docs/</b>"]
    ROOT --- TOOLS["<b>tools/</b>"]

    PB --- S["site.yml<br/><i>DNS/HTTPS/VPN/DHCP</i>"]
    PB --- MP["microcloud-prepare.yml<br/><i>Node preparation</i>"]
    PB --- MS["microcloud-services.yml<br/><i>Prometheus/Grafana/Checkmk</i>"]

    GV --- MV["main.yml<br/><i>Variables</i>"]
    GV --- VV["vault.yml<br/><i>Encrypted secrets</i>"]

    TPL --- T1["technitium-compose.yml.j2"]
    TPL --- T2["traefik-*.yml.j2"]
    TPL --- T3["keepalived.conf.j2"]
    TPL --- T4["wg0.conf.j2 / wg-client.conf.j2"]
    TPL --- T5["netplan / ddns / backup .j2"]

    DOC --- D1["PRD.md"]
    DOC --- D2["ARD.md"]
    DOC --- D3["USER-GUIDE.md"]

    TOOLS --- AI["ansible_ai.py<br/><i>AI playbook generator</i>"]

    style ROOT fill:#f5f5f5,stroke:#333,stroke-width:2px
    style PB fill:#e6f3ff,stroke:#0078D4
    style GV fill:#e8f5e9,stroke:#4caf50
    style TPL fill:#fff3e0,stroke:#ff9800
    style DOC fill:#fce4ec,stroke:#e91e63
    style TOOLS fill:#f3e5f5,stroke:#9c27b0
```

## License

MIT
