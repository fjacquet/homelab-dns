# homelab-dns

Ansible-automated homelab infrastructure on 5 Dell Optiplex Micro machines: HA DNS, HTTPS reverse proxy with wildcard certs, WireGuard VPN, DHCP, ad blocking, and full monitoring stack.

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
        MC_OVN["OVN + NFS"]
    end

    MC_OVN --> NAS

    subgraph NAS["Synology DS923+ — .10"]
        NAS_NFS["NFS storage"]
        NAS_APPS["HA / n8n / apps"]
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

## Key Design Decisions

- **No Ceph** — NFS from Synology for MicroCloud storage (simple, sufficient for homelab)
- **WireGuard native** — kernel module, not Docker (simpler, more reliable)
- **Technitium in Docker** — no .deb package available, `network_mode: host` for DHCP broadcast
- **keepalived VIP** — sub-10s failover vs DNS round-robin (minutes)
- **Dual monitoring** — Prometheus/Grafana (metrics) + Checkmk (SNMP, auto-discovery, alerting)

See [Architecture Decision Records](adr/index.md) for full rationale.
