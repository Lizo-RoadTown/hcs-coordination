"""Tests for the ADR 0010 shared-space + private-files guard wiring in init.

Pure/no-network: exercises the file-writing + env helpers directly. Run from
packages/cli/:  python -m pytest tests/ -q
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tapestry_cli import init  # noqa: E402

# Repo root = .../tapestry  (tests -> cli -> packages -> repo)
REPO_ROOT = Path(__file__).resolve().parents[3]


def _norm(s: str) -> str:
    """Compare ignoring trailing whitespace + line-ending differences (git may
    rewrite LF<->CRLF on checkout)."""
    return "\n".join(line.rstrip() for line in s.splitlines())


# ---------------------------------------------------------------------------
# .gitignore carries the private-shared entries
# ---------------------------------------------------------------------------

def test_gitignore_lines_include_shared_mount_and_pointer():
    assert ".shared/" in init._GITIGNORE_LINES
    assert ".tapestry-shared.local" in init._GITIGNORE_LINES


def test_skeleton_gitignore_ignores_shared(tmp_path):
    init._write_project_skeleton(tmp_path, "p", "P", "")
    gi = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".shared/" in gi
    assert ".tapestry-shared.local" in gi


# ---------------------------------------------------------------------------
# _setup_shared_space — optional; off when unset, wired when set
# ---------------------------------------------------------------------------

def test_shared_space_off_when_unset(tmp_path, monkeypatch):
    monkeypatch.delenv("TAPESTRY_SHARED_DIR", raising=False)
    proj = tmp_path / "proj"
    proj.mkdir()
    init._setup_shared_space(proj, "demo")
    assert not (proj / ".tapestry-shared.local").exists()
    assert not (proj / ".shared").exists()


def test_shared_space_wires_subfolder_and_pointer_when_set(tmp_path, monkeypatch):
    root = tmp_path / "synced"
    monkeypatch.setenv("TAPESTRY_SHARED_DIR", str(root))
    proj = tmp_path / "proj"
    proj.mkdir()
    init._setup_shared_space(proj, "demo-proj")
    # per-project subfolder created under the shared root
    assert (root / "demo-proj").is_dir()
    # git-ignored pointer file records the absolute path
    pointer = proj / ".tapestry-shared.local"
    assert pointer.exists()
    assert pointer.read_text(encoding="utf-8").strip().endswith("demo-proj")


# ---------------------------------------------------------------------------
# _seed_guard — writes the three guard files, idempotent
# ---------------------------------------------------------------------------

_GUARD_FILES = [
    "scripts/check_private_committed.py",
    ".githooks/pre-commit",
    ".github/workflows/private-files-check.yml",
]


def test_seed_guard_writes_all_files(tmp_path):
    init._seed_guard(tmp_path)  # tmp_path has no .git -> core.hooksPath step skipped
    for rel in _GUARD_FILES:
        assert (tmp_path / rel).exists(), f"missing {rel}"


def test_seed_guard_is_idempotent(tmp_path):
    init._seed_guard(tmp_path)
    (tmp_path / ".githooks" / "pre-commit").write_text("EDITED\n", encoding="utf-8")
    init._seed_guard(tmp_path)  # must not clobber
    assert (tmp_path / ".githooks" / "pre-commit").read_text(encoding="utf-8") == "EDITED\n"


# ---------------------------------------------------------------------------
# No drift: seeded templates match the tapestry-repo copies byte-for-byte
# ---------------------------------------------------------------------------

def test_seeded_templates_match_repo_copies():
    pairs = [
        (init._CHECK_SCRIPT, REPO_ROOT / "scripts" / "check_private_committed.py"),
        (init._PRECOMMIT_HOOK, REPO_ROOT / ".githooks" / "pre-commit"),
        (init._PRIVATE_FILES_WORKFLOW, REPO_ROOT / ".github" / "workflows" / "private-files-check.yml"),
    ]
    for template, repo_file in pairs:
        assert repo_file.exists(), f"repo copy missing: {repo_file}"
        assert _norm(template) == _norm(repo_file.read_text(encoding="utf-8")), (
            f"drift between init template and {repo_file.name}"
        )


# ---------------------------------------------------------------------------
# The seeded check script's logic actually flags the forbidden paths
# ---------------------------------------------------------------------------

def _load_check_module():
    path = REPO_ROOT / "scripts" / "check_private_committed.py"
    spec = importlib.util.spec_from_file_location("_check_private_committed", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_check_script_forbidden_logic():
    chk = _load_check_module()
    assert chk._is_forbidden(".shared/notes.pdf") is True
    assert chk._is_forbidden(".tapestry-shared.local") is True
    assert chk._is_forbidden("src/app.py") is False
    assert chk._is_forbidden("docs/README.md") is False


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
