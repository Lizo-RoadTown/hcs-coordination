"""Tests for the v0.1.12 scope gate (`_in_scope`) across all four hooks.

Run from the plugin root:

    python -m unittest integrations/claude-code/tapestry-discipline/tests/test_scope.py

v0.1.12 fix: the scope gate used to be a cwd-substring allowlist only
(Make_Skills / the-loom / project-starter / _common). A fully-wired
consuming project — LOOM_PROJECT_ID set in its .env, CLAUDE.md referencing
the discipline — silently no-op'd every hook because its path matched no
substring (e.g. C:\\Users\\Liz\\SDE_Extraction). The gate now ALSO returns
True when LOOM_PROJECT_ID is set. These tests pin both arms of that OR for
each of the four hook scripts, which carry identical `_in_scope` copies
(self-contained-script convention — no shared import the gate depends on).
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

# Import all four hooks under test (mirrors test_pre_tool_use.py pattern).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import pre_tool_use  # noqa: E402
import stop_audit  # noqa: E402
import user_prompt_submit  # noqa: E402
import session_start  # noqa: E402

MODULES = (pre_tool_use, stop_audit, user_prompt_submit, session_start)

# An out-of-scope path: no loom substring anywhere in it.
OUT_OF_SCOPE_CWD = r"C:\Users\Liz\SDE_Extraction"


def _call(mod, cwd, project_id=None, scope_dirs=None):
    """Call mod._in_scope(cwd) with LOOM_PROJECT_ID and TAPESTRY_SCOPE_DIRS
    controlled deterministically.

    Replaces os.environ wholesale so ambient values (e.g. loaded from a
    project .env at import time) cannot leak into the no-opt-in cases.
    """
    env = dict(os.environ)
    env.pop("LOOM_PROJECT_ID", None)
    env.pop("TAPESTRY_SCOPE_DIRS", None)
    if project_id is not None:
        env["LOOM_PROJECT_ID"] = project_id
    if scope_dirs is not None:
        env["TAPESTRY_SCOPE_DIRS"] = scope_dirs
    with mock.patch.dict(os.environ, env, clear=True):
        return mod._in_scope(cwd)


class TestScopeGate(unittest.TestCase):
    def test_all_hooks_expose_in_scope(self):
        for mod in MODULES:
            self.assertTrue(
                hasattr(mod, "_in_scope"),
                f"{mod.__name__} is missing the _in_scope helper",
            )

    def test_out_of_scope_without_project_id(self):
        for mod in MODULES:
            with self.subTest(mod=mod.__name__):
                self.assertFalse(_call(mod, OUT_OF_SCOPE_CWD, project_id=None))

    def test_out_of_scope_with_project_id_is_in_scope(self):
        # The core v0.1.12 fix: LOOM_PROJECT_ID set -> in scope.
        for mod in MODULES:
            with self.subTest(mod=mod.__name__):
                self.assertTrue(_call(mod, OUT_OF_SCOPE_CWD, project_id="sde-extraction"))

    def test_empty_project_id_does_not_opt_in(self):
        # Empty / whitespace value must not count as opt-in.
        for mod in MODULES:
            with self.subTest(mod=mod.__name__):
                self.assertFalse(_call(mod, OUT_OF_SCOPE_CWD, project_id=""))
                self.assertFalse(_call(mod, OUT_OF_SCOPE_CWD, project_id="   "))

    def test_no_hardcoded_substrings(self):
        # v0.1.24: the plugin ships universal. Paths that USED to be
        # hardcoded-in-scope are out of scope without an explicit opt-in.
        for cwd in (
            r"C:\Users\Liz\Make_Skills",
            r"C:\Users\Liz\the-loom\adapters",
            r"C:\Users\Liz\project-starter",
            r"templates/_common/foo",
        ):
            for mod in MODULES:
                with self.subTest(mod=mod.__name__, cwd=cwd):
                    self.assertFalse(_call(mod, cwd, project_id=None))

    def test_scope_dirs_allowlist_opts_in(self):
        # TAPESTRY_SCOPE_DIRS is the path-based opt-in: comma-separated
        # substrings, matched case-insensitively.
        for mod in MODULES:
            with self.subTest(mod=mod.__name__):
                self.assertTrue(_call(
                    mod, r"C:\Users\Liz\the-loom\adapters",
                    scope_dirs="make_skills, the-loom",
                ))
                self.assertTrue(_call(
                    mod, r"C:\Users\Liz\The-Loom",
                    scope_dirs="the-loom",
                ))
                self.assertFalse(_call(
                    mod, OUT_OF_SCOPE_CWD,
                    scope_dirs="make_skills, the-loom",
                ))
                # Empty/whitespace entries never match everything.
                self.assertFalse(_call(
                    mod, OUT_OF_SCOPE_CWD, scope_dirs=" , ,  ",
                ))

    def test_accepts_pathlib_path(self):
        # session_start passes a Path; the helper must handle non-str cwd.
        for mod in MODULES:
            with self.subTest(mod=mod.__name__):
                self.assertTrue(
                    _call(mod, Path(r"C:\Users\Liz\the-loom"),
                          scope_dirs="the-loom")
                )
                self.assertFalse(
                    _call(mod, Path(OUT_OF_SCOPE_CWD), project_id=None)
                )


if __name__ == "__main__":
    unittest.main()
