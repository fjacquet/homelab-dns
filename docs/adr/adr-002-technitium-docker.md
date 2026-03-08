# ADR-002: Technitium DNS in Docker (not native)

**Date:** 2026-03-07 | **Status:** ✅ Accepted

## Context

Technitium DNS Server can run as a .NET application or Docker container.

## Decision

Deploy as Docker container with `network_mode: host`.

## Rationale

- No official .deb package — would require manual .NET runtime installation
- Docker simplifies upgrades and rollbacks
- `network_mode: host` provides full port access (53/UDP, 53/TCP, 5380)
- Built-in DHCP server requires broadcast, which works with host networking
- Consistent with Traefik (also Docker)

```mermaid
graph TD
    TECH["Technitium DNS\n(Docker, network_mode: host)"]
    P53U["UDP :53\nDNS queries"]
    P53T["TCP :53\nZone transfers"]
    P5380["TCP :5380\nAdmin UI"]
    DHCP["UDP :67/:68\nDHCP broadcast"]

    TECH --> P53U & P53T & P5380 & DHCP

    style TECH fill:#e6f3ff,stroke:#0078D4,stroke-width:2px
```

## Consequences

- Docker dependency on both infra nodes
- Container restart required for config changes (vs service reload)
- Technitium and Traefik excluded from Watchtower auto-updates (manual)
