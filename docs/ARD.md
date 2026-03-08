# Architecture Decision Records (ARD)

## Homelab DNS/HTTPS/VPN Infrastructure

---

## ADR-001: Dedicated Optiplex Micro for Infrastructure

**Date:** 2026-03-07
**Status:** Accepted

### Context

Network services (DNS, DHCP, reverse proxy, VPN) were initially planned on the Synology DS923+ NAS.

### Decision

Dedicate 2 of 5 Optiplex Micro to infrastructure. The Synology reverts to pure NAS.

### Rationale

- Port 53/80/443 conflicts with DSM services
- WireGuard kernel module unavailable on DSM
- `NET_ADMIN` capability unreliable in DSM Container Manager
- Single Point of Failure eliminated — NAS reboot no longer causes total network outage
- 3 remaining Optiplex still sufficient for MicroCloud (minimum 3 for OVN quorum)

### Consequences

- Higher idle power consumption (~30-50W for 2 Optiplex vs Synology alone)
- More hardware to maintain
- +65 CHF/year electricity vs Raspberry Pi alternative (but zero hardware cost since already owned)

---

## ADR-002: Technitium DNS in Docker (not native)

**Date:** 2026-03-07
**Status:** Accepted

### Context

Technitium DNS Server can run as a .NET application or Docker container.

### Decision

Deploy as Docker container with `network_mode: host`.

### Rationale

- No official .deb package — would require manual .NET runtime installation
- Docker simplifies upgrades and rollbacks
- `network_mode: host` provides full port access (53/UDP, 53/TCP, 5380)
- Built-in DHCP server requires broadcast, which works with host networking
- Consistent with Traefik (also Docker)

### Consequences

- Docker dependency on both infra nodes
- Container restart required for config changes (vs service reload)
- Technitium and Traefik excluded from Watchtower auto-updates (manual)

---

## ADR-003: WireGuard Native (not Docker)

**Date:** 2026-03-07
**Status:** Accepted

### Context

WireGuard can run as a Docker container (linuxserver/wireguard) or native kernel module.

### Decision

Deploy WireGuard natively via `apt install wireguard` + `wg-quick` + systemd.

### Rationale

- Linux kernel 6.x includes WireGuard module — no compilation needed
- Native is simpler: no `NET_ADMIN`/`SYS_MODULE` capabilities to manage
- `wg-quick@wg0` systemd service is stable and well-documented
- Fewer moving parts for a critical VPN service
- QR code generation works directly with `qrencode`

### Consequences

- Updates via `apt upgrade` instead of Docker image pull
- Config file at `/etc/wireguard/wg0.conf` (not in Docker volume)
- No Docker Compose for WireGuard — managed separately

---

## ADR-004: Traefik HA via keepalived (not DNS round-robin)

**Date:** 2026-03-07
**Status:** Accepted

### Context

With Traefik on 2 nodes, we need HA for the reverse proxy.

### Decision

Use keepalived with VRRP to manage a floating VIP (172.16.86.20).

### Rationale

- DNS wildcard `*.evlab.ch` points to a single IP — needs to always be reachable
- keepalived failover in ~5 seconds (vs DNS TTL-based failover in minutes)
- VRRP is well-proven for this exact use case
- Health check script verifies Docker container AND HTTP response
- Certificate sync via hourly rsync ensures BACKUP node has valid certs

### Alternatives Considered

- **DNS round-robin**: Both IPs in `*.evlab.ch` — client-dependent behavior, no health check
- **Traefik Swarm/K8s**: Overkill for 2 nodes

### Consequences

- VIP (172.16.86.20) must be reserved — not assigned to any physical host
- VRRP protocol 112 must be allowed between infra1 and infra2
- preempt_delay of 300s to avoid flapping

---

## ADR-005: NFS from Synology (not Ceph)

**Date:** 2026-03-08
**Status:** Accepted

### Context

MicroCloud typically uses Ceph for distributed storage across nodes.

### Decision

Use NFS exports from Synology DS923+ instead of Ceph.

### Rationale

- Ceph is overly complex for a 3-node homelab
- Zero fault tolerance with Ceph on 3 nodes (1 node failure = cluster degraded with no re-replication)
- Synology already hosts all persistent data
- NFS is simple, well-understood, zero additional disk requirements
- Two existing NFS exports: `datastore` and `isofiles`

### Alternatives Considered

- **Ceph (MicroCeph)**: Default for MicroCloud — rejected for complexity
- **LINSTOR (DRBD)**: Simpler than Ceph but still requires extra disks
- **iSCSI from Synology**: Better block performance but more complex setup

### Consequences

- Synology is SPOF for MicroCloud storage (acceptable for homelab)
- NFS performance limited by 1 GbE network (32KB packet size)
- Live migration works (all nodes see same NFS storage)
- No data locality — all I/O crosses the network

---

## ADR-006: Split-scope DHCP (not failover)

**Date:** 2026-03-07
**Status:** Accepted

### Context

DHCP needs to survive the failure of one infra node.

### Decision

Split-scope: infra1 serves 80% of the range (.100-.179), infra2 serves 20% (.180-.200).

### Rationale

- Technitium does not support native DHCP failover/replication
- Split-scope is the standard approach for DHCP HA without protocol support
- 80/20 split ensures infra1 handles most leases in normal operation
- Existing clients retain their lease (24h) even if their serving node fails
- All 24 DHCP reservations configured on both nodes (MAC-based)

### Consequences

- Clients may get different IPs from different scopes if their primary fails
- DHCP reservations must be maintained on both nodes (Ansible ensures this)
- 80% range on primary is sufficient for ~24 known + dynamic devices

---

## ADR-007: DNS-01 Challenge via Infomaniak API

**Date:** 2026-03-07
**Status:** Accepted

### Context

Let's Encrypt wildcard certificates require DNS-01 challenge validation.

### Decision

Use Infomaniak DNS API for ACME DNS-01 challenge (Traefik built-in provider).

### Rationale

- `evlab.ch` domain managed by Infomaniak — direct API access
- DNS-01 is the only challenge type that supports wildcard certs
- Traefik has native Infomaniak provider support
- No dependency on local Technitium DNS for certificate validation
- Public NS validation avoids any split-horizon issues

### Consequences

- Infomaniak API token required (stored in Ansible Vault)
- Challenge resolution depends on Infomaniak API availability
- 60-second delay before check to allow DNS propagation

---

## ADR-008: Dual Monitoring Stack (Prometheus + Checkmk)

**Date:** 2026-03-08
**Status:** Accepted

### Context

Infrastructure needs monitoring and alerting.

### Decision

Deploy both Prometheus + Grafana (metrics) and Checkmk (infrastructure monitoring).

### Rationale

- **Prometheus + Grafana**: Best-in-class time-series metrics, custom dashboards, PromQL
- **Checkmk**: Auto-discovery, built-in alerting, SNMP support (Synology, switch GC108PP)
- Each covers gaps in the other:
  - Prometheus: deep metrics, long-term storage, Traefik/WireGuard exporters
  - Checkmk: SNMP devices, service auto-detection, out-of-the-box alerting

### Alternatives Considered

- **Prometheus only**: Missing SNMP, complex alerting setup
- **Checkmk only**: Weaker custom dashboards, no native exporter ecosystem
- **Uptime Kuma**: Too simple for 5-node infrastructure

### Consequences

- Higher resource usage on mc-node-01 (Prometheus + Grafana + Checkmk)
- Two UIs to check (mitigated by Traefik providing HTTPS access to both)
- Checkmk agent deployed on all 5 nodes + node_exporter on all 5 nodes

---

## ADR-009: Application Services Stay on Synology

**Date:** 2026-03-07
**Status:** Accepted

### Context

Home Assistant, Stash, n8n could theoretically move to MicroCloud.

### Decision

Keep application services on Synology DS923+.

### Rationale

**Home Assistant:**
- USB dongle passthrough (Zigbee/Z-Wave) trivial on Docker, complex on Incus
- mDNS discovery requires host networking
- Recorder database benefits from local storage
- Must survive MicroCloud maintenance

**Stash:**
- Large media library resides on Synology volumes
- NFS mount would add latency and complexity
- Not a HA-critical service

**n8n:**
- Workflow data on Synology
- Integration with Synology-local databases (pgvector, redis, mongo)

### Consequences

- Synology runs application containers (watchtower manages updates)
- MicroCloud reserved for stateless workloads, dev/test, VMs
- Clear separation: Synology = data, Optiplex = infrastructure + compute
