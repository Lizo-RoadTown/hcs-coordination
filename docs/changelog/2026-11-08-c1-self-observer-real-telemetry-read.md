---
date: 2026-11-08
kind: feature
area: services/self-observer
prs: [199]
adrs: []
memory: [milestone-telemetry-cutover-live-2026-11-08, adopted-personal-loop-build-sequence-2026-10-21]
supersedes: null
---

# C1 — self-observer reads real telemetry (wire X4 closed)

**What:** `services/self-observer/telemetry_client.py` no longer returns `None`
unconditionally. `invocations_30d` now performs an authenticated
`GET /telemetry/invocations` against the live read API (cut over 2026-11-08),
mirroring its 0-vs-None existence contract exactly: never-seen → `None`
(suppress), known-but-0 → `0` (orphan territory), active → count. Bearer =
`OBSERVER_JWT` (same pattern as `candidate_client.py:84`; the production cron
got its token today). Fail-soft throughout — transport error, 401, 5xx,
non-JSON, non-numeric all degrade to `None`, because this runs inside the
6-hourly production cron and must never crash it. `main.py` now passes auth to
the client. 11 new tests pin the contract; suite 85 passed.

**Live verification (raw, so success is distinguishable from failure):** a
never-seen `None` would look identical to a rejected token, so the raw responses are
recorded: with the read key, `GET /telemetry/invocations?repo=Lizo-RoadTown/tapestry&file_path=.claude/skills/never-existed/SKILL.md`
→ **HTTP 200** `{"invocations":null,"known":false}`; without it → **HTTP 401**
`{"detail":"Authorization required"}`. Note for C2/C3: inside `signal_rules` a 401,
a 5xx and a never-seen all still arrive as `None` — telling processing failure from
missing instrumentation (procedure step 6) is C2/C3's to close, e.g. by passing
`known`/a reason through instead of discarding it.

**Base URL (the plan row's second half):** `config.py:152-155` keeps its default
`https://loom-telemetry-ingestion.onrender.com`. That is now correct as-is — the A4
repoint preserved the service name and URL while switching its build to this repo, so
no retarget is needed.

**Reality-first finding from that run:** the store holds 394 events (re-measured
2026-11-09 under the tenant's row-level security) and ALL have `artifact_ref`
NULL — the artifact-identity gap is now measured in
production, not predicted. Until B1 (skill attribution) stamps refs onto hook
events, every per-artifact read legitimately answers "never seen". The
unresolved events stay visible (adoption requirement 1); nothing is dropped.
Bonus evidence: 158 of those were the backfill; the rest arrived LIVE since the
cutover, so the hook emitter (wire X1) works unattended. Sharper still: the only tools
recorded are Bash, Write, Edit and apply_patch — **no Skill invocation has ever been
captured**, because the PreToolUse matcher does not include the Skill tool. B1 must
start capturing skill invocations, not only stamp a field on them.

**Next on the M1 path:** B1 (artifact identity in capture) — now the measured
bottleneck, not just the planned one.
