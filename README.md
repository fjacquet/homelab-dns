# homelab-dns

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
![License](https://img.shields.io/badge/License-MIT-green)

Ansible-automated homelab infrastructure on 5 Dell Optiplex Micro machines: HA DNS, HTTPS reverse proxy with wildcard certs, WireGuard VPN, DHCP, ad blocking, and full monitoring stack.

## Architecture

```
                         ┌─────────────┐
                         │  Wingo IB4  │ WAN / NAT
                         │ 172.16.86.1 │ UDP 51820 → infra2
                         └──────┬──────┘
                                │ 172.16.86.0/24
          ┌─────────────────────┼─────────────────────┐
          │                     │                      │
   ┌──────┴──────┐      ┌──────┴──────┐      ┌───────┴───────┐
   │   infra1    │      │   infra2    │      │  MicroCloud   │
   │ .11 (opt1)  │      │ .12 (opt2)  │      │ .13/.14/.15   │
   ├─────────────┤      ├─────────────┤      ├───────────────┤
   │ DNS PRIMARY │      │ DNS SECOND. │      │ Prometheus    │
   │ Traefik  HA │◄─VIP─┤ Traefik  HA │      │ Grafana       │
   │ keepalived  │ .20  │ keepalived  │      │ Checkmk       │
   │ DHCP 80%    │      │ DHCP 20%    │      │ OVN + NFS     │
   │ DDNS cron   │      │ WireGuard   │      └───────┬───────┘
   └─────────────┘      └─────────────┘              │
                                              ┌──────┴──────┐
                                              │ Synology    │
                                              │ DS923+ .10  │
                                              │ NFS storage │
                                              │ HA/n8n/apps │
                                              └─────────────┘
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

| Playbook | Target | Description |
|----------|--------|-------------|
| `site.yml` | infra1 + infra2 | DNS, DHCP, Traefik, keepalived, WireGuard, monitoring exporters |
| `microcloud-prepare.yml` | opt3/4/5 | Base setup, snaps, NFS mounts, node_exporter |
| `microcloud-services.yml` | mc-node-01 | Prometheus, Grafana, Checkmk server + agents |

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

| Service | URL | Host |
|---------|-----|------|
| Technitium DNS | `https://dns.evlab.ch` | infra1 |
| Technitium DNS | `https://dns2.evlab.ch` | infra2 |
| Home Assistant | `https://homeassistant.evlab.ch` | Synology |
| n8n | `https://n8n.evlab.ch` | Synology |
| Stash | `https://stash.evlab.ch` | Synology |
| pgAdmin | `https://pgadmin.evlab.ch` | Synology |
| NAS (DSM) | `https://nas.evlab.ch` | Synology |
| Grafana | `https://grafana.evlab.ch` | mc-node-01 |
| Prometheus | `https://prometheus.evlab.ch` | mc-node-01 |
| Checkmk | `https://checkmk.evlab.ch` | mc-node-01 |

All services behind Traefik HA (VIP `172.16.86.20`) with Let's Encrypt wildcard cert `*.evlab.ch`.

## Key Design Decisions

- **No Ceph** — NFS from Synology for MicroCloud storage (simple, sufficient for homelab)
- **WireGuard native** — kernel module, not Docker (simpler, more reliable)
- **Technitium in Docker** — no .deb package available, `network_mode: host` for DHCP broadcast
- **keepalived VIP** — sub-10s failover vs DNS round-robin (minutes)
- **Dual monitoring** — Prometheus/Grafana (metrics) + Checkmk (SNMP, auto-discovery, alerting)

See [Architecture Decision Records](docs/ARD.md) for full rationale.

## Documentation

| Document | Description |
|----------|-------------|
| [PRD](docs/PRD.md) | Product Requirements — goals, functional & non-functional requirements |
| [ARD](docs/ARD.md) | Architecture Decision Records — 9 key decisions with rationale |
| [User Guide](docs/USER-GUIDE.md) | Operations, maintenance, troubleshooting, day-2 procedures |

## Project Structure

```
homelab-dns/
├── README.md
├── .gitignore
├── ansible.cfg
├── inventory.yml
├── site.yml                     # Infra playbook (DNS/HTTPS/VPN/DHCP)
├── microcloud-prepare.yml       # MicroCloud node preparation
├── microcloud-services.yml      # Monitoring stack (Prometheus/Grafana/Checkmk)
├── group_vars/
│   └── all/
│       ├── main.yml             # Variables (IPs, DNS records, services)
│       └── vault.yml            # Encrypted secrets (ansible-vault)
├── templates/                   # Jinja2 templates
│   ├── technitium-compose.yml.j2
│   ├── traefik-static.yml.j2
│   ├── traefik-compose.yml.j2
│   ├── traefik-services.yml.j2
│   ├── keepalived.conf.j2
│   ├── check-traefik.sh.j2
│   ├── sync-acme.sh.j2
│   ├── wg0.conf.j2
│   ├── wg-client.conf.j2
│   ├── netplan-infra.yml.j2
│   ├── update-ddns.sh.j2
│   └── backup-infra.sh.j2
└── docs/
    ├── PRD.md
    ├── ARD.md
    └── USER-GUIDE.md
```

## License

MIT
