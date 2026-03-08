# Maintenance

## Update Services

```bash
# Technitium DNS
ssh fjacquet@172.16.86.11 "cd /opt/docker/technitium && docker compose pull && docker compose up -d"
ssh fjacquet@172.16.86.12 "cd /opt/docker/technitium && docker compose pull && docker compose up -d"

# Traefik
ssh fjacquet@172.16.86.11 "cd /opt/docker/traefik && docker compose pull && docker compose up -d"
ssh fjacquet@172.16.86.12 "cd /opt/docker/traefik && docker compose pull && docker compose up -d"

# WireGuard
ssh fjacquet@172.16.86.12 "sudo apt update && sudo apt upgrade wireguard wireguard-tools -y"
```

## Let's Encrypt Certificate

Renewal is automatic — Traefik renews before expiry via Infomaniak DNS-01 challenge. Check validity:

```bash
curl -vI https://homeassistant.evlab.ch 2>&1 | grep "expire date"
```

## Check Backups

Nightly backup cron runs at 02:00 on both infra nodes, storing to Synology NAS:

```bash
ssh fjacquet@172.16.86.10 "ls -lh /volume1/backups/infra/"
```
