# ADR-010: MkDocs + GitHub Pages for Documentation

**Date:** 2026-03-08 | **Status:** ✅ Accepted

## Context

The project had documentation in three markdown files (`PRD.md`, `ARD.md`, `USER-GUIDE.md`) browsable only as raw GitHub markdown. No navigation, no search, no versioning, no cross-linking between documents.

## Decision

Use **MkDocs** with the **Material theme**, deployed automatically to **GitHub Pages** via GitHub Actions on every push to `main` that touches `docs/**` or `mkdocs.yml`.

## Rationale

```mermaid
graph TD
    subgraph Chosen["✅ MkDocs + Material"]
        M1["Native Mermaid rendering"]
        M2["Tab navigation + search"]
        M3["Dark/light mode"]
        M4["Edit on GitHub button"]
        M5["Zero infra — GitHub Pages"]
        M6["uv: no env to manage"]
    end

    subgraph Rejected["❌ Alternatives"]
        R1["Docusaurus — React overhead\nfor a small project"]
        R2["GitBook — paid for private repos,\nexternal service dependency"]
        R3["Sphinx — RST-first,\npoor Mermaid support"]
        R4["Raw GitHub markdown — no\nnavigation or search"]
    end

    style Chosen fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style Rejected fill:#fce4ec,stroke:#e91e63,stroke-width:2px
```

## Deployment pipeline

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant GH as GitHub
    participant CI as GitHub Actions
    participant Pages as GitHub Pages

    Dev->>GH: git push main (docs/** changed)
    GH->>CI: Trigger docs.yml workflow
    CI->>CI: uvx --with mkdocs-material mkdocs build --strict
    CI->>Pages: upload-pages-artifact + deploy-pages
    Pages-->>Dev: https://fjacquet.github.io/homelab-dns/
```

## Consequences

- Docs live at `https://fjacquet.github.io/homelab-dns/` — always in sync with `main`
- `mkdocs build --strict` in CI catches broken links and missing pages at deploy time
- Local preview: `uv run tools/serve-docs.py` (no global installs required)
- `site/` excluded from git via `.gitignore`
