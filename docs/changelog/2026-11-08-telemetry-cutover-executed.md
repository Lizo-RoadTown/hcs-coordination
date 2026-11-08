---
date: 2026-11-08
kind: migration
area: services/telemetry-ingestion
prs: []
adrs: []
memory: [coord-minipc-a2-a3-protection-2026-11-08, decision-telemetry-deployment-all-recommended-2026-10-21]
supersedes: null
---

# Telemetry cutover executed — the receiver persists, reads are authenticated

**What:** Runbook 05 (A2–A5) executed end to end on 2026-11-08. The
`loom-telemetry-ingestion` Render service now builds from THIS repo
(`services/telemetry-ingestion`), same name and URL, per the agent-context cutover
pattern. The gated block in `infra/deploy/render.yaml` is uncommented and is the live
definition.

- **A2:** migrations 005 + 006 applied to live loom-postgres (`APPLIED.md` rows, PR #195);
  `telemetry_events`, `telemetry_rollup_daily`, `observation_signals` verified with RLS.
- **A3:** env provisioned via Render API — `SELF_HOST_TENANT_ID`, minted
  `LOOM_HOOK_BRIDGE_SECRET` + `TAPESTRY_TELEMETRY_READ_KEY`, `LOOM_JWT_PUBLIC_KEY` copied;
  `LOOM_DB_URL` verified already the live internal string; `LOOM_SKILL_BRIDGE_SECRET`
  pre-existing.
- **A4:** the-loom PR #33 merged (one-blueprint invariant), then the service repo PATCHed
  the-loom → tapestry via API (gotcha: the PATCH must carry `branch` with `repo`).
- **A5 smoke:** `/health` 200; unauthenticated read **401**; authenticated read 200;
  **158 backlogged hook events replayed via `flush_hooks_jsonl` — all accepted** and
  queryable through `/telemetry/counts` (108 hook + 14 tool in-window, project
  attribution live for slug-carrying events).

**Wires closed (fleet-reality-map §4):** X1 — `LOOM_INGEST_ENDPOINT` now set (full
`/hook-events` URL — note: the variable takes the FULL route URL, not the host);
X2 — the live receiver persists instead of discarding. Still open: X3 (classifiers
staging-gated → C2), X4 (self-observer telemetry stub → C1).

**Client wiring:** this machine's `tapestry/.env` carries endpoint + hook secret + read
key; Poppytart's copy is staged in the shared space
(`tapestry/TELEMETRY-CLIENT-ENV-2026-11-08.env`). Remaining repos get the lines as
sessions touch them (or via one sweep on request).

**Rollback:** re-point the service repo back to the-loom (one dashboard/API action; the
shared DB is untouched).
