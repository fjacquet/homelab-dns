# ADR-011: Mermaid as Documentation Diagram Standard

**Date:** 2026-03-08 | **Status:** ✅ Accepted

## Context

The project used ASCII art for architecture diagrams and markdown tables for structured data throughout `README.md`, `ARD.md`, `PRD.md`, and `USER-GUIDE.md`. ASCII art is fragile to edit, doesn't scale, and doesn't render interactively.

## Decision

Replace all ASCII art and markdown tables that represent relationships or flows with **Mermaid diagrams** (`graph TD/LR`, `sequenceDiagram`, `pie`, `mindmap`). Markdown tables are kept only for simple reference data (e.g., quick-reference credentials).

## Rationale

```mermaid
mindmap
  root((Mermaid))
    Authoring
      Plain text in markdown
      Version control friendly
      Diff-readable
    Rendering
      Native GitHub rendering
      MkDocs Material built-in
      No external service
    Diagram types used
      graph TD/LR — architecture & flows
      sequenceDiagram — API interactions
      pie — split ratios
      mindmap — concept maps
```

## Alternatives Considered

- **PlantUML** — requires a render server or local Java; no native GitHub rendering
- **draw.io / Excalidraw** — binary format, not diff-friendly, external dependency
- **ASCII art** — no learning curve, but fragile and visually poor at scale

## Consequences

- All new ADRs include at least one Mermaid diagram illustrating the decision
- `README.md`, `docs/index.md`, and all ADR files use Mermaid for architecture, flows, and comparisons
- MkDocs Material renders Mermaid natively via `pymdownx.superfences` — no plugin needed
- GitHub renders Mermaid natively in `.md` files as of 2022
