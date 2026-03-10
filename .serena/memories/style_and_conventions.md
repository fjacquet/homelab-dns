# Code Style & Conventions

## Ansible

- FQCN required everywhere (e.g., `ansible.builtin.apt`, `community.docker.docker_compose_v2`)
- `no_log: true` on all tasks handling secrets
- `flush_handlers` before API calls that depend on service state
- Vault vars follow `vault_*` naming, referenced from `main.yml`
- Variable naming: `lan_interface` (not `wireguard_interface`) for physical NIC

## Python

- Python 3.12+ with type hints
- uv + PEP 723 inline script metadata for standalone tools
- Pydantic models for data validation (FastAPI webhook)
- No requirements.txt — deps in pyproject.toml or inline metadata

## Documentation

- MkDocs Material, GitHub Pages deployment
- Mermaid diagrams only (no ASCII art)
- ADRs in `docs/adr/`

## General

- Diagrams: Mermaid (`graph TD/LR`, `sequenceDiagram`, `pie`, `mindmap`)
- No emojis unless explicitly requested
