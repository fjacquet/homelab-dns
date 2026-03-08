# Maintenance

## OS Patch Management

Updates all 5 nodes one at a time (`serial: 1`). Reboots only if a kernel update requires it. LXD instances on MicroCloud nodes are evacuated before reboot and restored after.

```bash
# Full patch run (apt dist-upgrade + conditional reboot)
ansible-playbook -i inventory.yml update.yml

# Dry-run first
ansible-playbook -i inventory.yml update.yml --check --diff

# Single node
ansible-playbook -i inventory.yml update.yml --limit opt1

# Skip reboot (security patches only, no disruption)
ansible-playbook -i inventory.yml update.yml --skip-tags reboot
```

## Container and Binary Updates

Pulls latest images and recreates containers. Also updates the `node_exporter` binary to the version in `group_vars/all/main.yml`.

```bash
# Update all containers + node_exporter
ansible-playbook -i inventory.yml update-containers.yml

# Single host
ansible-playbook -i inventory.yml update-containers.yml --limit opt1
```

**Containers updated:**

| Host | Container |
|------|-----------|
| infra1, infra2 | Technitium, Traefik, cAdvisor |
| mc-node-01 | Prometheus, Grafana, Checkmk |
| All 5 nodes | node_exporter binary |

To upgrade `node_exporter` to a new version, bump `node_exporter_version` in `group_vars/all/main.yml`, then run `update-containers.yml`.

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
