#!/usr/bin/env python3
"""Validate YAML frontmatter of every docs-site content page.

Why this exists: an unquoted frontmatter `description` containing ": " in
systems/observatory.md broke every Vercel deployment for six PRs before
anyone read the build log (docs/changelog/2026-11-08-copilot-review-replaces-
claude-ci-review.md has the story; the fix was 2026-11-08). Starlight only
validates frontmatter during `astro build`, which runs on Vercel — this check
catches the same class of failure in CI, before the deploy.

Usage: python scripts/check_docs_frontmatter.py [content_root]
Default root: apps/docs-site/src/content/docs. Exit 1 on any invalid page.
Requires PyYAML.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

DEFAULT_ROOT = Path("apps/docs-site/src/content/docs")


def check_file(path: Path) -> str | None:
    """Return an error string for this file, or None if its frontmatter is OK."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return f"{path}: unreadable ({e})"
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return f"{path}: missing frontmatter block (must start with ---)"
    try:
        end = next(i for i, l in enumerate(lines[1:], 1) if l.strip() == "---")
    except StopIteration:
        return f"{path}: frontmatter never closed (no second ---)"
    block = "\n".join(lines[1:end])
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        where = f" (frontmatter line {mark.line + 1}, col {mark.column + 1})" if mark else ""
        return f"{path}: invalid YAML{where}: {getattr(e, 'problem', e)}"
    if not isinstance(data, dict):
        return f"{path}: frontmatter is not a mapping"
    if not data.get("title"):
        return f"{path}: frontmatter has no title"
    return None


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ROOT
    if not root.is_dir():
        print(f"content root not found: {root}")
        return 1
    pages = sorted(list(root.rglob("*.md")) + list(root.rglob("*.mdx")))
    errors = [e for e in (check_file(p) for p in pages) if e]
    for e in errors:
        print(f"FRONTMATTER: {e}")
    print(f"checked {len(pages)} pages, {len(errors)} invalid")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
