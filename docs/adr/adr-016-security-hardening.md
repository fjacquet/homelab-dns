# ADR-016: Security Hardening and Idempotency Fixes

**Date:** 2026-03-08 | **Status:** ✅ Accepted

## Context

A comprehensive code review identified 23 issues across security, idempotency, and code quality. The most critical findings were:

1. **Secrets in plaintext on disk** — vault-decrypted credentials rendered directly into Docker Compose environment variables
2. **API tokens in URL query strings** — Technitium API calls used GET with tokens in URLs, leaking to logs
3. **Non-idempotent iptables** — individual `ansible.builtin.iptables` tasks accumulated duplicate rules on each run
4. **Webhook engine fail-open** — missing API key caused HTTP 500 instead of startup refusal
5. **Docker installed via curl-pipe-bash** — supply chain risk, not auditable

## Decisions

### Secrets Management

Secrets are no longer rendered into Docker Compose YAML files. Instead:

- Each service gets a `.env` file deployed with `mode: 0600`, `owner: root`, `no_log: true`
- Docker Compose references secrets via `env_file:` directive
- All Technitium API calls converted from GET (token in URL) to POST (token in body)
- `no_log: true` added to every task that handles API tokens

### Firewall Idempotency

Individual `ansible.builtin.iptables` tasks replaced with a single Jinja2 template (`iptables-rules.v4.j2`) applied via `iptables-restore`. This guarantees:

- Correct rule ordering (ACCEPT before DROP)
- No duplicate rules on re-run
- Single source of truth for firewall state

### Docker Installation

The `get.docker.com` convenience script replaced with the official APT repository method:

- Docker GPG key stored at `/etc/apt/keyrings/docker.asc`
- APT repository added via `ansible.builtin.apt_repository`
- `docker-ce`, `docker-ce-cli`, `containerd.io`, `docker-compose-plugin` installed via `apt`
- Fully idempotent — no conditional `docker --version` check needed

### Container Image Pinning

All `:latest` tags replaced with major/minor version pins to prevent silent breaking changes:

| Image | Pin |
|-------|-----|
| technitium/dns-server | `:14` |
| traefik | `:v3.6` |
| prom/prometheus | `:v3` |
| grafana/grafana | `:11` |
| checkmk/check-mk-raw | `:2.3` |
| n8nio/n8n | `:1` |

### Webhook Hardening

- Startup fails immediately if `WEBHOOK_API_KEY` is unset
- `tags` and `limit` fields validated via regex allowlists
- Job store bounded: `MAX_JOBS=200` with oldest-finished eviction, `MAX_LOG_LINES=1000` per job
- Healthcheck added to Docker Compose definitions
- SSH host key checking enabled with pre-populated `known_hosts`

### Code Deduplication

- Node exporter installation extracted into `roles/node_exporter/` (was duplicated across `site.yml` and `microcloud-prepare.yml`)
- `dns_primary_ip`/`dns_secondary_ip` derived from inventory via `hostvars` (was hardcoded in both `main.yml` and `inventory.yml`)

## Consequences

- **Secrets rotation** requires updating `.env` files (deployed automatically on next `site.yml` run)
- **Container upgrades** require explicit version bump in `group_vars/all/main.yml` or `microcloud-services.yml`
- **Firewall changes** are managed entirely through `templates/iptables-rules.v4.j2`
- **Node exporter updates** only need changes in `roles/node_exporter/tasks/main.yml`
