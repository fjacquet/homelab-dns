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

## Check NTP Sync Status

All 5 Optiplex nodes use `ntp.metas.ch` (MeteoSwiss NTP) via systemd-timesyncd.

```bash
# Check sync status on all infra nodes
for h in 172.16.86.11 172.16.86.12; do
  echo "=== $h ==="; ssh fjacquet@$h "timedatectl status | grep -E 'NTP|sync|RTC'"
done

# Check MicroCloud nodes
for h in 172.16.86.13 172.16.86.14 172.16.86.15; do
  echo "=== $h ==="; ssh fjacquet@$h "timedatectl status | grep -E 'NTP|sync|RTC'"
done
```

Expected output: `NTP service: active` and `System clock synchronized: yes`.

## Check MicroCloud / LXD Cluster Status

```bash
# Cluster health (all 3 nodes should show ONLINE)
ssh fjacquet@172.16.86.13 "lxc cluster list"

# List all LXD VMs
ssh fjacquet@172.16.86.13 "lxc list"

# macvlan-host routing (must show enp0s31f6, NOT macvlan-host, for cross-node traffic)
ssh fjacquet@172.16.86.13 "ip route get 172.16.86.14"
ssh fjacquet@172.16.86.14 "ip route get 172.16.86.13"

# macvlan-host service status
for h in 172.16.86.13 172.16.86.14 172.16.86.15; do
  echo "=== $h ==="; ssh fjacquet@$h "systemctl is-active macvlan-host.service && ip addr show macvlan-host | grep inet"
done
```

## Check Monitoring Stack (Prometheus / Grafana / Checkmk)

```bash
# Prometheus targets (all should be UP)
curl -s http://172.16.86.21:9090/api/v1/targets | python3 -c \
  "import json,sys; d=json.load(sys.stdin); [print(t['labels'].get('job','?'), t['health']) for t in d['data']['activeTargets']]"

# Grafana health
curl -s http://172.16.86.21:3000/api/health | python3 -m json.tool

# Checkmk — list hosts with problems
ssh fjacquet@172.16.86.13 "lxc exec vm-checkmk -- su - cmk -s /bin/bash -c \
  'cmk -v --check mc-node-01.evlab.ch 2>&1 | grep -E \"WARN|CRIT|!!\"'"

# SNMP exporter health (proxies Synology NAS)
curl -s http://172.16.86.21:9116/metrics | grep snmp_up
```
