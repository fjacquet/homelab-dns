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
