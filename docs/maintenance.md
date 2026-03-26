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

| Host | Service | Method |
|------|---------|--------|
| infra1, infra2 | Technitium, Traefik, cAdvisor | Docker containers |
| vm-monitoring (172.16.86.21) | Prometheus, Grafana, SNMP exporter | systemd (native apt) |
| vm-checkmk (172.16.86.22) | Checkmk CRE | omd restart cmk |
| All 5 nodes | node_exporter binary | Binary updated in-place |

To upgrade `node_exporter` to a new version, bump `node_exporter_version` in `group_vars/all/main.yml`, then run `update-containers.yml`.

## Ansible Webhook Engine

Deployed on the Synology NAS alongside n8n. Swagger UI available at `https://ansible.evlab.ch/docs`.

```bash
# First-time secrets setup on mc-node-01 (one-time, before running the playbook)
ssh fjacquet@172.16.86.13
sudo mkdir -p /opt/secrets
sudo cp ~/.ssh/id_rsa /opt/secrets/id_rsa
echo 'vault-password' | sudo tee /opt/secrets/vault_pass
sudo chmod 600 /opt/secrets/id_rsa /opt/secrets/vault_pass

# Deploy via Ansible (handles repo clone, build, start)
ansible-playbook -i inventory.yml microcloud-services.yml --tags mc_automation

# Update after code changes (rebuild image from updated repo)
ansible-playbook -i inventory.yml update-containers.yml --limit microcloud

# View logs
ssh fjacquet@172.16.86.13 "docker logs ansible-webhook -f"

# Test from CLI
curl https://ansible.evlab.ch/health
curl -H "X-API-Key: <key>" https://ansible.evlab.ch/playbooks

# Trigger a dry-run update
curl -X POST https://ansible.evlab.ch/run \
  -H "X-API-Key: <key>" \
  -H "Content-Type: application/json" \
  -d '{"playbook":"update.yml","limit":"opt1","extra_vars":{"ansible_check_mode":true}}'
```

## System Fixes (NTP + Service Suppression)

Idempotent fixes for all 5 Optiplex nodes: NTP server configuration and masking of services that produce false alarms on desktop hardware (e.g. `openipmi` — no IPMI hardware present on Optiplex Micro).

```bash
# Apply to infra nodes (opt1, opt2)
ansible-playbook playbooks/site.yml --tags fixes

# Apply to MicroCloud nodes (opt3, opt4, opt5)
ansible-playbook playbooks/microcloud-prepare.yml --tags mc_fixes
```

These are safe to re-run at any time. Expected changes: 0 if already applied.

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

## Checkmk Operations

Checkmk runs as an OMD site (`cmk`) inside `vm-checkmk` (`172.16.86.22`), accessed via `lxc exec` from mc-node-01.

```bash
# Run service discovery on a host
ssh fjacquet@172.16.86.13 "lxc exec vm-checkmk -- su - cmk -s /bin/bash -c 'cmk -II hostname.evlab.ch'"

# Check for unmonitored services
ssh fjacquet@172.16.86.13 "lxc exec vm-checkmk -- su - cmk -s /bin/bash -c 'cmk --check-discovery hostname.evlab.ch'"

# Reload core config (after editing .mk files)
ssh fjacquet@172.16.86.13 "lxc exec vm-checkmk -- su - cmk -s /bin/bash -c 'cmk -O'"

# Run full discovery on all hosts
for host in mc-node-01.evlab.ch mc-node-02.evlab.ch mc-node-03.evlab.ch \
            vm-monitoring.evlab.ch vm-checkmk.evlab.ch vm-automation.evlab.ch \
            infra1.evlab.ch infra2.evlab.ch ds923fj; do
  ssh fjacquet@172.16.86.13 "lxc exec vm-checkmk -- su - cmk -s /bin/bash -c 'cmk -II $host'"
done
ssh fjacquet@172.16.86.13 "lxc exec vm-checkmk -- su - cmk -s /bin/bash -c 'cmk -O'"
```

**Adding custom check parameters** (e.g. memory thresholds): Write `.mk` files to `/omd/sites/cmk/etc/check_mk/conf.d/` inside vm-checkmk, then run `cmk -O`. The REST API only exposes a subset of rulesets — legacy `checkgroup_parameters` (like `memory_linux`) must be written directly.
