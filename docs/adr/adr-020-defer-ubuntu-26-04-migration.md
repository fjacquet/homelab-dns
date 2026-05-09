# ADR-020: Defer Ubuntu 24.04 → 26.04 LTS Migration Until 26.04.1

**Date:** 2026-05-09 | **Status:** ✅ Accepted

## Context

Ubuntu 26.04 LTS "Resolute Raccoon" was released on 23 April 2026. The homelab currently runs Ubuntu 24.04 LTS (`noble`) on:

- 5 Dell OptiPlex 7040 hosts (kernel 6.8.0-111, BIOS 1.24.0)
- 3 LXD VMs hosting Prometheus/Grafana, Checkmk and n8n

Ubuntu 24.04 LTS receives standard security maintenance until **April 2029** (Pro until 2034), so there is no calendar-driven urgency. The question is whether early-adopting 26.04 buys anything that justifies the risk.

A repo-wide scan turned up exactly four hardcoded references to either `ubuntu:24.04` (LXD VM image launch) or `noble` (Checkmk Raw Edition `.deb` URL), all concentrated in `playbooks/microcloud-services.yml`. Everything else (Docker repo, Grafana repo, snap channels, Ansible collections, container images, Python tooling, netplan templates) is already version-flexible.

## Decision

**Do not migrate now. Re-evaluate after 26.04.1 ships (~July/August 2026)** and at least three months of community feedback are available. Concrete migration windowed for **Q4 2026 / Q1 2027**.

## Rationale

Three rupture points in 26.04 dominate the risk profile for this specific homelab:

| Change | 24.04 | 26.04 | Risk |
|---|---|---|---|
| Kernel | 6.8 | **7.0** | Major series jump. OptiPlex 7040 hardware verified on 6.x; 7.0's first-of-series quirks (especially around macvlan + LXD) need community shake-out. |
| systemd | 256 | **259 (cgroup v1 removed)** | Docker and LXD-snap are on cgroup v2 already, so this is *theoretically* fine, but a release-cycle of validation costs nothing. |
| sudo | sudo (C) | **sudo-rs** (Rust) | Ansible's `become` relies on sudo. The rewrite is meant to be drop-in but 26.04 is the first LTS where it's the default; the homelab is not the place to discover regressions. |

Other deltas are lower-risk: Python 3.14 (our `requires-python=">=3.11"` covers it), Netplan 1.2 (our `version: 2` schemas are stable), Dracut replacing initramfs-tools (no custom hooks here).

The path `do-release-upgrade` from 24.04 LTS to 26.04 LTS does not open by default until **26.04.1**. Forcing it earlier with `-d` only buys early-adopter bugs.

## Pre-migration prerequisites

1. **Checkmk publishes a `resolute_amd64.deb`** for the version we install. Without that the Checkmk VM bootstrap step fails. Watch `https://download.checkmk.com/checkmk/<version>/`.
2. **Spike a 26.04 LXD VM** as a sanity bed: verify apt, snap, sudo-rs, systemd 259 cgroup behaviour.
3. **Snap LXD channel check**: `snap info lxd` on each host. The cluster currently runs on whatever channel the `latest/stable` track resolves to; on 26.04, snapd may pull a major LXD version with cluster-format implications. Pin the channel explicitly if needed before doing `do-release-upgrade`.

## What this ADR ships alongside

To keep the future migration to a one-line variable bump, `microcloud-services.yml` is parameterised in the same PR as this ADR:

| Variable | Today's value | When ready |
|---|---|---|
| `ubuntu_lxd_release` (`group_vars/all/main.yml`) | `"24.04"` | bump to `"26.04"` |
| `checkmk_deb_codename` (`group_vars/all/main.yml`) | `"noble"` | bump to `"resolute"` |

The four hardcoded `ubuntu:24.04` and `noble` strings in the playbook are replaced with the corresponding Jinja references. Behaviour is unchanged today.

## Migration approach (when ready)

1. Bump the two variables. Single PR, single commit.
2. Migrate hosts one at a time in the order already proven for the BIOS-flash run: opt5 → opt1 → opt2 → opt3 → opt4. For MicroCloud nodes, reuse the `lxc cluster evacuate --force` / `lxc cluster restore --force` pattern from `update.yml` (ADR-014, plus the `reboot_timeout: 1800` from PR #3).
3. Migrate the 3 LXD VMs in place via `do-release-upgrade` driven through `lxc exec` — extension of `update-vms.yml`. Recreating from `ubuntu:26.04` images would lose Checkmk configuration.
4. Verify per the checklist in `.planning/synthetic-gliding-thimble.md` (kept locally).

## Consequences

- No functional change today; all four codename references are now centralised.
- Q4 2026 migration is a 2-line variable diff plus host-by-host execution rather than a hardcode hunt.
- If Canonical ships `do-release-upgrade` instructions or LVFS firmware for the OptiPlex line in the meantime, this ADR is revisited (especially the kernel-7.0 risk paragraph).
