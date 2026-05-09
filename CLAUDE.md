# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Ansible-automated homelab infrastructure on 5 Dell Optiplex Micro machines running Ubuntu 24.04 LTS. Deploys HA DNS (Technitium), HTTPS reverse proxy with wildcard certs (Traefik + keepalived), WireGuard VPN, DHCP, ad blocking, and monitoring (Prometheus/Grafana + Checkmk).

Domain: `evlab.ch`. Network: `172.16.86.0/24`.

## Prerequisites

```bash
brew install ansible
ansible-galaxy collection install -r requirements.yml  # community.docker, community.general, ansible.posix
echo 'your-vault-password' > ~/.vault_pass && chmod 600 ~/.vault_pass
```

SSH access required to all target hosts before running any playbook.

## Key Commands

```bash
# Full infra deployment (infra1 + infra2)
ansible-playbook playbooks/site.yml

# Dry-run
ansible-playbook playbooks/site.yml --check --diff

# Deploy by phase/tag
ansible-playbook playbooks/site.yml --tags base
ansible-playbook playbooks/site.yml --tags docker
ansible-playbook playbooks/site.yml --tags technitium
ansible-playbook playbooks/site.yml --tags dns_records
ansible-playbook playbooks/site.yml --tags traefik
ansible-playbook playbooks/site.yml --tags keepalived
ansible-playbook playbooks/site.yml --tags iptables
ansible-playbook playbooks/site.yml --tags dhcp
ansible-playbook playbooks/site.yml --tags wireguard
ansible-playbook playbooks/site.yml --tags cron
ansible-playbook playbooks/site.yml --tags monitoring
ansible-playbook playbooks/site.yml --tags verify  # smoke tests

# Patch management (all 5 nodes, serial, reboot if needed)
ansible-playbook playbooks/update.yml
ansible-playbook playbooks/update.yml --check --diff   # dry-run
ansible-playbook playbooks/update.yml --limit opt1     # single host
ansible-playbook playbooks/update.yml --skip-tags reboot  # no reboots

# Container image updates (pull latest + recreate, no reboot)
ansible-playbook playbooks/update-containers.yml
ansible-playbook playbooks/update-containers.yml --limit opt1  # single host

# LXD VM OS updates (apt full-upgrade inside each VM via lxc exec)
ansible-playbook playbooks/update-vms.yml
ansible-playbook playbooks/update-vms.yml --check --diff   # dry-run
ansible-playbook playbooks/update-vms.yml --skip-tags reboot

# MicroCloud nodes (opt3/4/5)
ansible-playbook playbooks/microcloud-prepare.yml
ssh fjacquet@172.16.86.13 "sudo microcloud init"  # interactive, must run manually
ansible-playbook playbooks/microcloud-services.yml
ansible-playbook playbooks/microcloud-vms-monitoring.yml  # node_exporter + Prometheus scrape

# MicroCloud service tags (microcloud-services.yml)
ansible-playbook playbooks/microcloud-services.yml --tags mc_macvlan_host  # macvlan bridge (opt3/opt4)
ansible-playbook playbooks/microcloud-services.yml --tags mc_checkmk_tune  # memory rules + discovery
ansible-playbook playbooks/microcloud-services.yml --tags mc_checkmk_tls   # agent TLS registration
ansible-playbook playbooks/microcloud-services.yml --tags mc_snmp          # SNMP exporter in vm-monitoring

# Checkmk CLI (run from opt3 / mc-node-01)
lxc exec vm-checkmk -- su - cmk -s /bin/bash -c "cmk -II hostname.evlab.ch"  # full rediscovery
lxc exec vm-checkmk -- su - cmk -s /bin/bash -c "cmk -O"                     # reload core config

# Vault management
ansible-vault edit group_vars/all/vault.yml
```

## Architecture

### Inventory Groups

- `dns_primary` → opt1 / infra1 (`172.16.86.11`): primary DNS, Traefik (MASTER), DDNS cron
- `dns_secondary` → opt2 / infra2 (`172.16.86.12`): secondary DNS, Traefik (BACKUP), WireGuard
- `dns_servers` → parent group containing both of the above
- `microcloud` → opt3/4/5 (`172.16.86.13-15`): MicroCloud cluster nodes

### Playbooks

| Playbook | Targets | Purpose |
|---|---|---|
| `site.yml` | `dns_servers` | All infra: DNS, DHCP, Traefik, keepalived, WireGuard, monitoring exporters |
| `update.yml` | `dns_servers:microcloud` | Patch all nodes (serial), reboot if needed, verify services |
| `update-containers.yml` | `dns_servers` + `microcloud[0]` | Pull latest container images and recreate (no reboot) |
| `update-vms.yml` | `microcloud[0]` | Apt full-upgrade inside each LXD VM via `lxc exec`; restart VM if kernel changed |
| `microcloud-prepare.yml` | `microcloud` | Base setup, snaps, NFS mounts, node_exporter |
| `microcloud-services.yml` | `microcloud[0]` (mc-node-01) | LXD VMs + macvlan networking + Prometheus/Grafana/Checkmk/n8n |
| `microcloud-vms-monitoring.yml` | `microcloud[0]` | Install node_exporter in VMs + add `node-vms` Prometheus job |

### Service Architecture

- **Traefik HA**: VIP `172.16.86.20` via keepalived VRRP. Wildcard cert `*.evlab.ch` via Infomaniak DNS-01 challenge. Traefik runs on both infra nodes; primary is MASTER. ACME cert synced from primary to secondary via hourly cron (`sync-acme.sh`).
- **Technitium DNS**: Docker (`network_mode: host`) on both nodes. Primary/secondary zone replication via zone transfer. DHCP split-scope: infra1 handles `.100-.179`, infra2 handles `.180-.200`.
- **WireGuard**: Native kernel module (not Docker) on infra2 only. Port 51820 UDP. Internal subnet `10.13.13.0/24`. Client configs + QR codes at `/etc/wireguard/clients/` on infra2.
- **Monitoring**: Prometheus + Grafana in `vm-monitoring` (`172.16.86.21`). Checkmk CRE in `vm-checkmk` (`172.16.86.22`). Both are LXD VMs on mc-node-01; accessed via `lxc exec <vm> -- <cmd>`. Node exporters, cAdvisor, WireGuard exporter, and SNMP exporter on infra nodes / vm-monitoring.
- **macvlan-host bridge**: Each MicroCloud node runs a systemd service that creates a macvlan interface so the host can reach its own LXD VMs (macvlan isolation prevents direct host↔VM traffic). Uses `/32` + explicit host routes per VM — **never /24** (causes competing kernel route for 172.16.86.0/24 that breaks LXD cluster quorum).

### Variables

- `group_vars/all/main.yml`: All non-secret variables (IPs, ports, DNS records, DHCP reservations, service definitions)
- `group_vars/all/vault.yml`: Ansible Vault encrypted secrets (passwords, API tokens, WireGuard keys)
- Host-specific vars (`dhcp_range_start`, `dhcp_range_end`, `infra_hostname`) are in `inventory.yml`
- `dns_primary_ip`/`dns_secondary_ip` are derived from inventory via `hostvars` (not hardcoded)

Vault vars follow the pattern `vault_*` and are referenced from `main.yml`.

### Templates

All Jinja2 templates in `templates/`. Key ones:

- `technitium-compose.yml.j2`: Technitium Docker Compose
- `traefik-compose.yml.j2`, `traefik-static.yml.j2`, `traefik-services.yml.j2`: Traefik stack
- `keepalived.conf.j2`: VRRP config (priority differs per host via `inventory_hostname` checks)
- `wg0.conf.j2`: WireGuard server config; `wg-client.conf.j2`: per-peer client configs
- `netplan-infra.yml.j2`: Network config for infra nodes (NIC: `enp0s31f6`)
- `netplan-mc.yml.j2`: Network config for MicroCloud nodes (no macvlan stanza — macvlan-host is managed by systemd service, not netplan)

### Primary-Only vs Both-Node Logic

Several tasks use `when: inventory_hostname in groups['dns_primary']` or `groups['dns_secondary']` to differentiate behavior. Traefik directories, DDNS cron, and ACME sync only run on primary; WireGuard only on secondary.

### LXD VMs (on mc-node-01 / opt3)

| VM | IP | Services |
|---|---|---|
| vm-monitoring | 172.16.86.21 | Prometheus (9090), Grafana (3000), SNMP exporter (9116) |
| vm-checkmk | 172.16.86.22 | Checkmk CRE (5000 internal) |
| vm-automation | 172.16.86.23 | n8n, ansible-webhook |

### Port Reference

| Port | Service | Notes |
|---|---|---|
| 5380 | Technitium Web UI | Firewalled — only localhost + infra1→infra2 |
| 8080 | Traefik API | Firewalled — only localhost (keepalived health check) |
| 9090 | Prometheus | vm-monitoring (172.16.86.21) |
| 3000 | Grafana | vm-monitoring |
| 9116 | SNMP exporter | vm-monitoring (proxies Synology NAS SNMP) |
| 9100 | node_exporter | All nodes + VMs |
| 9101 | cAdvisor | Infra nodes |
| 9586 | WireGuard exporter | infra2 only |
| 51820/UDP | WireGuard | infra2 only |

### Critical Gotchas

- **macvlan-host must use /32**: A /24 prefix creates a competing kernel route for 172.16.86.0/24 that shadows `enp0s31f6` and breaks LXD cluster quorum (dqlite "no available leader"). Always use `/32` + `ip route replace <vm-ip>/32 dev macvlan-host`.

- **Checkmk `memory_linux` ruleset is not in the REST API**: It's a legacy `checkgroup_parameters` ruleset. Write rules directly to `/omd/sites/cmk/etc/check_mk/conf.d/memory_tuning.mk` inside vm-checkmk, then `cmk -O` to reload. The REST API returns 400 "Unknown ruleset" silently when `failed_when: false`.

- **`site.yml --check` fails at "Extract API token"**: Check mode skips the Technitium restart handler, so `technitium_login` has no `.content`. This is a check-mode artifact only — not a real failure.

- **LXD VM netplan**: Run `netplan apply` inside a VM via `lxc exec <vm> -- netplan apply`. Static IPs are configured inside the VM; host-side is macvlan only.

- **All 5 nodes boot in legacy BIOS (CSM), not UEFI**: `/sys/firmware/efi` does not exist on any host, and `fwupdmgr get-updates` reports `WARNING: UEFI firmware can not be updated in legacy BIOS mode → No updatable devices`. Two consequences:
  - **`fwupd` capsule firmware updates do not work.** BIOS / Intel ME / EC firmware can only be updated by booting from a Dell BIOS-update USB stick during a maintenance window. Latest OptiPlex 7040 BIOS as of 2024 is `1.31.0`; nodes are running `1.12.0`–`1.21.0`. Intel CPU microcode is still patched at runtime via apt's `intel-microcode` package — that's the only firmware-adjacent thing the `update.yml` playbook actually touches.
  - **UEFI Secure Boot is not engaged.** The Microsoft Corporation UEFI CA 2011 expiration (October 2026) does not affect these machines because the shim → MS CA chain is not in the boot path. The `Canonical Ltd. Secure Boot Signing` certs visible in `dmesg` are the kernel's built-in MOK keyring for module signing, not active firmware-level Secure Boot.
- **MicroCloud reboot needs `reboot_timeout >= 1800`**: After a kernel upgrade, snap + LXD daemon initialization keeps `sshd` from binding for several minutes past kernel boot. The default 600s in `ansible.builtin.reboot` is too short and produces spurious `UNREACHABLE` errors mid-rolling-upgrade — `update.yml` uses 1800s for this reason. The host actually recovers; ansible just gave up too early.

- **`lxc cluster restore` is interactive**: The bare command prompts `(yes/no)` and fails under ansible with `Error: EOF`. Always pass `--force` (matching the existing `lxc cluster evacuate ... --force` pattern in `update.yml`).

<!-- rtk-instructions v2 -->
# RTK (Rust Token Killer) - Token-Optimized Commands

## Golden Rule

**Always prefix commands with `rtk`**. If RTK has a dedicated filter, it uses it. If not, it passes through unchanged. This means RTK is always safe to use.

**Important**: Even in command chains with `&&`, use `rtk`:
```bash
# ❌ Wrong
git add . && git commit -m "msg" && git push

# ✅ Correct
rtk git add . && rtk git commit -m "msg" && rtk git push
```

## RTK Commands by Workflow

### Build & Compile (80-90% savings)
```bash
rtk cargo build         # Cargo build output
rtk cargo check         # Cargo check output
rtk cargo clippy        # Clippy warnings grouped by file (80%)
rtk tsc                 # TypeScript errors grouped by file/code (83%)
rtk lint                # ESLint/Biome violations grouped (84%)
rtk prettier --check    # Files needing format only (70%)
rtk next build          # Next.js build with route metrics (87%)
```

### Test (90-99% savings)
```bash
rtk cargo test          # Cargo test failures only (90%)
rtk vitest run          # Vitest failures only (99.5%)
rtk playwright test     # Playwright failures only (94%)
rtk test <cmd>          # Generic test wrapper - failures only
```

### Git (59-80% savings)
```bash
rtk git status          # Compact status
rtk git log             # Compact log (works with all git flags)
rtk git diff            # Compact diff (80%)
rtk git show            # Compact show (80%)
rtk git add             # Ultra-compact confirmations (59%)
rtk git commit          # Ultra-compact confirmations (59%)
rtk git push            # Ultra-compact confirmations
rtk git pull            # Ultra-compact confirmations
rtk git branch          # Compact branch list
rtk git fetch           # Compact fetch
rtk git stash           # Compact stash
rtk git worktree        # Compact worktree
```

Note: Git passthrough works for ALL subcommands, even those not explicitly listed.

### GitHub (26-87% savings)
```bash
rtk gh pr view <num>    # Compact PR view (87%)
rtk gh pr checks        # Compact PR checks (79%)
rtk gh run list         # Compact workflow runs (82%)
rtk gh issue list       # Compact issue list (80%)
rtk gh api              # Compact API responses (26%)
```

### JavaScript/TypeScript Tooling (70-90% savings)
```bash
rtk pnpm list           # Compact dependency tree (70%)
rtk pnpm outdated       # Compact outdated packages (80%)
rtk pnpm install        # Compact install output (90%)
rtk npm run <script>    # Compact npm script output
rtk npx <cmd>           # Compact npx command output
rtk prisma              # Prisma without ASCII art (88%)
```

### Files & Search (60-75% savings)
```bash
rtk ls <path>           # Tree format, compact (65%)
rtk read <file>         # Code reading with filtering (60%)
rtk grep <pattern>      # Search grouped by file (75%)
rtk find <pattern>      # Find grouped by directory (70%)
```

### Analysis & Debug (70-90% savings)
```bash
rtk err <cmd>           # Filter errors only from any command
rtk log <file>          # Deduplicated logs with counts
rtk json <file>         # JSON structure without values
rtk deps                # Dependency overview
rtk env                 # Environment variables compact
rtk summary <cmd>       # Smart summary of command output
rtk diff                # Ultra-compact diffs
```

### Infrastructure (85% savings)
```bash
rtk docker ps           # Compact container list
rtk docker images       # Compact image list
rtk docker logs <c>     # Deduplicated logs
rtk kubectl get         # Compact resource list
rtk kubectl logs        # Deduplicated pod logs
```

### Network (65-70% savings)
```bash
rtk curl <url>          # Compact HTTP responses (70%)
rtk wget <url>          # Compact download output (65%)
```

### Meta Commands
```bash
rtk gain                # View token savings statistics
rtk gain --history      # View command history with savings
rtk discover            # Analyze Claude Code sessions for missed RTK usage
rtk proxy <cmd>         # Run command without filtering (for debugging)
rtk init                # Add RTK instructions to CLAUDE.md
rtk init --global       # Add RTK to ~/.claude/CLAUDE.md
```

## Token Savings Overview

| Category | Commands | Typical Savings |
|----------|----------|-----------------|
| Tests | vitest, playwright, cargo test | 90-99% |
| Build | next, tsc, lint, prettier | 70-87% |
| Git | status, log, diff, add, commit | 59-80% |
| GitHub | gh pr, gh run, gh issue | 26-87% |
| Package Managers | pnpm, npm, npx | 70-90% |
| Files | ls, read, grep, find | 60-75% |
| Infrastructure | docker, kubectl | 85% |
| Network | curl, wget | 65-70% |

Overall average: **60-90% token reduction** on common development operations.
<!-- /rtk-instructions -->