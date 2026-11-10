"""The GitHub scanner must follow repo-rename redirects.

GitHub answers a renamed repo's old name with HTTP 301 (all six module repos were
renamed on 2026-11-10). httpx does not follow redirects by default, so without
follow_redirects=True every scan of an old name returned nothing while the cron still
reported success. Entries must keep the name they were scanned under (target.repo), so
artifact refs stay consistent with B1 capture.
"""
from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

_SVC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SVC))

import github_scanner  # noqa: E402
from config import AuthConfig, RegistryTarget  # noqa: E402

OLD = "Lizo-RoadTown/tapestry"
NEW = "Lizo-RoadTown/hcs-coordination"
DIR = "integrations/claude-code/tapestry-patterns/skills"


def _handler(request: httpx.Request) -> httpx.Response:
    url = str(request.url)
    path = request.url.path  # match on path; the scanner adds ?ref=<branch>
    if f"/repos/{OLD}/" in path:
        return httpx.Response(301, headers={"Location": url.replace(OLD, NEW)})
    if path.endswith(f"/contents/{DIR}"):
        return httpx.Response(200, json=[
            {"type": "dir", "name": "project-launch", "path": f"{DIR}/project-launch"},
        ])
    if path.endswith(f"/contents/{DIR}/project-launch"):
        return httpx.Response(200, json=[
            {"type": "file", "name": "SKILL.md", "path": f"{DIR}/project-launch/SKILL.md",
             "download_url": "https://raw.example/SKILL.md"},
        ])
    if "raw.example" in url or path.endswith("SKILL.md"):
        return httpx.Response(200, text="---\nname: project-launch\ndescription: x\n---\nbody\n")
    return httpx.Response(404)


@pytest.mark.asyncio
async def test_scan_follows_rename_redirect_and_keeps_scanned_name(monkeypatch):
    real_client = httpx.AsyncClient

    def patched(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(_handler)
        return real_client(*args, **kwargs)

    monkeypatch.setattr(github_scanner.httpx, "AsyncClient", patched)
    target = RegistryTarget(repo=OLD, paths=(DIR,), project_id=None)
    entries = [e async for e in github_scanner.scan_github(AuthConfig(), [target])]
    assert entries, "renamed repo scanned as empty — redirect not followed"
    assert all(e.repo == OLD for e in entries)
