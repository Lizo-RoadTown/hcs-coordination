#!/usr/bin/env python3
"""Guard: fail if private shared material is tracked or staged in git.

ADR 0010. The local mount `.shared/` links to the operator's external synced
directory (`$TAPESTRY_SHARED_DIR/<slug>/`), and `.tapestry-shared.local` holds
that absolute path. Both are git-ignored and must NEVER be committed.

Used by both guard layers: the git pre-commit hook (staged files) and the CI
workflow (tracked tree, the authoritative backstop). Stdlib-only.
"""
from __future__ import annotations

import subprocess
import sys

FORBIDDEN_PREFIXES = (".shared/",)
FORBIDDEN_NAMES = (".tapestry-shared.local",)


def _git_lines(args: list[str]) -> list[str]:
    try:
        r = subprocess.run(["git", *args], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return []
    if r.returncode != 0:
        return []
    return [ln for ln in r.stdout.splitlines() if ln.strip()]


def _is_forbidden(path: str) -> bool:
    return path in FORBIDDEN_NAMES or any(path.startswith(p) for p in FORBIDDEN_PREFIXES)


def main() -> int:
    staged = _git_lines(["diff", "--cached", "--name-only"])
    tracked = _git_lines(["ls-files"])
    bad = sorted({p for p in (*staged, *tracked) if _is_forbidden(p)})
    if not bad:
        return 0
    print("ERROR: private shared material must never be committed (ADR 0010):", file=sys.stderr)
    for p in bad:
        print(f"  {p}", file=sys.stderr)
    print(
        "\n`.shared/` is the local mount of your external synced folder, and "
        "`.tapestry-shared.local` points at it. Both are git-ignored on purpose. "
        "Move the file out of `.shared/` before committing. (A forced `git add -f` "
        "is the usual cause.)",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
