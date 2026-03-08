# User Guide

## Homelab DNS/HTTPS/VPN Infrastructure

## Quick Reference

| Service | URL | Credentials |
|---------|-----|-------------|
| Technitium DNS (infra1) | https://dns.evlab.ch | admin / vault password |
| Technitium DNS (infra2) | https://dns2.evlab.ch | admin / vault password |
| Home Assistant | https://homeassistant.evlab.ch | your HA credentials |
| n8n | https://n8n.evlab.ch | your n8n credentials |
| Stash | https://stash.evlab.ch | your Stash credentials |
| pgAdmin | https://pgadmin.evlab.ch | your pgAdmin credentials |
| NAS (DSM) | https://nas.evlab.ch | your Synology credentials |
| Grafana | https://grafana.evlab.ch | admin / vault password |
| Prometheus | https://prometheus.evlab.ch | no auth |
| Checkmk | https://checkmk.evlab.ch | cmkadmin / vault password |

---

## Sections

- [Day-to-Day Operations](operations.md) — DNS, Traefik/VIP, WireGuard, keepalived health checks
- [How-To Guides](how-to.md) — Add devices, Traefik services, WireGuard clients
- [WireGuard Client Setup](wireguard-clients.md) — Install and connect on iPhone and macOS
- [Maintenance](maintenance.md) — Update services, certificate renewal, backups
- [Disaster Recovery](disaster-recovery.md) — Node failure scenarios and full rebuild procedure
- [Troubleshooting](troubleshooting.md) — DNS, VIP, certs, ad blocking, DHCP, WireGuard, systemd-resolved
