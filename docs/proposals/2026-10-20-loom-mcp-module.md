# Proposal: Loom_MCP — the memory MCP as its own module repo

**Status:** Open — awaiting Liz's confirmation of the component redefinition and the repo name
**Authors:** Liz, agent-assisted
**Date:** 2026-10-20

## Problem

The loom-memory MCP is the one service every agent and every project in the fleet depends on. Today it
lives inside Tapestry (`services/agent-context/`), deployed as `loom-agent-context.onrender.com`.
Under the forming component redefinition (Tapestry becomes the adaptive engine, the Observer; Lens
becomes the interface; Loom memory becomes the MCP), the memory service needs its own module repo with
its own identity, per the module-identity rule: module repos keep their own identity and do not absorb
the platform's.

## Decision: a standalone module repo, equipped like a full Tapestry-managed project

Working name **Loom_MCP** (Liz's suggestion; `loom-mcp` is the kebab-case alternative if GitHub/Render
naming conventions matter; the name is Liz's call). The repo carries the service, its deploy, its
contract, and the full managed-project equipment, so its agent can work it with the same discipline as
any other repo in the fleet.

### Repo layout

```text
Loom_MCP/
  CLAUDE.md                  # module identity + operating guide (memory wiring, discipline, PROBE rules)
  AGENTS.md                  # same content for non-Claude agents
  README.md                  # what it is, the tool surface, how a repo connects (.mcp.json snippet)
  CHANGELOG.md
  service/                   # moved from tapestry/services/agent-context/
    main.py  mcp_server.py  mcp_http.py  mcp_self_host_middleware.py  auth_bridge.py  storage.py
    requirements.txt  requirements-test.txt
  tests/                     # moved with the service; CI runs them on every push
  schemas/                   # the contract, versioned:
    memory-record.md         #   record types (decision/fact/feedback/lesson/preference/project/...)
    tool-surface.md          #   memory_read/write/recall/search/list/delete semantics
  docs/
    adr/  architecture/  architecture-snapshots/  plans/  proposals/  runbooks/
    session-reports/  test-runs/
    conventions/             # LOOM_PROJECT_ID, project tags, the why-field discipline, visibility
  infra/deploy/render.yaml   # SERVICE NAME PRESERVED: loom-agent-context (same URL through the move)
  .mcp.json                  # this repo's own agent uses the hosted memory like everyone else
  .project-intelligence/     # minted via `tapestry onboard`
  .claude/settings.json      # tapestry-discipline@tapestry + tapestry-patterns@tapestry
  .env.template              # TAPESTRY_MEMORY_API_KEY, LENS/REGISTRY URLs as needed
```

### Equipment (the "all the things Tapestry has" list)

1. **Discipline plugin** (`tapestry-discipline@tapestry`): session hooks, PROBE reminders,
   architecture snapshots into `docs/architecture-snapshots/`, stop audit, upskilling reports.
2. **Patterns plugin** (`tapestry-patterns@tapestry`): the shared skills and agents by name.
3. **Loom memory wiring**: `.mcp.json` to the hosted URL; `LOOM_PROJECT_ID=loom-mcp`; its own project
   tags. The memory service's repo is also a memory consumer; that is intentional.
4. **Project intelligence**: `.project-intelligence/` with a registry-minted id.
5. **Docs skeleton** with ADRs and runbooks. First runbooks to write: deploy + rollback, key rotation,
   tenant operations, the self-host mode.
6. **Two-mode, first-class**: the self-host middleware already exists in the service
   (`mcp_self_host_middleware.py`); this repo is where `PLATFORM_MODE=self_host` vs `hosted` stops
   being forward-looking and becomes the module's documented contract.
7. **Tests + CI** from day one; the fleet depends on this service more than on any other.
8. **Versioned contract**: `schemas/` plus CHANGELOG discipline, because every consumer's agent reads
   this surface.

### Consumer requirements (from lens-core, 2026-10-20)

- The conventions doc must cover: LOOM_PROJECT_ID; project_tags usage; record types and when to use
  each; the `handoff-*` naming for cross-session notes; the rule "the file is the record, memory is
  the pointer."
- A drop-in `.mcp.json` snippet with env-reference auth (no literal tokens).
- A migration note stating the guarantee: every repo's `.mcp.json` defaults to
  `https://loom-agent-context.onrender.com/mcp/memory/` with env `TAPESTRY_MEMORY_API_KEY`; both keep
  working through the move, or the change is one line per repo and announced.
- Self-host mode documentation.
- **Known defect to fix or document:** `memory_write` content containing certain strings (URLs plus
  shell commands) was rejected by the host's WAF with a 403 page on 2026-10-20; plain prose went
  through. This is a correctness issue for an API whose consumers write technical records.

### Migration plan (consumers must feel nothing)

| Phase | Scope | Gate |
|---|---|---|
| P1 | Create repo; copy `services/agent-context/*` + tests; CI green in the new repo | Tests pass on copied code |
| P2 | Staging deploy from the new repo under a distinct name; parity checks against prod behavior | Existing runbook `docs/migration-cicd/runbooks/02-agent-context-mcp.md` governs |
| P3 | Flip the production deploy source to the new repo, **service name preserved** (`loom-agent-context`, same URL) | Every consumer `.mcp.json` untouched |
| P4 | Freeze then remove `tapestry/services/agent-context/`; Tapestry's UMBRELLA and CLAUDE.md updated | No runtime dependency on the old path |

The env name `TAPESTRY_MEMORY_API_KEY` is kept through the move; renaming it would touch every repo in
the fleet and is a separate decision for later.

## What else leaves Tapestry (inventory, being worked with lens-core)

Under Tapestry = the adaptive engine (the Observer):

- **Stays in Tapestry:** `engine/` (local-observer, skill-compiler, agency-to-structure, adapters),
  telemetry-ingestion, policy, architecture-registry — the adaptive loop itself.
- **Moves to Loom_MCP:** the memory service (this proposal). Candidate to co-locate or follow:
  `services/project-registry` (it resolves tenants, which is memory-adjacent) — open question.
- **Toward Lens (the interface):** operator-facing surfaces — `apps/docs-site`, `apps/web-dashboard`,
  the observatory UI. Pending lens-core's answer on what the Lens side claims.
- **Location open, names fixed:** the plugin marketplace must keep the name `tapestry` and the plugin
  names (`tapestry-discipline`, `tapestry-patterns`), or every consuming repo's settings break; the
  `tapestry` CLI (`onboard`) likewise keeps its name wherever it lives. Known CLI bug to fix: `onboard`
  defaults its registry URL to a placeholder.

## Two-mode notes

| Mode | What changes |
|---|---|
| Self-host | The module's own middleware serves per-operator fallback tenants; runbook documents standing it up |
| Hosted | Render service `loom-agent-context`, per-tenant auth via the auth bridge |

## Open questions

1. Repo name: `Loom_MCP` or `loom-mcp`? (Liz names things.)
2. **The Lens naming collision (raised by lens-core).** "The Lens" today names the PROVES-derived lab
   (lens-core, lens-ingest, lens-review, lens-serve, lens-observe), and none of those is an interface
   layer. If "Lens" becomes the interface component, Liz chooses: (a) the lab repos stay as they are
   and the interface is a new thing under the Lens name, (b) the lab repos are renamed, or (c) the lab
   is re-scoped into the interface. lens-core claims no new territory until she decides.
3. Does `project-registry` move with it, stay in Tapestry, or become its own module? (lens-core's
   consumer preference: the registry is about projects, not memory — keep it next to the CLI that
   registers projects, wherever `onboard` lives, not inside Loom_MCP.)
4. Do the interface surfaces (`docs-site`, `web-dashboard`, observatory UI) move to the Lens side, and
   when relative to this move? (lens-core claims none of them today; the lab keeps its own working
   screens, which are not the system's interface layer.)
5. Does the memory conventions doc become canon inside Loom_MCP (single source for LOOM_PROJECT_ID,
   tags, record types)?
6. Who owns tenant operations (key issuance, rotation) once the module is separate?

## What this implies for the next action

Create the repo with the layout above, copy the service and tests, and run P1–P2 against the existing
runbook. Nothing flips until P3 is gated and Liz confirms the component redefinition.

## Sources

- `docs/architecture/UMBRELLA.md` (services table; agent-context row)
- `docs/migration-cicd/runbooks/02-agent-context-mcp.md` (cutover discipline; service-name preservation)
- `infra/deploy/render.yaml` (staging-first block; prod name preserved)
- loom memory: `five-component-redefinition-forming-2026-10-20`,
  `five-component-split-coordination-state-2026-10-20` (the dependency contract)
- `docs/architecture/2026-10-10-system-architecture.md` (prior five-part framing, to be updated when
  Liz confirms the new definition)
