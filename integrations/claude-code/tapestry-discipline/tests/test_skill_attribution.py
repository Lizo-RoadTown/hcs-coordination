"""B1 (pl-005) plugin side: skill invocations resolve to the exact `repo#path`
the self-observer queries, and anything unresolvable stays visible as
unresolved — never dropped, never given a fake ref.

Plugin skills resolve through a fake ~/.claude (installed_plugins.json ->
known_marketplaces.json -> the clone's marketplace.json). Project skills
resolve through a throwaway git repo with a GitHub-style origin remote.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from skill_attribution import RESOLVED, UNRESOLVED, resolve_skill  # noqa: E402


def _write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data) if not isinstance(data, str) else data,
                    encoding="utf-8")


class PluginSkillTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name) / ".claude"
        self.clone = Path(self._tmp.name) / "clone"
        _write(self.home / "plugins" / "installed_plugins.json",
               {"plugins": {"tapestry-patterns@tapestry": [{"scope": "user"}],
                            "ext-plugin@other": [{"scope": "user"}]}})
        _write(self.home / "plugins" / "known_marketplaces.json", {
            "tapestry": {"source": {"source": "github", "repo": "Lizo-RoadTown/tapestry"},
                         "installLocation": str(self.clone)},
            "other": {"source": {"source": "github", "repo": "someone/other"},
                      "installLocation": str(self.clone)},
        })
        _write(self.clone / ".claude-plugin" / "marketplace.json", {"plugins": [
            {"name": "tapestry-patterns",
             "source": "./integrations/claude-code/tapestry-patterns"},
            {"name": "ext-plugin", "source": {"source": "url", "url": "https://x"}},
        ]})
        _write(self.clone / "integrations/claude-code/tapestry-patterns/skills/"
               "project-launch/SKILL.md", "---\nname: project-launch\n---\n")

    def tearDown(self):
        self._tmp.cleanup()

    def test_plugin_skill_resolves_to_self_observer_join_key(self):
        a = resolve_skill("tapestry-patterns:project-launch", claude_home=self.home)
        self.assertEqual(a.resolution, RESOLVED)
        self.assertEqual(
            a.artifact_ref,
            "Lizo-RoadTown/tapestry#integrations/claude-code/"
            "tapestry-patterns/skills/project-launch/SKILL.md",
        )

    def test_skill_missing_from_clone_is_unresolved(self):
        a = resolve_skill("tapestry-patterns:no-such-skill", claude_home=self.home)
        self.assertEqual((a.artifact_ref, a.resolution), (None, UNRESOLVED))
        self.assertEqual(a.skill_name, "tapestry-patterns:no-such-skill")

    def test_uninstalled_plugin_is_unresolved(self):
        a = resolve_skill("not-installed:x", claude_home=self.home)
        self.assertEqual((a.artifact_ref, a.resolution), (None, UNRESOLVED))

    def test_external_source_plugin_is_unresolved(self):
        a = resolve_skill("ext-plugin:x", claude_home=self.home)
        self.assertEqual((a.artifact_ref, a.resolution), (None, UNRESOLVED))

    def test_missing_metadata_never_raises(self):
        a = resolve_skill("tapestry-patterns:project-launch",
                          claude_home=Path(self._tmp.name) / "nowhere")
        self.assertEqual(a.resolution, UNRESOLVED)

    def test_empty_name_is_unresolved(self):
        self.assertEqual(resolve_skill("").resolution, UNRESOLVED)


class ProjectSkillTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "proj"
        self.repo.mkdir()

        def git(*args):
            subprocess.run(["git", *args], cwd=self.repo, check=True,
                           capture_output=True)
        git("init", "-q")
        git("config", "user.email", "t@example.com")
        git("config", "user.name", "t")
        git("remote", "add", "origin", "https://github.com/Owner/proj.git")
        _write(self.repo / ".claude/skills/tracked-skill/SKILL.md", "x")
        _write(self.repo / ".claude/skills/untracked-skill/SKILL.md", "x")
        git("add", ".claude/skills/tracked-skill/SKILL.md")
        git("commit", "-q", "-m", "init")

    def tearDown(self):
        self._tmp.cleanup()

    def test_tracked_project_skill_resolves(self):
        a = resolve_skill("tracked-skill", cwd=self.repo)
        self.assertEqual(a.resolution, RESOLVED)
        self.assertEqual(a.artifact_ref,
                         "Owner/proj#.claude/skills/tracked-skill/SKILL.md")

    def test_untracked_project_skill_is_unresolved(self):
        # Exists locally but not in git: the self-observer (which scans
        # GitHub) could never join it, so it must not claim "resolved".
        a = resolve_skill("untracked-skill", cwd=self.repo)
        self.assertEqual((a.artifact_ref, a.resolution), (None, UNRESOLVED))

    def test_unknown_project_skill_is_unresolved(self):
        a = resolve_skill("nope", cwd=self.repo)
        self.assertEqual(a.resolution, UNRESOLVED)


if __name__ == "__main__":
    unittest.main()
