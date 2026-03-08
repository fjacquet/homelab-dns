#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "anthropic>=0.45.0",
# ]
# ///
"""Ansible playbook generator and validator using Claude API.

Usage:
    uv run tools/ansible_ai.py generate "Deploy a Redis container with persistence"
    uv run tools/ansible_ai.py validate site.yml
    uv run tools/ansible_ai.py visualize site.yml
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import anthropic

MODEL = "claude-opus-4-6"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ── Context loading ──────────────────────────────────────────────────────────


def load_project_context() -> str:
    """Load existing project files to give Claude full context."""
    parts: list[str] = []

    # Inventory
    inv = PROJECT_ROOT / "inventory.yml"
    if inv.exists():
        parts.append(f"## inventory.yml\n```yaml\n{inv.read_text()}\n```")

    # Group vars (skip vault)
    main_vars = PROJECT_ROOT / "group_vars" / "all" / "main.yml"
    if main_vars.exists():
        parts.append(f"## group_vars/all/main.yml\n```yaml\n{main_vars.read_text()}\n```")

    # Existing playbooks (first 200 lines each to stay within budget)
    for pb in sorted(PROJECT_ROOT.glob("*.yml")):
        if pb.name in ("requirements.yml",):
            continue
        lines = pb.read_text().splitlines()[:200]
        parts.append(f"## {pb.name} (first 200 lines)\n```yaml\n" + "\n".join(lines) + "\n```")

    # Template names (not contents)
    templates = sorted(PROJECT_ROOT.glob("templates/*"))
    if templates:
        names = "\n".join(f"- {t.name}" for t in templates)
        parts.append(f"## Templates available\n{names}")

    return "\n\n".join(parts)


def load_playbook(path: str) -> str:
    """Load a playbook file, resolving relative to project root."""
    p = Path(path)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    if not p.exists():
        sys.exit(f"Error: file not found: {p}")
    return p.read_text()


# ── System prompts ───────────────────────────────────────────────────────────

SYSTEM_GENERATE = """\
You are an expert Ansible automation engineer. You generate production-ready \
Ansible playbooks for a homelab environment.

Rules:
- Follow the existing project conventions (phase-based tasks with tags, \
  Docker Compose via community.docker, variables in group_vars).
- Use FQCN for all modules (ansible.builtin.*, community.docker.*, etc.).
- Use `become: true` where privilege escalation is needed.
- Reference existing variables from group_vars/all/main.yml when possible.
- Add meaningful task names.
- Output ONLY the YAML playbook — no surrounding markdown fences.
"""

SYSTEM_VALIDATE = """\
You are a senior Ansible reviewer. Analyze the given playbook and produce \
a structured report with these sections:

1. **Summary** — one-paragraph overview.
2. **Issues** — a Mermaid flowchart (`graph TD`) showing each issue as a node \
   colored by severity (red=critical, orange=warning, green=info), with edges \
   pointing to the task/line reference.
3. **Best-practice checks** — a Mermaid pie chart showing pass/warn/fail counts.
4. **Security** — flag any secrets in plain text, missing `no_log`, or overly \
   permissive file modes.
5. **Recommendations** — numbered list of concrete fixes.

Use Mermaid diagrams (```mermaid ... ```) instead of ASCII tables everywhere. \
For tabular data use Mermaid flowcharts, pie charts, or mindmaps.
"""

SYSTEM_VISUALIZE = """\
You are an Ansible architecture visualizer. Given a playbook, produce Mermaid \
diagrams that show:

1. **Playbook flow** — a `graph TD` diagram showing plays, phases (tags), and \
   task groups. Color nodes by type (play=blue, phase=green, task=gray).
2. **Host targeting** — a `graph LR` showing which host groups run which plays.
3. **Service dependency map** — a `graph TD` showing services and their \
   dependencies (ports, volumes, networks).
4. **Variable usage** — a `mindmap` showing variable categories and which tasks \
   consume them.

Output ONLY Mermaid diagram blocks (```mermaid ... ```), each preceded by a \
short heading. No ASCII tables.
"""


# ── Streaming helper ─────────────────────────────────────────────────────────


def stream_response(client: anthropic.Anthropic, system: str, user_msg: str) -> str:
    """Stream a Claude response to stdout and return the full text."""
    collected: list[str] = []

    with client.messages.stream(
        model=MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    ) as stream:
        for event in stream:
            if event.type == "content_block_start":
                if getattr(event.content_block, "type", None) == "thinking":
                    print("\n[thinking...]", file=sys.stderr)
            elif event.type == "content_block_delta":
                if event.delta.type == "text_delta":
                    print(event.delta.text, end="", flush=True)
                    collected.append(event.delta.text)
                elif event.delta.type == "thinking_delta":
                    pass  # suppress thinking output

    print()  # trailing newline
    return "".join(collected)


# ── Commands ─────────────────────────────────────────────────────────────────


def cmd_generate(args: argparse.Namespace) -> None:
    """Generate a playbook from a natural language description."""
    client = anthropic.Anthropic()
    context = load_project_context()

    user_msg = (
        f"# Project context\n\n{context}\n\n"
        f"---\n\n"
        f"# Request\n\n"
        f"Generate an Ansible playbook for the following:\n\n"
        f"{args.description}\n\n"
        f"Follow the conventions visible in the project context above."
    )

    result = stream_response(client, SYSTEM_GENERATE, user_msg)

    if args.output:
        out = Path(args.output)
        out.write_text(result)
        print(f"\nSaved to {out}", file=sys.stderr)


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate a playbook with Claude — outputs Mermaid diagrams."""
    client = anthropic.Anthropic()
    context = load_project_context()
    playbook = load_playbook(args.playbook)

    user_msg = (
        f"# Project context\n\n{context}\n\n"
        f"---\n\n"
        f"# Playbook to validate: {args.playbook}\n\n"
        f"```yaml\n{playbook}\n```\n\n"
        f"Produce the validation report using Mermaid diagrams (no ASCII tables)."
    )

    result = stream_response(client, SYSTEM_VALIDATE, user_msg)

    if args.output:
        out = Path(args.output)
        out.write_text(result)
        print(f"\nSaved to {out}", file=sys.stderr)


def cmd_visualize(args: argparse.Namespace) -> None:
    """Visualize a playbook as Mermaid diagrams."""
    client = anthropic.Anthropic()
    playbook = load_playbook(args.playbook)

    user_msg = (
        f"# Playbook to visualize: {args.playbook}\n\n"
        f"```yaml\n{playbook}\n```\n\n"
        f"Produce Mermaid diagrams showing the playbook architecture."
    )

    result = stream_response(client, SYSTEM_VISUALIZE, user_msg)

    if args.output:
        out = Path(args.output)
        out.write_text(result)
        print(f"\nSaved to {out}", file=sys.stderr)


# ── CLI ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ansible playbook AI assistant (Claude API)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
        '  uv run tools/ansible_ai.py generate "Add a Portainer container"\n'
        "  uv run tools/ansible_ai.py validate site.yml\n"
        "  uv run tools/ansible_ai.py visualize site.yml\n",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # generate
    gen = sub.add_parser("generate", help="Generate a playbook from description")
    gen.add_argument("description", help="Natural language description of what to deploy")
    gen.add_argument("-o", "--output", help="Save output to file")
    gen.set_defaults(func=cmd_generate)

    # validate
    val = sub.add_parser("validate", help="Validate a playbook (Mermaid report)")
    val.add_argument("playbook", help="Path to playbook YAML")
    val.add_argument("-o", "--output", help="Save report to file")
    val.set_defaults(func=cmd_validate)

    # visualize
    vis = sub.add_parser("visualize", help="Visualize playbook as Mermaid diagrams")
    vis.add_argument("playbook", help="Path to playbook YAML")
    vis.add_argument("-o", "--output", help="Save output to file")
    vis.set_defaults(func=cmd_visualize)

    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Error: ANTHROPIC_API_KEY environment variable is required")

    args.func(args)


if __name__ == "__main__":
    main()
