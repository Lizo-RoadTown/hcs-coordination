"""Tests for v0.1.19: permanent session-report persistence + resolver version-glob.

Run from the plugin root:

    python -m unittest integrations/claude-code/tapestry-discipline/tests/test_session_report_persist.py

Covers:
1. _scan_session_metrics captures the report body + record name from the
   memory_write tool block.
2. _persist_report_to_disk writes the report to docs/session-reports/, is
   idempotent, and no-ops on empty content. Git auto-commit is mocked out so the
   tests never touch any repo.
3. _resolve_patterns_scripts_dir returns a valid scripts dir (smoke) — the
   version-glob branch is additionally verified manually against the real
   .../tapestry-patterns/0.1.2/scripts install.
"""
from __future__ import annotations

import json
import sys
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Mirror the import pattern used by the other tests in this dir.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import stop_audit  # noqa: E402
import session_start  # noqa: E402


def _memory_write_report_entry(name: str, content: str) -> dict:
    return {
        "role": "assistant",
        "content": [
            {
                "type": "tool_use",
                "name": "mcp__loom-memory__memory_write",
                "input": {"name": name, "content": content, "record_type": "lesson"},
            }
        ],
    }


def _jsonl(*entries: dict) -> str:
    return "\n".join(json.dumps(e) for e in entries) + "\n"


class ScanCapturesReport(unittest.TestCase):
    def test_captures_content_and_name(self):
        name = "upskilling_report_session_2026_08_29"
        content = "# Upskilling report\n\nSkills invoked: foo (3 uses)\n"
        raw = _jsonl(_memory_write_report_entry(name, content))
        m = stop_audit._scan_session_metrics(raw)
        self.assertTrue(m["upskilling_report_seen"])
        self.assertEqual(m["report_name"], name)
        self.assertEqual(m["report_content"], content)

    def test_no_report_leaves_fields_empty(self):
        raw = _jsonl({"role": "assistant", "content": [{"type": "text", "text": "hi"}]})
        m = stop_audit._scan_session_metrics(raw)
        self.assertFalse(m["upskilling_report_seen"])
        self.assertEqual(m["report_content"], "")
        self.assertEqual(m["report_name"], "")


class PersistReport(unittest.TestCase):
    """v0.1.28: reports go to the shared space or ~/.claude, never into the repo."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.repo = base / "repo"; self.repo.mkdir()
        self.shared = base / "shared"
        self.home = base / "home"
        self._env = mock.patch.dict(os.environ, {"TAPESTRY_SHARED_DIR": str(self.shared),
                                                 "LOOM_PROJECT_ID": "proj"}, clear=False)
        self._env.start()
        self._home = mock.patch.object(Path, "home", lambda: self.home)
        self._home.start()

    def tearDown(self):
        self._home.stop(); self._env.stop(); self._tmp.cleanup()

    def _assert_repo_untouched(self):
        self.assertFalse((self.repo / "docs" / "session-reports").exists(),
                         "a report was written into the working repo")

    def test_writes_to_shared_space_with_header_and_body(self):
        content = "# Upskilling report\n\nSkills invoked: foo (3 uses)"
        out = stop_audit._persist_report_to_disk(
            str(self.repo), "abcd1234efgh", content, "upskilling_report_session_2026_08_29")
        p = Path(out)
        self.assertEqual(p, self.shared / "proj" / "session-reports" / "2026-08-29-abcd1234.md")
        text = p.read_text(encoding="utf-8")
        self.assertIn("session: abcd1234efgh", text)
        self.assertIn("memory_record: upskilling_report_session_2026_08_29", text)
        self.assertIn("Skills invoked: foo (3 uses)", text)
        self._assert_repo_untouched()

    def test_pointer_file_used_when_no_env(self):
        target = Path(self._tmp.name) / "pointed"
        (self.repo / ".tapestry-shared.local").write_text(str(target) + "\n", encoding="utf-8")
        with mock.patch.dict(os.environ, {"TAPESTRY_SHARED_DIR": ""}):
            out = stop_audit._persist_report_to_disk(
                str(self.repo), "abcd1234", "# body", "upskilling_report_session_2026_08_29")
        self.assertEqual(Path(out).parent, target / "session-reports")
        self._assert_repo_untouched()

    def test_falls_back_to_claude_home(self):
        with mock.patch.dict(os.environ, {"TAPESTRY_SHARED_DIR": ""}):
            out = stop_audit._persist_report_to_disk(
                str(self.repo), "abcd1234", "# body", "upskilling_report_session_2026_08_29")
        self.assertEqual(Path(out).parent, self.home / ".claude" / "session-reports" / "proj")
        self._assert_repo_untouched()

    def test_never_invokes_git(self):
        with mock.patch("subprocess.run", side_effect=AssertionError("git must not run")):
            out = stop_audit._persist_report_to_disk(
                str(self.repo), "abcd1234", "# body", "upskilling_report_session_2026_08_29")
        self.assertIsNotNone(out)

    def test_idempotent_second_call_noop(self):
        args = (str(self.repo), "abcd1234", "# Report body", "upskilling_report_session_2026_08_29")
        self.assertIsNotNone(stop_audit._persist_report_to_disk(*args))
        self.assertIsNone(stop_audit._persist_report_to_disk(*args))

    def test_changed_content_rewrites(self):
        name = "upskilling_report_session_2026_08_29"
        stop_audit._persist_report_to_disk(str(self.repo), "abcd1234", "v1", name)
        out = stop_audit._persist_report_to_disk(str(self.repo), "abcd1234", "v2", name)
        self.assertIn("v2", Path(out).read_text(encoding="utf-8"))

    def test_empty_content_noop_and_no_folder_created(self):
        out = stop_audit._persist_report_to_disk(
            str(self.repo), "sid", "   ", "upskilling_report_session_2026_08_29")
        self.assertIsNone(out)
        self.assertFalse(self.shared.exists())  # folder only created when a report is written
        self._assert_repo_untouched()


class ResolverGlob(unittest.TestCase):
    def test_resolver_returns_valid_scripts_dir(self):
        # Simulate the versioned cache layout the literal path used to miss.
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            scripts = base / "tapestry" / "tapestry-patterns" / "0.1.2" / "scripts"
            scripts.mkdir(parents=True)
            (scripts / "architecture_snapshot.py").write_text("# stub", encoding="utf-8")
            plugin_root = base / "tapestry" / "tapestry-discipline" / "0.1.19"
            plugin_root.mkdir(parents=True)
            with mock.patch.dict("os.environ", {"CLAUDE_PLUGIN_ROOT": str(plugin_root)}):
                got = session_start._resolve_patterns_scripts_dir(base)
            # On a dev checkout the monorepo fallback may resolve first; either way
            # the function must return a real scripts dir containing the script.
            self.assertIsNotNone(got)
            self.assertTrue((got / "architecture_snapshot.py").exists())


if __name__ == "__main__":
    unittest.main()
