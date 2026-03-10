# homelab-dns Project Overview

## Purpose

Ansible-automated homelab infrastructure on 5 Dell Optiplex Micro nodes (Ubuntu 24.04 LTS).
Deploys: HA DNS (Technitium), HTTPS reverse proxy (Traefik + keepalived), WireGuard VPN, DHCP, monitoring (Prometheus/Grafana/Checkmk).
Domain: `evlab.ch`, Network: `172.16.86.0/24`.

## Tech Stack

- **Ansible** (primary): playbooks, Jinja2 templates, FQCN everywhere
- **Python 3.12+**: FastAPI webhook engine (`ansible-webhook/main.py`), CLI tools (`tools/`)
- **Docker Compose**: Technitium, Traefik, Prometheus, Grafana, Checkmk, n8n
- **MkDocs Material**: documentation site
- **uv**: Python tooling (PEP 723 inline metadata)

## Structure

```
site.yml                    — Main infra playbook (DNS, DHCP, Traefik, WireGuard, monitoring)
update.yml                  — OS patch management
update-containers.yml       — Container image updates
microcloud-prepare.yml      — MicroCloud node prep
microcloud-services.yml     — Monitoring + automation stack
inventory.yml               — Host definitions
group_vars/all/main.yml     — Shared variables
group_vars/all/vault.yml    — Encrypted secrets (ansible-vault)
templates/                  — Jinja2 templates for all services
ansible-webhook/            — FastAPI webhook engine (main.py, Dockerfile, docker-compose.yml)
tools/                      — Python CLI tools (ansible_ai.py, serve-docs.py)
docs/                       — MkDocs site source
.github/workflows/          — CI (lint.yml, docs.yml)
```

## Hosts

- `dns_primary` (opt1/infra1, 172.16.86.11): primary DNS, Traefik MASTER
- `dns_secondary` (opt2/infra2, 172.16.86.12): secondary DNS, Traefik BACKUP, WireGuard
- `microcloud` (opt3-5, 172.16.86.13-15): MicroCloud cluster
