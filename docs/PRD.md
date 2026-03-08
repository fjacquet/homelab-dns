# Product Requirements Document (PRD)

## Homelab DNS/HTTPS/VPN Infrastructure

**Version:** 1.0
**Date:** 2026-03-08
**Author:** Frederic Jacquet

---

## 1. Overview

Automated deployment of a complete homelab network infrastructure on 5 Dell Optiplex Micro machines running Ubuntu 24.04 LTS Server, managed by Ansible playbooks.

### 1.1 Problem Statement

The initial plan placed all network services (DNS, DHCP, reverse proxy, VPN) on a Synology DS923+ NAS. This failed due to:

- Port 53/80/443 conflicts with DSM
- Missing WireGuard kernel module
- Insufficient container capabilities (`NET_ADMIN`)
- Single Point of Failure — NAS reboot = total network outage
- DSM Container Manager silently strips capabilities

### 1.2 Solution

Dedicate 2 Optiplex Micro to network infrastructure (DNS, HTTPS, VPN) and 3 to MicroCloud (compute). The Synology reverts to pure NAS + application containers.

---

## 2. Goals

| ID | Goal | Priority |
|----|------|----------|
| G1 | HA DNS with automatic failover | P0 |
| G2 | HTTPS for all services via wildcard cert | P0 |
| G3 | VPN access from outside the home | P0 |
| G4 | DHCP with reservations for all devices | P0 |
| G5 | Ad blocking via DNS blocklists | P1 |
| G6 | Automated deployment via Ansible | P1 |
| G7 | Monitoring with alerting | P1 |
| G8 | Nightly backups to Synology | P1 |
| G9 | MicroCloud compute cluster | P2 |

---

## 3. Architecture

### 3.1 Hardware

| Machine | Role | IP |
|---------|------|----|
| opt1 (infra1) | DNS primary, Traefik MASTER, keepalived, DDNS | 172.16.86.11 |
| opt2 (infra2) | DNS secondary, Traefik BACKUP, keepalived, WireGuard | 172.16.86.12 |
| opt3 (mc-node-01) | MicroCloud bootstrap, Prometheus, Grafana, Checkmk | 172.16.86.13 |
| opt4 (mc-node-02) | MicroCloud compute | 172.16.86.14 |
| opt5 (mc-node-03) | MicroCloud compute | 172.16.86.15 |
| Synology DS923+ | NAS, application containers | 172.16.86.10 |
| VIP (keepalived) | Traefik HA floating IP | 172.16.86.20 |

### 3.2 Network

- **Subnet:** 172.16.86.0/24
- **Gateway:** 172.16.86.1 (Wingo IB4)
- **Domain:** evlab.ch (Infomaniak)
- **WireGuard subnet:** 10.13.13.0/24

### 3.3 Software Stack

| Component | Technology | Deployment |
|-----------|-----------|------------|
| DNS | Technitium DNS Server | Docker (network_mode: host) |
| Reverse Proxy | Traefik v3 | Docker |
| HA Failover | keepalived (VRRP) | Native (apt) |
| VPN | WireGuard | Native (wg-quick + systemd) |
| DHCP | Technitium built-in | Docker (same container) |
| Certificates | Let's Encrypt wildcard (DNS-01 via Infomaniak) | Traefik ACME |
| Monitoring | Prometheus + Grafana + Checkmk | Docker (MicroCloud) |
| Compute | MicroCloud (LXD + OVN) | Snap |
| Storage | NFS from Synology (no Ceph) | Native mount |

---

## 4. Functional Requirements

### 4.1 DNS (FR-DNS)

| ID | Requirement |
|----|-------------|
| FR-DNS-01 | Primary DNS on infra1 with authoritative zone `evlab.ch` |
| FR-DNS-02 | Secondary DNS on infra2 with AXFR zone transfer |
| FR-DNS-03 | Reverse DNS zone `86.16.172.in-addr.arpa` |
| FR-DNS-04 | Wildcard `*.evlab.ch` → VIP 172.16.86.20 |
| FR-DNS-05 | Explicit A records for all infrastructure devices |
| FR-DNS-06 | PTR records for all static IPs |
| FR-DNS-07 | DNS-over-HTTPS forwarding to Cloudflare + Google |
| FR-DNS-08 | Ad blocking via StevenBlack, OISD, Hagezi blocklists |

### 4.2 DHCP (FR-DHCP)

| ID | Requirement |
|----|-------------|
| FR-DHCP-01 | Split-scope: infra1 serves .100-.179 (80%), infra2 serves .180-.200 (20%) |
| FR-DHCP-02 | 24 DHCP reservations (MAC → IP) |
| FR-DHCP-03 | Push DNS servers (infra1, infra2) to clients |
| FR-DHCP-04 | 24h lease time |

### 4.3 HTTPS / Reverse Proxy (FR-HTTPS)

| ID | Requirement |
|----|-------------|
| FR-HTTPS-01 | Wildcard cert `*.evlab.ch` via Let's Encrypt DNS-01 |
| FR-HTTPS-02 | Automatic HTTP → HTTPS redirect |
| FR-HTTPS-03 | Traefik HA via keepalived VIP on both nodes |
| FR-HTTPS-04 | VIP failover in < 10 seconds |
| FR-HTTPS-05 | Certificate sync from infra1 to infra2 (hourly rsync) |
| FR-HTTPS-06 | Prometheus metrics endpoint enabled |

### 4.4 VPN (FR-VPN)

| ID | Requirement |
|----|-------------|
| FR-VPN-01 | WireGuard server on infra2, port UDP 51820 |
| FR-VPN-02 | Full tunnel (AllowedIPs = 0.0.0.0/0) |
| FR-VPN-03 | DNS via both Technitium servers |
| FR-VPN-04 | 3 client configs: iPhone, MacBook, iPad |
| FR-VPN-05 | QR code generation for mobile clients |
| FR-VPN-06 | DDNS update via Infomaniak API (5-min cron) |

### 4.5 Monitoring (FR-MON)

| ID | Requirement |
|----|-------------|
| FR-MON-01 | node_exporter on all 5 nodes (port 9100) |
| FR-MON-02 | cAdvisor on infra1/infra2 (port 9101) |
| FR-MON-03 | WireGuard exporter on infra2 (port 9586) |
| FR-MON-04 | Traefik Prometheus metrics |
| FR-MON-05 | Prometheus + Grafana on MicroCloud |
| FR-MON-06 | Checkmk for auto-discovery, SNMP, alerting |
| FR-MON-07 | Checkmk agents on all 5 nodes |

### 4.6 MicroCloud (FR-MC)

| ID | Requirement |
|----|-------------|
| FR-MC-01 | 3-node cluster (opt3, opt4, opt5) |
| FR-MC-02 | OVN networking |
| FR-MC-03 | NFS shared storage from Synology (datastore + isofiles) |
| FR-MC-04 | No Ceph (too complex for 3-node homelab) |

### 4.7 Backup (FR-BAK)

| ID | Requirement |
|----|-------------|
| FR-BAK-01 | Nightly backup at 02:00 to Synology via rsync |
| FR-BAK-02 | infra1: Technitium config, Traefik config + certs, keepalived |
| FR-BAK-03 | infra2: Technitium config, Traefik config + certs, WireGuard |
| FR-BAK-04 | 30-day retention |

---

## 5. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-01 | All deployment automated via Ansible (idempotent) |
| NFR-02 | Secrets managed via Ansible Vault |
| NFR-03 | Phase-by-phase deployment via Ansible tags |
| NFR-04 | Dry-run support (`--check --diff`) |
| NFR-05 | Infrastructure services excluded from Watchtower |
| NFR-06 | Ports 5380 and 8080 locked to localhost via iptables |
| NFR-07 | VRRP traffic allowed between infra1 and infra2 |

---

## 6. Services Matrix

| Service | URL | Backend | Host |
|---------|-----|---------|------|
| Home Assistant | homeassistant.evlab.ch | 172.16.86.10:8123 | Synology |
| n8n | n8n.evlab.ch | 172.16.86.10:5678 | Synology |
| Stash | stash.evlab.ch | 172.16.86.10:9999 | Synology |
| pgAdmin | pgadmin.evlab.ch | 172.16.86.10:8888 | Synology |
| NAS (DSM) | nas.evlab.ch | 172.16.86.10:5000 | Synology |
| DNS (infra1) | dns.evlab.ch | localhost:5380 | infra1 |
| DNS (infra2) | dns2.evlab.ch | 172.16.86.12:5380 | infra2 |
| Grafana | grafana.evlab.ch | 172.16.86.13:3000 | mc-node-01 |
| Prometheus | prometheus.evlab.ch | 172.16.86.13:9090 | mc-node-01 |
| Checkmk | checkmk.evlab.ch | 172.16.86.13:8090 | mc-node-01 |

---

## 7. Out of Scope

- IPv6 dual-stack (future)
- Multi-site VPN (single-site only)
- Public-facing services (LAN only, VPN for remote access)
- Distributed transcoding (Stash does not support external workers)
- Ceph distributed storage (NFS from Synology instead)
