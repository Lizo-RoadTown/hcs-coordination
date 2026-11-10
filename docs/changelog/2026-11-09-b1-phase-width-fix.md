---
date: 2026-11-09
kind: fix
area: integrations/claude-code/tapestry-discipline, services/telemetry-ingestion
prs: []
adrs: []
memory: []
supersedes: null
---

# B1 phase width: skill events fit 005, and the receiver enforces column widths (discipline 0.1.27)

**What happened:** B1 (#202) emitted skill events with `phase: "skill_invocation"` (16
characters). `telemetry_events.phase` is `VARCHAR(8)` (`infra/migrations/005_init_telemetry.sql:84`).
After deploying #202, a live smoke test POSTed one resolved and one unresolved skill event to
production `/hook-events`. The service returned HTTP 500 with Postgres
`StringDataRightTruncation: value too long for type character varying(8)`. One over-long
value aborts the **whole batch**. The unit tests never touched a database, so they could not
see it. The live smoke after deploy did.

**Fix:**
- The plugin emits `phase: "skill"`.
- The receiver now enforces 005's widths for every text column in `_entry_to_row`. An
  over-long value is kept in `attrs` as `<column>_raw`. The column is left out, or for the two
  `NOT NULL DEFAULT ''` columns set to `''`. So no emitter, current or future, can fail a batch
  by sending one oversized field.

**Tests:** receiver suite 23 passed (4 new width tests); discipline suite 132 passed.

**Lesson:** unit tests that mock the database cannot see schema constraints. A live smoke test
against the real store after every deploy that changes what gets written is the check that
catches this class of bug.
