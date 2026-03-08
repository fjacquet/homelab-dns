# ADR-008: Dual Monitoring Stack (Prometheus + Checkmk)

**Date:** 2026-03-08 | **Status:** ✅ Accepted

## Context

Infrastructure needs monitoring and alerting.

## Decision

Deploy both Prometheus + Grafana (metrics) and Checkmk (infrastructure monitoring).

## Rationale

Each tool covers gaps in the other:

```mermaid
graph TD
    subgraph Prometheus["Prometheus + Grafana"]
        P1["⏱ Time-series metrics"]
        P2["📊 Custom dashboards (PromQL)"]
        P3["🔌 Exporter ecosystem\n(Traefik, WireGuard, cAdvisor)"]
        P4["📦 Long-term storage"]
    end

    subgraph Checkmk["Checkmk"]
        C1["🔍 Auto-discovery"]
        C2["📡 SNMP (Synology, GC108PP switch)"]
        C3["🚨 Built-in alerting"]
        C4["🤖 Out-of-the-box service checks"]
    end

    STACK["Dual Monitoring Stack\nmc-node-01"]
    STACK --> Prometheus & Checkmk

    style Prometheus fill:#fff3e0,stroke:#ff9800
    style Checkmk fill:#e6f3ff,stroke:#0078D4
    style STACK fill:#f5f5f5,stroke:#333,stroke-width:2px
```

## Alternatives Considered

- **Prometheus only**: Missing SNMP, complex alerting setup
- **Checkmk only**: Weaker custom dashboards, no native exporter ecosystem
- **Uptime Kuma**: Too simple for 5-node infrastructure

## Consequences

- Higher resource usage on mc-node-01 (Prometheus + Grafana + Checkmk)
- Two UIs to check (mitigated by Traefik providing HTTPS access to both)
- Checkmk agent + node_exporter deployed on all 5 nodes
