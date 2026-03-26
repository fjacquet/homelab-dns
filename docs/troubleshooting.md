# Troubleshooting

## DNS Not Resolving

```bash
# Check Technitium is running
ssh fjacquet@172.16.86.11 "docker ps | grep technitium"

# Check port 53 is bound (should show 0.0.0.0:53, not 127.0.0.53)
ssh fjacquet@172.16.86.11 "ss -tlnp | grep ':53 '"
```

If `127.0.0.53` appears, `systemd-resolved` is interfering — see [systemd-resolved conflict](#systemd-resolved-blocking-port-53).

## VIP Not Responding

```bash
# Check keepalived status and logs
ssh fjacquet@172.16.86.11 "systemctl status keepalived"
ssh fjacquet@172.16.86.11 "journalctl -u keepalived -n 20"

# Verify NIC name matches config (must be enp0s31f6)
ssh fjacquet@172.16.86.11 "ip -br link | grep -v lo"
```

## Certificate Errors

```bash
# Check ACME logs
ssh fjacquet@172.16.86.11 "docker logs traefik 2>&1 | grep -i acme"

# Check Infomaniak API token is set
ssh fjacquet@172.16.86.11 "docker inspect traefik | jq '.[0].Config.Env[] | select(startswith(\"INFOMANIAK\"))'"

# Force certificate renewal
ssh fjacquet@172.16.86.11 "sudo rm /opt/docker/traefik/certs/acme.json && docker restart traefik"
# Wait ~2 minutes for DNS-01 challenge to complete
```

## Ad Blocking Not Working

Blocklists may not have downloaded yet.

```bash
# Get API token
TOKEN=$(curl -s "http://172.16.86.11:5380/api/user/login?user=admin&pass=YOUR_PASSWORD" | jq -r .token)

# Check blocking status
curl -s "http://172.16.86.11:5380/api/settings/get?token=$TOKEN" | jq '.response.enableBlocking, .response.blockListUrls'

# Force blocklist download (takes 1-2 min for large lists)
curl -s "http://172.16.86.11:5380/api/settings/forceUpdateBlockLists?token=$TOKEN"

# Verify (should return 0.0.0.0)
dig @172.16.86.11 doubleclick.net +short
```

Repeat on infra2 (`172.16.86.12`) if needed. Blocklists auto-update every 24h.

## DHCP Giving Wrong IP

Reservations must exist on **both** DHCP servers. If a device gets a `.180-.200` address, infra2 responded first without the reservation.

```bash
# Re-deploy reservations on both servers
ansible-playbook -i inventory.yml site.yml --tags dhcp

# Force DHCP renewal on the device
# Linux: sudo dhclient -r && sudo dhclient
# macOS: sudo ipconfig set en0 DHCP
```

## WireGuard "Key is not the correct length"

Keys must be exactly 44 characters (base64 of 32 bytes, ending with `=`). In Ansible Vault, **keys must be quoted**:

```yaml
# Correct
vault_wg_server_private_key: "aBcDeFg...xyz="

# Wrong — YAML strips trailing =
vault_wg_server_private_key: aBcDeFg...xyz=
```

## openipmi Service Failure (False Alarm)

**Symptom:** `systemctl status` or `systemd-analyze blame` shows `openipmi.service` failed.

**Cause:** Dell Optiplex Micro machines have no IPMI hardware. The `openipmi` package (sometimes pulled in as a dependency) tries to load IPMI kernel modules at boot and fails silently — it is harmless but pollutes the service summary.

**Fix:** Already applied to all 5 nodes via `--tags fixes` / `--tags mc_fixes`. To reapply:

```bash
# infra nodes (opt1, opt2)
ansible-playbook playbooks/site.yml --tags fixes

# MicroCloud nodes (opt3, opt4, opt5)
ansible-playbook playbooks/microcloud-prepare.yml --tags mc_fixes
```

To verify manually:

```bash
ssh fjacquet@172.16.86.11 "systemctl is-enabled openipmi 2>&1"
# Expected: masked
```

---

## NTP Not Syncing

**Symptom:** `timedatectl` shows `System clock synchronized: no` or uses wrong NTP server.

**Fix:** All 5 nodes have a timesyncd drop-in at `/etc/systemd/timesyncd.conf.d/homelab.conf` setting `NTP=ntp.metas.ch`. If missing, redeploy:

```bash
ansible-playbook playbooks/site.yml --tags fixes          # opt1, opt2
ansible-playbook playbooks/microcloud-prepare.yml --tags mc_fixes  # opt3-5
```

Verify:

```bash
ssh fjacquet@172.16.86.11 "cat /etc/systemd/timesyncd.conf.d/homelab.conf"
ssh fjacquet@172.16.86.11 "timedatectl timesync-status"
```

---

## systemd-resolved Blocking Port 53

```bash
# Confirm resolved is on port 53
ssh fjacquet@172.16.86.11 "ss -tlnp | grep ':53 '"

# Fix: disable stub listener
sudo sed -i 's/^#\?DNSStubListener=.*/DNSStubListener=no/' /etc/systemd/resolved.conf
sudo systemctl restart systemd-resolved

# Restart Technitium and verify
ssh fjacquet@172.16.86.11 "docker restart technitium-dns"
ssh fjacquet@172.16.86.11 "ss -tlnp | grep ':53 '"
# Should now show 0.0.0.0:53
```

---

## LXD Cluster Quorum Lost ("no available dqlite leader")

**Symptom:** `lxc cluster list` or `lxc list` fails with "no available dqlite leader server found" on one MicroCloud node.

**Root cause (most likely):** The `macvlan-host` interface has a `/24` address, creating a competing kernel route for `172.16.86.0/24` that takes priority over `enp0s31f6`. The affected node cannot reach cluster peers on port 8443.

**Diagnose:**
```bash
# On the failing node — should say "dev enp0s31f6", NOT "dev macvlan-host"
ssh fjacquet@172.16.86.13 "ip route get 172.16.86.14"

# Check macvlan-host address prefix
ssh fjacquet@172.16.86.13 "ip addr show macvlan-host"
# If it shows /24, that is the bug. It must be /32.
```

**Fix:**
```bash
# Immediate: remove the /24 address and add /32
ssh fjacquet@172.16.86.13 "sudo ip addr del 172.16.86.25/24 dev macvlan-host"

# Redeploy the correct service
ansible-playbook playbooks/microcloud-services.yml --tags mc_macvlan_host
```

After fixing, wait ~30 seconds for LXD to reconnect to dqlite, then verify:
```bash
ssh fjacquet@172.16.86.13 "lxc cluster list"
# Expected: all 3 nodes ONLINE
```

---

## Checkmk Memory WARN/CRIT on MicroCloud Nodes (False Alarm)

**Symptom:** Checkmk reports Memory WARN/CRIT for `Shared memory` on mc-node-01/02/03. Default thresholds are 20%/30%, but LXD VMs use shared memory (QEMU/virtio) inflating the counter to 30-50%+.

**Fix:** The `memory_tuning.mk` rule raises thresholds to 80%/95% for MicroCloud nodes. If missing:

```bash
# Check if file exists inside vm-checkmk
ssh fjacquet@172.16.86.13 "lxc exec vm-checkmk -- ls /omd/sites/cmk/etc/check_mk/conf.d/memory_tuning.mk"

# Reapply via Ansible
ansible-playbook playbooks/microcloud-services.yml --tags mc_checkmk_tune
```

**Note:** The `memory_linux` ruleset is NOT exposed by the Checkmk REST API (legacy `checkgroup_parameters` ruleset). Rules must be written directly to `/omd/sites/cmk/etc/check_mk/conf.d/memory_tuning.mk` inside vm-checkmk and activated with `cmk -O`.

---

## LXD VM Gets DHCP IP Instead of Static

**Symptom:** An LXD VM (e.g. vm-monitoring) has a random `.180-.200` DHCP address instead of its assigned static IP (`.21`/`.22`/`.23`).

**Cause:** The netplan static IP tasks run inside a `when: vm_exists.rc != 0` block — they only execute during VM creation. If the VM already existed when the playbook ran, static IP was never configured.

**Fix:**
```bash
# Apply static IP manually via lxc exec (example for vm-monitoring)
ssh fjacquet@172.16.86.13 "lxc exec vm-monitoring -- rm -f /etc/netplan/50-cloud-init.yaml"
ssh fjacquet@172.16.86.13 "lxc exec vm-monitoring -- netplan apply"

# Or redeploy the full service (will reconfigure netplan inside VMs)
ansible-playbook playbooks/microcloud-services.yml --tags mc_vm_monitoring
```
