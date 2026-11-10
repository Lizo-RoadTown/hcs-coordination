# Tapestry migration map against the settled homes (2026-11-10)

**Status:** map for operator review. Every move listed needs the operator's approval before it
happens; this document only prepares them.
**Governing decision:** loom memory `decision-module-homes-and-operator-answers-2026-11-10`. The
architecture is settled; Tapestry is "Core, where all the coordination happens… deals with agents
and orchestration".

## Tapestry's role

Coordination and execution:
- connecting components;
- equipping agents (plugins, CLI, project registry);
- scheduling;
- the platform-change gate (registry and policy);
- carrying approved changes through validation and installation (the executor).

Telemetry ingestion stays here; other modules read it over HTTP.

## Every component in this repo, by destination

**Stays in Tapestry**

| Component | Live state (2026-11-10) | Work before it is done |
|---|---|---|
| `services/project-registry` | live from tapestry (dormant 2026-06-25 deploy) | `tapestry onboard --token` documented before any redeploy (anonymous onboard would 401) |
| `services/telemetry-ingestion` | live from tapestry; B1 exit check passed 2026-11-10 | none |
| `services/architecture-registry` | **live from the-loom**; tapestry copy undeployed | cut over (repoint) to tapestry; make the gate act only on approved decisions (remove auto-dispatch, `main.py:234-249`) |
| `services/policy` | **live from the-loom**; tapestry copy undeployed | cut over; approver from the token, not the body (`models.py:65`) |
| `services/skill-making`, `engine/skill-compiler` | undeployed here; Make_Skills runs the live compile end | become part of the executor (`docs/proposals/2026-11-09-executor-design.md`) |
| `services/audit-log`, `services/candidate-registry` | README-only slots | audit-log becomes the executor's append-only chain (safety gate item 4); candidate-registry stays absorbed into architecture-registry (ADR-0001) |
| `services/docs-mcp` | code present | stays (distribution of docs to agents) |
| `packages/cli`, `packages/sdk`, `packages/schemas`, `packages/shared-types` | CLI on PyPI | keep |
| `integrations/claude-code/tapestry-discipline`, `tapestry-patterns` | marketplace `tapestry` | keep; the lizo-skills marketplace joins as distribution, and the-loom's `lizo-loom` marketplace retires into tapestry-discipline |
| the executor | proposed (#203) | E1 starts after approval |

**Arrives in Tapestry**

| Component | From | Condition |
|---|---|---|
| the roadmap, its checker and its test step (H3) | lens-core | after Surveyor takes the module list (H6); only the roadmap-check step of lens-core's `roadmap.yml` moves |

**Leaves Tapestry**

| Component | To | Live state | Move mechanics |
|---|---|---|---|
| `services/agent-context` (memory) + 001 migration | Loom_MCP | live from tapestry @ `47332906` | P3, then P4. **Blocked by the 12-item pre-flight in Loom_MCP `docs/plans/2026-11-10-memory-safety-report.md`.** Code freeze in tapestry until then |
| `services/self-observer` | education-lab (engine) | **live from tapestry** (cron `crn-daedvggu01pc73e3r820`, 6-hourly, OBSERVER_JWT set) | same-name repoint; its env lives on the Render service and survives |
| `services/project-observatory` | education-lab (engine) | the only live instance is a `/health` stub from the-loom; the signal code here has never been deployed | first deployment happens in education-lab; tapestry's copy is source material, not a service to move |
| `engine/local-observer`, `engine/agency-to-structure`, `engine/adapters/*` | education-lab (engine) | not deployed | copy as source; adapters overlap education domain packages |
| `apps/web-dashboard` | lens-core (interface) | live, Vercel | move with the console |
| `apps/docs-site` observatory console (`src/pages/observatory.astro`) | lens-core (interface) | live, Vercel project `tapestry` | **needs a `/observatory` redirect** from the docs site; the rest of the docs site stays |
| `apps/admin-console`, `packages/ui` | lens-core (interface), or retire | not deployed | decide at the interface move |
| `docs/architecture` observatory docs | lens-core | — | with the console |
| master-plan steps **C2** (classifier) and **C3** (console) | education-lab and lens-core | not started | owned there now; Tapestry hands over the plan rows and evidence |

## Concrete conflicts (each needs a decision before or during its move)

1. **The first closed loop now spans three homes.** The review's P3-narrow loop runs: self-observer
   drift candidate (engine), then a proposal into the gate (Tapestry), then approval in the
   dashboard (interface), then an executor PR (Tapestry), then an outcome event (to the engine),
   then a memory record (Loom_MCP). Every arrow between homes needs its P0 contract
   (proposal→gate is drafted; execution-result and settings are not). **Do not move the
   self-observer mid-loop:** run the first loop with it where it is, then repoint.
2. **Registry and policy are Tapestry's but run from the-loom.** The gate the executor depends on
   runs from a retired repo, with anonymous reads open (the-loom #34 is merged but not deployed).
   Cutover order: deploy #34 (the dashboard now carries a JWT), then repoint both services to
   tapestry, then fix the auto-dispatch and the approver-from-body defect.
3. **One shared database, many owners.** loom-postgres holds records (Loom_MCP), telemetry and
   signals (Tapestry and the engine), projects, policy and candidates. ADR-0003 says tapestry's
   series is canonical. When 001 leaves for Loom_MCP and 006 for the engine, the amendment must
   name each table's owner, and a migration must never be applied twice from two series.
4. **The runtime dependency on the-loom's env group.** Production memory gets its tenant ID from
   the-loom's `loom-shared-secrets` group, and other services may too. Every service that leaves
   or stays needs its own env pinned before the-loom's blueprint is retired, or it silently falls
   to the zeros tenant.
5. **The Vercel split.** The console and the dashboard leave, and the docs site stays. One
   `/observatory` redirect, coordinated with lens-core, keeps existing links working.
6. **The session-report hook writes into every repo.** It is a live path for personal session
   text into project repos (QuickPrime included), and it conflicts with "sharing an
   implementation never shares data". The fix is proposed: write reports to the shared space,
   never commit them. It needs operator approval.

## Recommended order of Tapestry's own work

1. Operator-gated safety items that need no move: a logical export of loom-postgres; deploying
   the-loom #34; pinning the tenant on production memory; giving staging its own credentials.
2. Registry and policy cutover to tapestry, with the gate fixes. This is Tapestry's core and
   unblocks the executor.
3. Executor E1 (intake and authority), approval-required by default.
4. Hand C2/C3 plan rows to education-lab and lens-core; accept H3 after H6.
5. Loom_MCP P3 when its pre-flight is complete.
6. Repoints out (self-observer, then the console with its redirect), after the first loop has run.
