# Day-to-Day Operations

## Check DNS Status

```bash
# Verify both DNS servers respond
dig @172.16.86.11 homeassistant.evlab.ch +short   # → 172.16.86.20
dig @172.16.86.12 homeassistant.evlab.ch +short   # → 172.16.86.20

# Check ad blocking works
dig @172.16.86.11 doubleclick.net +short           # → 0.0.0.0

# Check reverse DNS
dig @172.16.86.11 -x 172.16.86.10 +short          # → nas.evlab.ch
```

## Check Traefik / VIP Status

```bash
# Which node holds the VIP?
ssh fjacquet@172.16.86.11 "ip addr show | grep 172.16.86.20"
ssh fjacquet@172.16.86.12 "ip addr show | grep 172.16.86.20"

# Check certificate validity
curl -vI https://homeassistant.evlab.ch 2>&1 | grep -E "issuer:|expire"

# Check Traefik dashboard (via SSH tunnel)
ssh -L 8080:localhost:8080 fjacquet@172.16.86.11
# Then open http://localhost:8080/dashboard/
```

## Check WireGuard Status

```bash
ssh fjacquet@172.16.86.12 "sudo wg show"
```

Output shows connected peers, last handshake time, and bytes transferred.

## Check keepalived Status

```bash
ssh fjacquet@172.16.86.11 "systemctl status keepalived"
ssh fjacquet@172.16.86.12 "systemctl status keepalived"

# Check VRRP logs
ssh fjacquet@172.16.86.11 "journalctl -u keepalived --no-pager -n 20"
```
