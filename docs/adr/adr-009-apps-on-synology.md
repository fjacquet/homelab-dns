# ADR-009: Application Services Stay on Synology

**Date:** 2026-03-07 | **Status:** ✅ Accepted

## Context

Home Assistant, Stash, n8n could theoretically move to MicroCloud.

## Decision

Keep application services on Synology DS923+.

```mermaid
graph LR
    subgraph Synology["Synology DS923+ — Apps"]
        HA["Home Assistant\nUSB Zigbee dongle\nmDNS discovery"]
        STASH["Stash\nLarge media library\non local volumes"]
        N8N["n8n\nWorkflow data\n+ local DBs"]
    end

    subgraph MicroCloud["MicroCloud — Compute"]
        VM["Stateless workloads\nDev/test VMs\nPrometheus/Grafana/Checkmk"]
    end

    style Synology fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    style MicroCloud fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
```

## Rationale

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

## Consequences

- Synology runs application containers (Watchtower manages updates)
- MicroCloud reserved for stateless workloads, dev/test, VMs
- Clear separation: **Synology = data + apps**, **Optiplex = infrastructure + compute**
