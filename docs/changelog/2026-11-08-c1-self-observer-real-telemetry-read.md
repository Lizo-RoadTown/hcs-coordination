---
date: 2026-11-08
kind: feature
area: services/self-observer
prs: []
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

**Live verification:** the client ran against production — authenticated,
never-seen artifact → `None` (correct suppression).

**Reality-first finding from that run:** the store holds 283 events and ALL
carry `artifact_ref=''` — the artifact-identity gap is now measured in
production, not predicted. Until B1 (skill attribution) stamps refs onto hook
events, every per-artifact read legitimately answers "never seen". The
unresolved events stay visible (adoption requirement 1); nothing is dropped.
Bonus evidence: 158 of those were the backfill — ~125 arrived LIVE since the
cutover, so the hook emitter (wire X1) is confirmed working unattended.

**Next on the M1 path:** B1 (artifact identity in capture) — now the measured
bottleneck, not just the planned one.
