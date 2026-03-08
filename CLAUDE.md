# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Ansible-automated homelab infrastructure on 5 Dell Optiplex Micro machines running Ubuntu 24.04 LTS. Deploys HA DNS (Technitium), HTTPS reverse proxy with wildcard certs (Traefik + keepalived), WireGuard VPN, DHCP, ad blocking, and monitoring (Prometheus/Grafana + Checkmk).

Domain: `evlab.ch`. Network: `172.16.86.0/24`.

## Prerequisites

```bash
brew install ansible
ansible-galaxy collection install -r requirements.yml  # community.docker, community.general, ansible.posix
echo 'your-vault-password' > ~/.vault_pass && chmod 600 ~/.vault_pass
```

SSH access required to all target hosts before running any playbook.

## Key Commands

```bash
# Full infra deployment (infra1 + infra2)
ansible-playbook -i inventory.yml site.yml

# Dry-run
ansible-playbook -i inventory.yml site.yml --check --diff

# Deploy by phase/tag
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
ansible-playbook -i inventory.yml site.yml --tags verify  # smoke tests

# MicroCloud nodes (opt3/4/5)
ansible-playbook -i inventory.yml microcloud-prepare.yml
ssh fjacquet@172.16.86.13 "sudo microcloud init"  # interactive, must run manually
ansible-playbook -i inventory.yml microcloud-services.yml

# Vault management
ansible-vault edit group_vars/all/vault.yml
```

## Architecture

### Inventory Groups

- `dns_primary` → opt1 / infra1 (`172.16.86.11`): primary DNS, Traefik (MASTER), DDNS cron
- `dns_secondary` → opt2 / infra2 (`172.16.86.12`): secondary DNS, Traefik (BACKUP), WireGuard
- `dns_servers` → parent group containing both of the above
- `microcloud` → opt3/4/5 (`172.16.86.13-15`): MicroCloud cluster nodes

### Playbooks

| Playbook | Targets | Purpose |
|---|---|---|
| `site.yml` | `dns_servers` | All infra: DNS, DHCP, Traefik, keepalived, WireGuard, monitoring exporters |
| `microcloud-prepare.yml` | `microcloud` | Base setup, snaps, NFS mounts, node_exporter |
| `microcloud-services.yml` | `microcloud[0]` (mc-node-01) | Prometheus, Grafana, Checkmk server + agents |

### Service Architecture

- **Traefik HA**: VIP `172.16.86.20` via keepalived VRRP. Wildcard cert `*.evlab.ch` via Infomaniak DNS-01 challenge. Traefik runs on both infra nodes; primary is MASTER. ACME cert synced from primary to secondary via hourly cron (`sync-acme.sh`).
- **Technitium DNS**: Docker (`network_mode: host`) on both nodes. Primary/secondary zone replication via zone transfer. DHCP split-scope: infra1 handles `.100-.179`, infra2 handles `.180-.200`.
- **WireGuard**: Native kernel module (not Docker) on infra2 only. Port 51820 UDP. Internal subnet `10.13.13.0/24`. Client configs + QR codes at `/etc/wireguard/clients/` on infra2.
- **Monitoring**: Prometheus + Grafana on mc-node-01 (`172.16.86.13`). Checkmk server also on mc-node-01. Node exporters, cAdvisor, and WireGuard exporter on infra nodes.

### Variables

- `group_vars/all/main.yml`: All non-secret variables (IPs, ports, DNS records, DHCP reservations, service definitions)
- `group_vars/all/vault.yml`: Ansible Vault encrypted secrets (passwords, API tokens, WireGuard keys)
- Host-specific vars (`dhcp_range_start`, `dhcp_range_end`, `infra_hostname`, `infra_ip`) are in `inventory.yml`

Vault vars follow the pattern `vault_*` and are referenced from `main.yml`.

### Templates

All Jinja2 templates in `templates/`. Key ones:

- `technitium-compose.yml.j2`: Technitium Docker Compose
- `traefik-compose.yml.j2`, `traefik-static.yml.j2`, `traefik-services.yml.j2`: Traefik stack
- `keepalived.conf.j2`: VRRP config (priority differs per host via `inventory_hostname` checks)
- `wg0.conf.j2`: WireGuard server config; `wg-client.conf.j2`: per-peer client configs
- `netplan-infra.yml.j2`: Network config for infra nodes (NIC: `enp0s31f6`)

### Primary-Only vs Both-Node Logic

Several tasks use `when: inventory_hostname in groups['dns_primary']` or `groups['dns_secondary']` to differentiate behavior. Traefik directories, DDNS cron, and ACME sync only run on primary; WireGuard only on secondary.

### Port Reference

| Port | Service | Notes |
|---|---|---|
| 5380 | Technitium Web UI | Firewalled — only localhost + infra1→infra2 |
| 8080 | Traefik API | Firewalled — only localhost (keepalived health check) |
| 9100 | node_exporter | All nodes |
| 9101 | cAdvisor | Infra nodes |
| 9586 | WireGuard exporter | infra2 only |
| 51820/UDP | WireGuard | infra2 only |
