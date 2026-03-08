# ADR-015: Ansible Webhook Engine (FastAPI + Docker)

**Date:** 2026-03-08 | **Status:** ✅ Accepted

## Context

Ansible playbooks were executed exclusively from a developer's CLI, creating three problems:

1. **Silos** — infrastructure changes cannot be triggered by external events (monitoring alerts, GitHub webhooks, n8n workflows)
2. **No audit trail** — no centralized log of who ran what playbook when
3. **Blocking** — long-running playbooks (5–15 min) cannot be called synchronously from workflow tools without timeouts

n8n (`n8n.evlab.ch`) already runs on the Synology NAS and is the homelab's workflow automation hub. The goal is to let n8n trigger any Ansible playbook via HTTP POST without manual intervention.

## Decision

Deploy a **containerized FastAPI webhook service** (`ansible-webhook`) on the Synology NAS alongside n8n. It exposes four endpoints:

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /health` | None | Liveness probe |
| `GET /playbooks` | X-API-Key | List available playbooks |
| `POST /run` | X-API-Key | Accept job, return 202 + `job_id` |
| `GET /status/{job_id}` | X-API-Key | Poll job status + log tail |

The service runs `ansible-playbook` as a subprocess in a background thread, streams stdout to an in-memory job log, and exposes the result via `/status`.

## Architecture

```mermaid
sequenceDiagram
    participant N as n8n
    participant W as ansible-webhook<br/>(FastAPI :8000)
    participant A as ansible-playbook<br/>(subprocess)
    participant H as Target hosts<br/>(SSH)

    N->>W: POST /run {playbook, tags, limit, extra_vars}<br/>X-API-Key: ***
    W-->>N: 202 Accepted {job_id}
    W->>A: spawn thread → ansible-playbook ...
    A->>H: SSH (mounted id_rsa)
    H-->>A: results
    A-->>W: stdout streamed to job.log_lines
    N->>W: GET /status/{job_id}
    W-->>N: {status: succeeded, log_lines: [...]}
```

## Deployment

```mermaid
graph TD
    subgraph Synology["Synology DS923+ (172.16.86.10)"]
        N8N["n8n container\n:5678"]
        AW["ansible-webhook container\n:8000"]
        NET["n8n_default Docker network"]
        N8N -->|"http://ansible-webhook:8000"| NET
        NET --> AW
    end

    subgraph Volumes["Read-only mounts"]
        REPO["/volume1/homelab-dns\n→ /playbooks"]
        SSH["/volume1/secrets/id_rsa\n→ /root/.ssh/id_rsa"]
        VAULT["/volume1/secrets/vault_pass\n→ /vault_pass"]
    end

    AW --> Volumes

    subgraph Infra["Infrastructure nodes"]
        OPT1["opt1 (172.16.86.11)"]
        OPT2["opt2 (172.16.86.12)"]
        MC["MicroCloud (.13-.15)"]
    end

    AW -->|SSH :22| Infra

    TRAEFIK["Traefik VIP\nansible.evlab.ch"] --> AW

    style Synology fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    style Volumes fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style Infra fill:#e6f3ff,stroke:#0078D4,stroke-width:2px
```

## Security Model

- **API key** — `WEBHOOK_API_KEY` env var; compared with `X-API-Key` header via `secrets.compare_digest` (timing-safe)
- **Secrets** — SSH private key and Vault password mounted read-only; never baked into the image
- **Path traversal** — playbook names validated to be plain filenames (no `/` or `..`)
- **Network** — container joins `n8n_default` network; internal n8n calls need no Traefik hop
- **Watchtower** disabled — explicit image updates only

## Rationale

- **FastAPI** — async-native, built-in OpenAPI docs at `/docs`, type-safe via Pydantic
- **202 + polling** — Ansible playbooks run 5–15 minutes; synchronous HTTP would time out n8n. Asynchronous job model avoids this entirely
- **In-memory job store** — sufficient for homelab single-instance deployment; no Redis/database dependency
- **Synology placement** — same host as n8n → internal Docker network communication, no Traefik hop for n8n→webhook calls
- **Repo mounted read-only** — container always runs the current version of playbooks from the cloned repo on the NAS

## Alternatives Considered

- **Ansible Semaphore** — full UI + DB + RBAC; over-engineered for a single-operator homelab
- **AWX/Tower** — same concern; requires PostgreSQL, Redis, significant resource overhead
- **Direct n8n SSH Execute** — n8n has an SSH node but it blocks the workflow, no async, no audit log
- **Celery + Redis** — overkill for homelab; adds two services for the same result

## Consequences

- Repo must be cloned at `/volume1/homelab-dns` on the Synology NAS
- SSH key (`id_rsa`) and Vault password must be placed at `/volume1/secrets/` on the NAS
- `WEBHOOK_API_KEY` must be set in `/volume1/homelab-dns/ansible-webhook/.env` (not committed)
- `ansible.evlab.ch` DNS record + Traefik service added for external access
- OpenAPI docs available at `https://ansible.evlab.ch/docs` (protected by API key)
