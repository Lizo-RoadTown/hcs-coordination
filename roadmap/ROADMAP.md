# Roadmap

<!-- generated from roadmap.yaml by roadmap/roadmap.py; edit roadmap.yaml, not this file -->

One roadmap for the six modules. Only **firm** items are built; **loose** and **hypothesis**
items name the fact that decides them. Owners are checked against the whole-system module
list in hcs-decomposition. Method: hcs-observatory `docs/plans/2026-10-21-roadmap-method-proposal.md`.

## Now

| id | item | outcome | owner | firmness | status | depends on | exit check / decides it |
|---|---|---|---|---|---|---|---|
| rotate-proves-key | Rotate the committed PROVES service_role key | The key committed in PROVES_LIBRARY scripts no longer authenticates. | operator | firm | proposed |  | human: Supabase shows the old service_role key revoked |

## Next

| id | item | outcome | owner | firmness | status | depends on | exit check / decides it |
|---|---|---|---|---|---|---|---|
| observe-signal-vocabulary | One signal package, lens-observe as its program-layer instance | lens-observe instantiates the shared scale-neutral signal package (tapestry pl-001) instead of building a second classifier. | education-lab | loose | proposed |  | decide when: tapestry proposes the pl-001 package; evaluate it against the spine (direction set in tapestry docs/plans/2026-10-21-master-plan-personal-loop.md section F) |
| tenancy-home | One home for tenancy | Tenancy is owned once (access + tenancy, Loom_MCP or project-registry). | operator | loose | proposed |  | decide when: Tapestry's breakdown names the Loom_MCP and registry homes |
| teaching-material-handling | Decide which teaching material comes into Surveyor, and in what form | Surveyor's running records hold what agents are taught, without proprietary material in public. | operator | loose | proposed |  | decide when: the operator rules on FRAMES/IAKM and copy vs summary vs pointer |

## Later

| id | item | outcome | owner | firmness | status | depends on | exit check / decides it |
|---|---|---|---|---|---|---|---|
| scope-boundary-enforcement | Enforce the personal and project boundary (policies, crossings, public projects) | Row policies use scope_id; crossing between scopes is authorized and recorded; a public project is kept apart from its owner's personal data. | Loom_MCP | loose | proposed | spine-scope-column | decide when: the operator settles the owner rule for public projects, and the tenancy-home decision names where scope ids live |
| name-proposed-repos | Final names for the two proposed repos | workflow oversight and access + tenancy get their final names once the whole decomposition is reconciled. | operator | loose | proposed |  | decide when: the full agreed decomposition is reconciled (tapestry prototype-reconstruction-procedure v0.1, step 8); stable IDs and descriptive labels until then |
| compose-lab | One command stands up a whole lab | The launcher composes every module against one injected database. | tapestry | firm | proposed | launcher-applies-spine | end-to-end smoke test on a shared test database |
| docs-sites | Docs agent and docs-site skeleton in every Lens repo | Each repo documents itself from a shared skeleton. | tapestry | firm | proposed |  | each repo builds its docs site skeleton |
| personal-observatory-reuse | Personal observatories built from Lens elements | Tapestry and Loom memory reuse published Lens modules, never a runtime dependency. | tapestry | hypothesis | proposed |  | decide when: Tapestry names which Lens elements it needs |
| project-observatory-feeds-shared-graph | A project observatory can contribute to the shared knowledge graph (QuickPrime) | What a Lens project observatory chooses to share reaches QuickPrime's graph through QuickPrime's contract, and nothing private crosses. | QuickPrime | loose | proposed |  | decide when: QuickPrime's research proposes its hook-in contract (which telemetry, how it arrives, how it is checked) |

## Done

| id | item | owner | status | evidence |
|---|---|---|---|---|
| approve-observatories | Approve the observatories architecture and roadmap method | lens-core | done | lens-core a881723 |
| siblings-under-lens-log | Put the four sibling repos under lens-log | lens-core | done | lens-ingest 4f44a63, lens-review 98969f7, lens-serve 7019d56, lens-observe e3f5ccd |
| lens-log-silent-loss-fixes | Fix lens-log M6, M7, M8 | surveyor | done | surveyor a984e18 |
| module-map-check | Module-map change needs an evaluation (lens-log D11) | surveyor | done | surveyor a5910e3, lens-core 4ee947b |
| roadmap-as-data | Roadmap as data with checks | lens-core | done | lens-core 79f1010 |
| install-lens-log-everywhere | Install lens-log 0.1.5 for every repo (user scope) | operator | done | user-scope install 2026-11-07, 0.1.5; stale project rows (lens-core 0.1.5, education-lab 0.1.4, surveyor 0.1.2) removed; backup installed_plugins.json.bak-2026-11-07-lens-log-global |
| log-index-action | Log-index GitHub Action | lens-core | done | lens-core 49e43dd, log-index run 39726154238 green; bot rebuilt INDEX.md in 3664af3, consistency failure covered by tests/test_log_index.py |
| roadmap-check-in-ci | Run the roadmap check in CI | lens-core | done | lens-core 10a8896, CI run 39609823937 passed on main, CI run 39609904466 failed on a deliberately broken roadmap (PR 1, closed) |
| lens-log-remaining-defects | Fix lens-log M1, M3, M4, M5 | surveyor | done | surveyor 5d1e804, 92 tests pass, lizo-skills marketplace 2a7036a |
| spine-neutral-names | Neutral table names in the spine | lens-core | done | lens-core fd1bf6b, tests/test_spine.py::test_no_reference_system_names_in_the_standard |
| spine-one-table-choices | Apply the five approved one-table choices | lens-core | done | lens-core fd1bf6b, tests/test_spine.py::test_one_table_per_kind_of_data and DB tests, CI run 42440690022 (30 passed, none skipped) |
| spine-scope-column | Scope column on every spine table (standard 0.2.0) | lens-core | done | lens-core b74ddb8, CI: 57 passed (7 scope DB tests); installed wheel reports standard 0.2.0 |
| oversight-tables-home | Decide whether the oversight tables stay in the spine | education-lab | superseded |  |
| review-promotion-contract | Review and promotion contract | lens-core | done | lens-core 6f45c72, contract tests in tests/test_spine.py; CI run 42453137049 (38 passed, none skipped) |
| spine-security-defaults | No anonymous grants; remove the source_id trigger bug | lens-core | done | lens-core 1658ab2, tests/test_spine.py::test_hosted_roles_and_strangers_get_nothing, CI run 42440991778 (32 passed) |
| launcher-applies-spine | Launcher applies the spine | lens-core | done | lens-core cf7485b, lens-core 6fa0566, CI run 42453587108: 47 passed; installed wheel printed lens-core 0.0.1 (standard 0.1.0) |
| ingest-derives-plan | lens-ingest works its source and records its own plan | QuickPrime | superseded |  |
| review-derives-plan | lens-review works its source and records its own plan | QuickPrime | superseded |  |
| serve-derives-plan | lens-serve works its source and records its own plan | lens-core | superseded |  |
| observe-derives-plan | lens-observe works its source and records its own plan | education-lab | superseded |  |
| program-layer-ids | Stable pr- component IDs for the program layer | lens-core | done | lens-core decomposition.json ids (pr-001 to pr-007), enforced by scripts/roadmap.py check_ids |
| access-tenancy-repo | Access + tenancy module | Loom_MCP | superseded |  |
| workflow-oversight-repo | Workflow oversight module (pluggable slot) | education-lab | superseded |  |
| lens-meaning | Settle what "Lens" means across the system | operator | done | loom memory decision-lens-is-the-observatory-memory-is-the-database-2026-11-09: the Lens is the observatory (interface layer + adaptive agents that observe Memory and fix projects by rules); Memory is the database |
| candidate-flow-one-pattern | One candidate -> decision flow | tapestry | superseded |  |
