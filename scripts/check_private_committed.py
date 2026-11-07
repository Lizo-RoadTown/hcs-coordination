#!/usr/bin/env python3
"""Guard: fail if private shared material is tracked or staged in git.

ADR 0010. The local mount `.shared` links to the operator's external synced
directory (`$TAPESTRY_SHARED_DIR/<slug>/`), and `.tapestry-shared.local` holds
that absolute path. Both are git-ignored and must NEVER be committed.

Used by both guard layers: the git pre-commit hook (staged files) and the CI
workflow (tracked tree, the authoritative backstop). Stdlib-only.

Matching is done by git pathspec with -z (NUL-delimited output), so git's
path-quoting and unusual filenames cannot slip past the guard.
"""
from __future__ import annotations

import subprocess
import sys

# Pathspecs git matches directly: the mount (dir or symlink) and anything under
# it, plus the pointer file. Using pathspecs (not string prefixes on possibly-
# quoted output) is what closes the parser-differential bypass.
PATHSPECS = (".shared", ".tapestry-shared.local")
# Secondary pure-string check — belt-and-suspenders + unit-testable.
FORBIDDEN_NAMES = (".shared", ".tapestry-shared.local")
FORBIDDEN_PREFIXES = (".shared/",)


def _git_paths(args: list[str]) -> list[str]:
    """Run git with NUL-delimited output; return the non-empty path entries.
    Empty list on any failure. Decodes with surrogateescape so odd bytes in a
    filename never raise."""
    try:
        r = subprocess.run(["git", *args], capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return []
    if r.returncode != 0:
        return []
    out = r.stdout.decode("utf-8", "surrogateescape")
    return [p for p in out.split("\0") if p]


def _is_forbidden(path: str) -> bool:
    return path in FORBIDDEN_NAMES or any(path.startswith(p) for p in FORBIDDEN_PREFIXES)


def main() -> int:
    staged = _git_paths(["diff", "--cached", "--name-only", "-z", "--", *PATHSPECS])
    tracked = _git_paths(["ls-files", "-z", "--", *PATHSPECS])
    bad = sorted({p for p in (*staged, *tracked) if _is_forbidden(p)})
    if not bad:
        return 0
    print("ERROR: private shared material must never be committed (ADR 0010):", file=sys.stderr)
    for p in bad:
        print(f"  {p}", file=sys.stderr)
    print(
        "\n`.shared` is the local mount of your external synced folder, and "
        "`.tapestry-shared.local` points at it. Both are git-ignored on purpose. "
        "Move the file out of `.shared` before committing. (A forced `git add -f` "
        "is the usual cause.)",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
