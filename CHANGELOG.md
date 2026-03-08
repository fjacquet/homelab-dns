# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- `ansible-webhook/` — containerized FastAPI webhook engine: `POST /run` triggers Ansible playbooks asynchronously (202 + job_id), `GET /status/{job_id}` polls results, `GET /playbooks` lists available playbooks, Swagger UI at `/docs`; deploys on Synology alongside n8n
- ADR-015: Ansible Webhook Engine (FastAPI + Docker)
- `ansible.evlab.ch` Traefik service and DNS entry for webhook engine
- `update.yml` — standalone OS patch management playbook: apt dist-upgrade on all 5 nodes (`serial: 1`), conditional reboot via `/var/run/reboot-required`, LXD evacuate/restore for MicroCloud nodes, post-reboot service health checks (Docker, Technitium, Traefik, LXD, NFS)
- `update-containers.yml` — standalone container/binary update playbook: node_exporter binary upgrade on all nodes, Technitium/Traefik/cAdvisor image pull + recreate on dns_servers, Prometheus/Grafana/Checkmk image pull + recreate on microcloud[0], with post-update health checks
- ADR-014: Separate OS and Container Patch Management Playbooks
- PiKVM DHCP reservation (172.16.86.3) and DNS records
- WireGuard client installation guide (iPhone + macOS) in User Guide
- Troubleshooting: ad blocking not working (blocklist download)
- Troubleshooting: DHCP wrong IP (missing reservations on secondary)
- Troubleshooting: systemd-resolved blocking port 53

### Fixed

- DHCP reservations now deployed on **both** servers (was primary-only, causing wrong IPs when infra2 responded first)
- `/opt/docker/ddns` directory created on both infra nodes (was primary-only, causing backup script deployment failure on infra2)
- Netplan templates use `{{ wireguard_interface }}` variable instead of hardcoded `enp1s0`

## [1.0.0] - 2026-03-07

### Added

- Ansible playbooks for full infrastructure automation (`site.yml`)
- Technitium DNS (HA primary/secondary) with zone transfer (AXFR)
- Traefik v3 reverse proxy with Let's Encrypt wildcard cert (`*.evlab.ch`)
- keepalived VIP (172.16.86.20) for Traefik HA failover
- WireGuard VPN (native kernel module) on infra2
- DHCP split-scope (80/20) with MAC reservations
- Ad blocking via StevenBlack + OISD + Hagezi blocklists
- MicroCloud preparation playbook (`microcloud-prepare.yml`)
- Monitoring stack playbook (`microcloud-services.yml`): Prometheus, Grafana, Checkmk
- Node exporter, cAdvisor, WireGuard exporter
- NFS mounts from Synology (datastore + isofiles)
- Netplan templates for infra and MicroCloud nodes
- DDNS update cron (Infomaniak API)
- Nightly backup cron
- iptables firewall rules (Technitium UI + Traefik API restricted to localhost)
- ACME certificate sync from primary to secondary
- Documentation: PRD, ARD (9 decisions), User Guide, README with badges
