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

## Ansible Webhook Engine

Trigger playbooks from n8n, scripts, or a browser via `https://ansible.evlab.ch`.

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/health` | GET | None | Liveness check |
| `/playbooks` | GET | X-API-Key | List available playbooks |
| `/run` | POST | X-API-Key | Submit a job → 202 + `job_id` |
| `/status/{job_id}` | GET | X-API-Key | Poll job status + log tail |
| `/docs` | GET | None | Swagger UI |

**Example n8n HTTP Request node:**
```json
{
  "method": "POST",
  "url": "http://ansible-webhook:8000/run",
  "headers": {"X-API-Key": "{{ $env.ANSIBLE_API_KEY }}"},
  "body": {
    "playbook": "update-containers.yml",
    "limit": "opt1"
  }
}
```

---

## Sections

- [Day-to-Day Operations](operations.md) — DNS, Traefik/VIP, WireGuard, keepalived health checks
- [How-To Guides](how-to.md) — Add devices, Traefik services, WireGuard clients
- [WireGuard Client Setup](wireguard-clients.md) — Install and connect on iPhone and macOS
- [Maintenance](maintenance.md) — Update services, certificate renewal, backups
- [Disaster Recovery](disaster-recovery.md) — Node failure scenarios and full rebuild procedure
- [Troubleshooting](troubleshooting.md) — DNS, VIP, certs, ad blocking, DHCP, WireGuard, systemd-resolved
