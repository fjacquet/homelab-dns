# Disaster Recovery

## infra1 (opt1) is down

| Service | Impact | Recovery |
|---------|--------|----------|
| DNS primary | Secondary serves all queries | Clients use infra2 (.12) |
| Traefik | VIP failover to infra2 in ~5s | Automatic |
| DHCP | infra2 serves 20% scope | Existing leases valid 24h |
| DDNS | Cron stops | IP update paused (5-min max drift) |
| Backups | infra1 backup missed | infra2 backup continues |

Fix or replace opt1, then re-run Ansible:

```bash
ansible-playbook -i inventory.yml site.yml --limit opt1
```

## infra2 (opt2) is down

| Service | Impact | Recovery |
|---------|--------|----------|
| DNS secondary | Primary handles all queries | Transparent |
| WireGuard | VPN down | No remote access until fixed |
| DHCP | 20% scope unavailable | 80% scope on infra1 sufficient |

## Full Rebuild from Scratch

1. Install Ubuntu 24.04 LTS Server on the Optiplex.
2. Set up SSH keys and sudo.
3. Run Ansible:

```bash
ansible-playbook -i inventory.yml site.yml
```

All configuration is in the playbooks — no manual steps beyond initial OS install.
