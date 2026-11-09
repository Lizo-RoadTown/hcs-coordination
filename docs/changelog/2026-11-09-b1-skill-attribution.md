---
date: 2026-11-09
kind: feature
area: integrations/claude-code/tapestry-discipline, services/telemetry-ingestion
prs: []
adrs: []
memory: [drift-watch-and-scope-audit-2026-11-09, adoption-requirements-personal-loop-2026-10-21]
supersedes: null
---

# B1 — skill invocations captured with a stable artifact_ref (discipline 0.1.26)

**What:** component pl-005, M1 critical path step B1 (moved to the head of the path by
the 2026-11-09 scope audit, after C1 measured all 394 stored events with
`artifact_ref` NULL).

**Plugin (discipline 0.1.26):**
- **Capture.** `Skill` is added to the PreToolUse matcher. Before this, no skill
  invocation had ever been recorded; the only tools in the store were Bash, Write,
  Edit and apply_patch.
- **Resolve** (`scripts/skill_attribution.py`, no repo names hardcoded):
  `plugin:skill` resolves through Claude Code's own metadata (installed_plugins.json →
  known_marketplaces.json → the clone's marketplace.json source path) to
  `owner/repo#<source>/skills/<skill>/SKILL.md`, confirmed against the local clone. A
  bare `skill` resolves to the current repo's `.claude/skills/` or `skills/` via the git
  remote, and only if the file is **tracked**: the self-observer scans GitHub, so an
  untracked skill could never be joined. Both forms are exactly the `repo#path` the
  self-observer queries (`self-observer/config.py:56-60,99-105` →
  `read_api.py:71-90`). Live check: `tapestry-patterns:project-launch` →
  `Lizo-RoadTown/tapestry#integrations/claude-code/tapestry-patterns/skills/project-launch/SKILL.md`.
- **Unresolved stays visible.** Anything that cannot be resolved (external-source
  plugins such as superpowers, unknown names, untracked skills) carries no ref, plus
  `tapestry.artifact_resolution: "unresolved"` and the raw `tapestry.skill_name`. It is
  never dropped and never given a fake ref (adoption requirement 1).
- `log_event` gains an additive `attrs` parameter. It never overrides core keys.
- The resolver loads by absolute path, like `_observability` (the v0.1.4 launcher
  lesson), and every failure degrades to unresolved rather than breaking the hook.

**Receiver (telemetry-ingestion):**
- `hook_event_handler._entry_to_row` maps `tapestry.artifact_ref` into the typed
  `artifact_ref` column. It accepts only the two 005 shapes (`repo#path`, `skill/<id>`,
  ≤512 chars). Anything else is preserved in attrs as `tapestry.artifact_ref_raw` and is
  never scored as a real artifact. Without this half, an emitter-only change would have
  landed NULL and failed quietly.
- `GET /telemetry/signals` now reports `skill_invocations: {resolved, unresolved}`.
  This is the exit-proof read for "an unresolved event visible as unresolved".
- **Pre-existing bug fixed:** `/telemetry/signals` returned HTTP 500 on every call in
  production. Its SQL goes through `str.format()`, which read the JSON literals'
  braces as placeholders. The route had only ever been tested on its 401 path. The
  braces are now escaped, and the new 200-path test caught it.

**Tests:** discipline suite 132 passed (9 new resolver tests: plugin, project, tracked
vs untracked, external source, missing metadata). Receiver suite 19 passed (7 new:
column mapping, both 005 shapes, unresolved visibility, malformed and overlong refs,
signals counts).

**To make it live (exit check):**
1. Merge.
2. Redeploy `loom-telemetry-ingestion` (autoDeploy is off).
3. Catch up and restart both machines for discipline 0.1.26.
4. Invoke one tapestry-patterns skill and one unresolvable skill.
5. Verify: `/telemetry/invocations?artifact_ref=<ref>` returns `known: true`, and
   `/telemetry/signals` shows `unresolved ≥ 1`.

**Next on the M1 path:** C2 — one classifier against production, which can now link a
finding through `artifact_ref`. Carry-forward from the drift watcher: C2/C3 must stop
collapsing "processing failure" and "never seen" into the same `None`.
