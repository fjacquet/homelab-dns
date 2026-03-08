# WireGuard Client Setup

VPN server: `vpn.evlab.ch` → infra2 (`172.16.86.12`), port `51820/UDP`.
Internal subnet: `10.13.13.0/24`. Client configs live at `/etc/wireguard/clients/` on infra2.

## Retrieve Your Config

```bash
# Config file
scp fjacquet@172.16.86.12:/etc/wireguard/clients/<name>.conf .

# QR code (PNG)
scp fjacquet@172.16.86.12:/etc/wireguard/clients/<name>.png .

# Or display QR directly in terminal
ssh fjacquet@172.16.86.12 "sudo cat /etc/wireguard/clients/<name>.conf" | qrencode -t ansiutf8
```

---

## iPhone

1. Install **WireGuard** from the App Store.
2. Tap **+** → **Create from QR code**.
3. Scan the QR code (see above).
4. Name the tunnel (e.g. "evlab") and activate.

---

## macOS

**Option A — App Store (GUI)**

```bash
scp fjacquet@172.16.86.12:/etc/wireguard/clients/macbook.conf .
```

Open WireGuard → **Import Tunnel(s) from File** → select the `.conf` → **Activate**.

**Option B — Homebrew (CLI)**

```bash
brew install wireguard-tools
sudo mkdir -p /etc/wireguard
sudo cp macbook.conf /etc/wireguard/wg0.conf
sudo chmod 600 /etc/wireguard/wg0.conf

sudo wg-quick up wg0    # connect
sudo wg-quick down wg0  # disconnect
```

---

## Verify the Connection

```bash
sudo wg show
dig @172.16.86.11 homeassistant.evlab.ch +short   # → 172.16.86.20
curl -sk https://homeassistant.evlab.ch | head -1
```

---

## Add a New Client

See [how-to.md — Add a New WireGuard Client](how-to.md#add-a-new-wireguard-client).
