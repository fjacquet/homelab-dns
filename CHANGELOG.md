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

### Changed

- Docker installation switched from `get.docker.com` script to official APT repository (GPG key + docker-ce packages)
- All Technitium API calls converted from GET+token-in-URL to POST+token-in-body
- iptables rules replaced with template-rendered `/etc/iptables/rules.v4` + `iptables-restore` (idempotent)
- ACME cert sync increased from hourly to every 5 minutes, with syslog logging and `StrictHostKeyChecking=yes`
- Container images pinned: technitium:14, traefik:v3.6, prometheus:v3, grafana:11, checkmk:2.3, n8n:1
- `dns_primary_ip`/`dns_secondary_ip` derived from inventory via `hostvars` (no more manual duplication)
- Node exporter tasks extracted into shared `roles/node_exporter/` (was duplicated in site.yml and microcloud-prepare.yml)
- Webhook container: enabled `host_key_checking`, pre-populated `known_hosts` via `ssh-keyscan`
- Prometheus Traefik scrape: replaced `insecure_skip_verify` with proper `ca_file` TLS validation
- ansible-lint pinned to `>=25,<26` in CI; molecule `continue-on-error` removed
- NFS mount point creation now skips already-mounted paths (fixes `EPERM` on re-run)

### Security

- Secrets (Technitium password, Infomaniak token) moved from Docker Compose templates to `.env` files with mode `0600`
- `no_log: true` added to all 12 Technitium/DHCP API tasks
- Webhook engine: startup fails if `WEBHOOK_API_KEY` is empty (was fail-open with HTTP 500)
- Webhook engine: `tags` and `limit` fields validated with regex allowlists
- Webhook engine: job store capped at `MAX_JOBS=200` with eviction; log lines capped at `MAX_LOG_LINES=1000`
- Webhook engine: healthcheck added to Docker Compose definitions
- Unused Docker socket mount removed from Traefik (file provider only)
- `acme.json` pre-created with mode `0600` to prevent Traefik permission errors

### Fixed

- LXD evacuate/restore uses `mc_hostname` instead of `inventory_hostname` (was using wrong cluster member name)
- Docker daemon verification task now skipped on MicroCloud nodes (no Docker installed)
- WireGuard kernel module only loaded on infra2 (was unnecessarily loaded on both nodes)
- Debug tasks no longer print literal vault variable names
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
