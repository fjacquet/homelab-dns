# ADR-018: Disable Synology LAN Proxy Server (Squid)

**Date:** 2026-03-10 | **Status:** ✅ Accepted

## Context

Synology DSM ships with a built-in Proxy Server package (Squid on port 3128) that was historically used for:

- HTTP caching to reduce bandwidth on slow/metered connections
- Content filtering
- Traffic logging and visibility

## Decision

**Disable the Synology Proxy Server.** It provides no meaningful benefit in the current homelab setup.

## Rationale

| Factor | Reality in 2026 |
|---|---|
| **HTTPS everywhere** | ~98% of traffic is TLS — Squid cannot cache encrypted content without a MITM CA |
| **HTTP/2 + HTTP/3** | Protocol-level multiplexing makes proxy caching largely irrelevant |
| **CDN edge caching** | Content is already cached close to the user; a local Squid adds no benefit |
| **DNS-level filtering** | Technitium DNS with ad blocking covers the filtering use case more cleanly |
| **Traffic visibility** | Prometheus + Grafana + Checkmk provide observability; Traefik access logs cover service traffic |

## Alternatives Considered

- **Keep proxy with SSL inspection (MITM CA)** — technically possible but complex, privacy-invasive, and would break certificate pinning in modern apps. Not justified for a homelab.
- **Keep proxy for legacy devices** — no such devices exist in this environment.
- **Replace with a modern proxy (e.g., mitmproxy)** — adds complexity without a clear use case.

## Consequences

- One fewer service running on the Synology NAS (reduced resource usage)
- No LAN traffic bottleneck through port 3128
- Clients that had `http_proxy=172.16.86.x:3128` set must have that env var removed (none identified)
- Content filtering remains handled by Technitium DNS ad blocking
