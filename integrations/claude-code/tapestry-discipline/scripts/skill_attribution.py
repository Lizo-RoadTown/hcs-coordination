"""Resolve a Skill invocation to a stable artifact_ref (B1, component pl-005).

The self-observer identifies a skill by (repo, file_path) and the telemetry
read API normalizes that to `repo#file_path` (services/telemetry-ingestion/
read_api.py:71-90). For a finding to link to real usage, a captured invocation
must carry EXACTLY that string. This module produces it.

Two skill-name shapes reach the Skill tool:

  "<plugin>:<skill>"  a plugin skill. Resolved through Claude Code's own plugin
                      metadata, with no repo names hardcoded:
                        installed_plugins.json  -> which marketplace it came from
                        known_marketplaces.json -> that marketplace's GitHub repo
                                                   and local clone
                        <clone>/.claude-plugin/marketplace.json -> the plugin's
                                                   source path inside the repo
                      -> "<owner>/<repo>#<source>/skills/<skill>/SKILL.md",
                      confirmed against the local clone.
  "<skill>"           a project skill. Looked up under the current repo's
                      .claude/skills/ and skills/ (the paths the self-observer
                      scans in consuming repos, self-observer/config.py:99-105)
                      -> "<owner>/<repo>#<path>/<skill>/SKILL.md", repo taken
                      from the git remote.

Anything that cannot be resolved is NOT dropped and NOT given a fake ref. It is
returned as unresolved with the raw name, so the event stays countable while
staying out of per-artifact scoring (project-observatory/signals.py drops
NULL refs; a fake ref would be scored as a real artifact).

Never raises: every failure degrades to unresolved.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import NamedTuple

RESOLVED = "resolved"
UNRESOLVED = "unresolved"

_GITHUB_REMOTE_RE = re.compile(
    r"github\.com[:/]+(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+?)(?:\.git)?/?$"
)


class Attribution(NamedTuple):
    artifact_ref: str | None
    resolution: str  # RESOLVED | UNRESOLVED
    skill_name: str


def _claude_home() -> Path:
    override = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(override) if override else Path.home() / ".claude"


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _resolve_plugin_skill(plugin: str, skill: str, claude_home: Path) -> str | None:
    plugins_dir = claude_home / "plugins"
    installed = _load_json(plugins_dir / "installed_plugins.json") or {}
    known = _load_json(plugins_dir / "known_marketplaces.json") or {}

    marketplaces = [
        key.split("@", 1)[1]
        for key in (installed.get("plugins") or {})
        if "@" in key and key.split("@", 1)[0] == plugin
    ]
    for mkt in marketplaces:
        info = known.get(mkt) or {}
        repo = (info.get("source") or {}).get("repo")
        clone = info.get("installLocation")
        if not repo or not clone:
            continue
        manifest = _load_json(Path(clone) / ".claude-plugin" / "marketplace.json") or {}
        for entry in manifest.get("plugins") or []:
            if entry.get("name") != plugin:
                continue
            source = entry.get("source")
            if not isinstance(source, str):
                continue  # external (url/github) sources: not resolvable to this repo
            rel = source.strip().lstrip("./").rstrip("/")
            skill_rel = f"{rel}/skills/{skill}/SKILL.md" if rel else f"skills/{skill}/SKILL.md"
            if (Path(clone) / skill_rel).is_file():
                return f"{repo}#{skill_rel}"
    return None


def _git(cwd: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args], cwd=str(cwd), capture_output=True, text=True,
            timeout=3, check=True,
        )
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _resolve_project_skill(skill: str, cwd: Path) -> str | None:
    top = _git(cwd, "rev-parse", "--show-toplevel")
    if not top:
        return None
    remote = _git(cwd, "remote", "get-url", "origin")
    m = _GITHUB_REMOTE_RE.search(remote or "")
    if not m:
        return None
    repo = f"{m.group('owner')}/{m.group('repo')}"
    root = Path(top)
    for base in (".claude/skills", "skills"):
        rel = f"{base}/{skill}/SKILL.md"
        # Must exist AND be tracked: the self-observer scans GitHub, so an
        # untracked/gitignored local skill can never be joined. "Resolved"
        # means joinable; anything else stays visible as unresolved.
        if (root / rel).is_file() and _git(root, "ls-files", "--error-unmatch", rel):
            return f"{repo}#{rel}"
    return None


def resolve_skill(skill_name: str, cwd: str | os.PathLike | None = None,
                  claude_home: Path | None = None) -> Attribution:
    """Resolve a Skill-tool `skill` argument to an Attribution. Never raises."""
    raw = (skill_name or "").strip()
    if not raw:
        return Attribution(None, UNRESOLVED, raw)
    try:
        if ":" in raw:
            plugin, skill = raw.split(":", 1)
            ref = _resolve_plugin_skill(plugin.strip(), skill.strip(),
                                        claude_home or _claude_home())
        else:
            ref = _resolve_project_skill(raw, Path(cwd or os.getcwd()))
    except Exception:  # noqa: BLE001 — capture must never break the hook
        ref = None
    if ref and len(ref) <= 512:
        return Attribution(ref, RESOLVED, raw)
    return Attribution(None, UNRESOLVED, raw)
