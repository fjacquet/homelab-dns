---
name: new-adr
description: Create a new Architecture Decision Record in docs/adr/. Auto-sequences the ADR number from existing files, creates the .md file with standard homelab-dns template, and adds the nav entry to mkdocs.yml.
---

The user wants to create a new Architecture Decision Record (ADR).

## Step 1: Determine next ADR number

Run this to find the highest existing number:
```bash
ls docs/adr/adr-*.md | sed -E 's/.*adr-([0-9]+).*/\1/' | sort -n | tail -1
```
Increment by 1 and zero-pad to 3 digits (e.g., if last is 18, next is 019).

## Step 2: Gather information

If the user hasn't provided a title and decision summary, ask:
- "What is the ADR title?" (short phrase, e.g., "SNMP Monitoring via Prometheus")
- "What decision was made and why?"

## Step 3: Create the ADR file

Filename: `docs/adr/adr-NNN-<kebab-case-title>.md`

Use this template:
```markdown
# ADR-NNN: <Title>

## Status
Accepted

## Context
<Why this decision was needed — what problem or question prompted it>

## Decision
<What was decided — be specific about the chosen approach>

## Consequences

### Positive
- <benefit>

### Negative / Trade-offs
- <trade-off or limitation>

### Neutral
- <implementation notes or follow-up items>
```

## Step 4: Update mkdocs.yml nav

Add the new ADR to the `Architecture Decisions:` section in `mkdocs.yml`, following the existing pattern:
```yaml
      - ADR-NNN <Short Title>: adr/adr-NNN-<kebab-title>.md
```

Insert it after the last existing ADR entry.

## Step 5: Confirm

Show the user:
- The created file path
- The mkdocs.yml nav entry added
- Suggest: "Run `uv run python tools/serve-docs.py` to preview locally"
