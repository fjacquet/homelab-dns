# How-To Guides

## Add a New Device (DHCP Reservation)

1. Get the device's MAC address.
2. Edit `group_vars/all/main.yml`:

```yaml
dhcp_reservations:
  # ... existing entries ...
  - { mac: "AA:BB:CC:DD:EE:FF", ip: "172.16.86.XX", name: "new-device" }
```

1. Add DNS records if needed:

```yaml
dns_a_records:
  - { name: "new-device.evlab.ch", ip: "172.16.86.XX" }

dns_ptr_records:
  - { ip: "172.16.86.XX", name: "new-device.evlab.ch" }
```

1. Deploy:

```bash
ansible-playbook -i inventory.yml site.yml --tags dhcp,dns_records
```

---

## Add a New Traefik Service

1. Edit `group_vars/all/main.yml`:

```yaml
traefik_services:
  # ... existing entries ...
  - { name: myapp, host: "myapp.evlab.ch", url: "http://172.16.86.XX:PORT" }
```

1. Deploy:

```bash
ansible-playbook -i inventory.yml site.yml --tags traefik
```

The wildcard `*.evlab.ch` already points to the VIP — no DNS change needed.

---

## Add a New WireGuard Client

1. Generate keys:

```bash
wg genkey | tee /tmp/newclient.key | wg pubkey > /tmp/newclient.pub
echo "Private: $(cat /tmp/newclient.key)"
echo "Public:  $(cat /tmp/newclient.pub)"
```

1. Add to Ansible Vault:

```bash
ansible-vault edit group_vars/all/vault.yml
# Add: vault_wg_newclient_privkey and vault_wg_newclient_pubkey
```

1. Edit `group_vars/all/main.yml`:

```yaml
wireguard_peers_list:
  # ... existing entries ...
  - {
      name: newclient,
      ip: "10.13.13.5",
      public_key: "{{ vault_wg_newclient_pubkey }}",
      private_key: "{{ vault_wg_newclient_privkey }}",
    }
```

1. Deploy:

```bash
ansible-playbook -i inventory.yml site.yml --tags wireguard
```

1. Retrieve client config:

```bash
scp fjacquet@172.16.86.12:/etc/wireguard/clients/newclient.conf .
scp fjacquet@172.16.86.12:/etc/wireguard/clients/newclient.png .
```

For client installation on iPhone and macOS, see [WireGuard Client Setup](wireguard-clients.md).
