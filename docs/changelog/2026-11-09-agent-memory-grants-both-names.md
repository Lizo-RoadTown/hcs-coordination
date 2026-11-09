---
date: 2026-11-09
kind: fix
area: integrations/claude-code/tapestry-patterns
prs: []
adrs: []
memory: []
supersedes: null
---

# Agents request memory tools under both registration names (patterns 0.1.10)

**What:** `drift-watcher`, `lessons-learned`, `next-actions-planning` and
`orchestration-cataloging` now grant each loom-memory tool under BOTH names it can
have: `mcp__loom-memory__memory_*` and `mcp__plugin_tapestry-discipline_loom-memory__memory_*`.

**Why:** the tool's name depends on how a session registered the server. A repo whose
own `.mcp.json` declares `loom-memory` (tapestry does) exposes `mcp__loom-memory__*`.
A session relying on the discipline plugin's registration exposes the `plugin_…`
name. Each agent granted only one name, so each was silently mute in the other kind of
session. #185 switched `drift-watcher` from the first name to the second. That fixed
it on Poppytart and broke it on MINIPC-T9CJY. On 2026-11-09 the drift watcher reviewed
C1 with no memory tools and could only hand its four findings back in text. The other
three agents had the mirror-image gap.

A grant for a tool that is absent in a session is ignored, so granting both names is
safe everywhere.

**Consumers act on:** both machines `catch-up-machine.ps1` + restart after merge.
