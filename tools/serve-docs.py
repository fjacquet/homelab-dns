#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "mkdocs-material>=9.5",
# ]
# ///
"""Serve or build MkDocs documentation.

Usage:
    uv run tools/serve-docs.py          # serve with live reload
    uv run tools/serve-docs.py build    # build static site to site/
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "serve"
    if cmd not in ("serve", "build"):
        sys.exit(f"Unknown command: {cmd!r}. Use 'serve' or 'build'.")
    subprocess.run(["mkdocs", cmd], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
