"""B1 (pl-005) receiver side: hook entries carrying skill attribution map onto
the typed artifact_ref column, and unresolved invocations stay visible.

Pins:
- a resolved `tapestry.artifact_ref` (005 shape `repo#path` or `skill/<id>`)
  lands in the artifact_ref COLUMN and is not duplicated into attrs
- an unresolved invocation has NO artifact_ref (column absent -> NULL, so the
  read API and classifiers never score it) but keeps
  tapestry.artifact_resolution="unresolved" + the raw skill name in attrs
- a malformed ref is never written to the column (it would be scored as a
  real artifact); it is preserved in attrs as tapestry.artifact_ref_raw
- GET /telemetry/signals reports skill_invocations.{resolved,unresolved}
"""
from __future__ import annotations

import hook_event_handler as heh

from .conftest import TEST_READ_KEY

TENANT = "1d8ec1b3-d62a-5fab-9a52-eb6a3e09f1c8"
REF = ("Lizo-RoadTown/tapestry#integrations/claude-code/"
       "tapestry-patterns/skills/project-launch/SKILL.md")


def _entry(**extra):
    base = {
        "ts": "2026-11-09T10:00:00+00:00",
        "hook": "PreToolUse",
        "phase": "skill_invocation",
        "tool_name": "Skill",
        "session_id": "s1",
        "project_id": "tapestry",
    }
    base.update(extra)
    return base


def test_resolved_ref_lands_in_column_not_attrs():
    row = heh._entry_to_row(_entry(**{
        "tapestry.artifact_ref": REF,
        "tapestry.artifact_resolution": "resolved",
        "tapestry.skill_name": "tapestry-patterns:project-launch",
    }), TENANT)
    assert row["artifact_ref"] == REF
    assert "tapestry.artifact_ref" not in row["attrs"]
    assert row["attrs"]["tapestry.artifact_resolution"] == "resolved"
    assert row["event_kind"] == "tool"


def test_skill_uuid_shape_accepted():
    row = heh._entry_to_row(_entry(**{
        "tapestry.artifact_ref": "skill/401f4ab6-119b-4ad1-abfb-141e7339213c",
    }), TENANT)
    assert row["artifact_ref"] == "skill/401f4ab6-119b-4ad1-abfb-141e7339213c"


def test_unresolved_has_no_ref_but_stays_visible():
    row = heh._entry_to_row(_entry(**{
        "tapestry.artifact_resolution": "unresolved",
        "tapestry.skill_name": "superpowers:brainstorming",
    }), TENANT)
    assert "artifact_ref" not in row  # -> NULL: never per-artifact scored
    assert row["attrs"]["tapestry.artifact_resolution"] == "unresolved"
    assert row["attrs"]["tapestry.skill_name"] == "superpowers:brainstorming"


def test_malformed_ref_never_reaches_column():
    row = heh._entry_to_row(_entry(**{
        "tapestry.artifact_ref": "just-a-name-no-shape",
    }), TENANT)
    assert "artifact_ref" not in row
    assert row["attrs"]["tapestry.artifact_ref_raw"] == "just-a-name-no-shape"


def test_overlong_ref_never_reaches_column():
    long_ref = "o/r#" + "x" * 600
    row = heh._entry_to_row(_entry(**{"tapestry.artifact_ref": long_ref}), TENANT)
    assert "artifact_ref" not in row
    assert row["attrs"]["tapestry.artifact_ref_raw"] == long_ref


def test_entries_without_attribution_unchanged():
    row = heh._entry_to_row(_entry(tool_name="Bash", phase="end"), TENANT)
    assert "artifact_ref" not in row
    assert "tapestry.artifact_resolution" not in row["attrs"]


def test_signals_reports_skill_invocation_counts(client, fake_db):
    fake_db.script(
        {"total": 10, "friction": 0, "memory_miss": 0, "errors": 0,
         "upskill_candidates": 0, "corrections": 0,
         "skill_invocations_resolved": 3, "skill_invocations_unresolved": 2},
        [],  # coordination-state rows
    )
    r = client.get("/telemetry/signals",
                   headers={"Authorization": f"Bearer {TEST_READ_KEY}"})
    assert r.status_code == 200
    assert r.json()["skill_invocations"] == {"resolved": 3, "unresolved": 2}
