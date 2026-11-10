---
type: decision
module: tapestry
surfaces: [definition]
date: 2026-11-10T02:24
source_commits: {}
---

# Tapestry adopts a lens-log piece file with narrow surfaces

## What was done
Added `decomposition.json` at the repo root as a lens-log **piece** (`role: piece`,
`module: tapestry`). This answers Surveyor's hand-off after H6 landed (surveyor ff642af, operator
approved; loom memory `handoff-piece-files-to-module-owners-2026-11-10`). The whole-system file
in Surveyor lists `tapestry` (pr-012). The log index (H4, now Surveyor's) reports any listed
module without a piece file as a problem.

Two surfaces, both `on: write`, both `entry: decision`:
- **identity:** `CLAUDE.md`, `AGENTS.md`, `MANIFESTO.md`, `docs/CORE_DIRECTIVES.md`;
- **definition:** `decomposition.json`, `docs/adr/**`, `docs/architecture/UMBRELLA.md`.

No `sources`: tapestry reads no source repo the whole declares.

## What was found / decided
- **Kept the surfaces narrow on purpose.** lens-log is enabled globally on this machine, and its
  Stop hook blocks the turn when a declared surface changes without an entry
  (`surveyor/plugins/lens-log/scripts/stop_check.py:128-135`). Wide surfaces would put every
  tapestry commit under a second logging rule.
- **Only Tapestry's identity and its formal decisions are covered.** Changes there deserve a
  logged decision anyway. Everything else keeps tapestry's existing change trail
  (`docs/changelog/`, enforced by `changelog-check.yml`). The two do not overlap.
- `docs/proposals/` and `docs/plans/` stay off the surfaces. They are working documents that
  change often, and their decisions land in ADRs or memory records, which are covered.
- The shape follows QuickPrime's and education-lab's piece files (identity and definition as
  decision surfaces) and passes lens-log's loader rules (`definition.py:90-106`): a name, `on`
  in TRIGGERS, `entry` in ENTRY_TYPES, and non-empty paths.

## Lessons
A piece file is not inert configuration. Wherever lens-log is enabled, declaring a surface
changes how every session in that repo has to work. Choose surfaces as a working-practice
decision, not as a coverage exercise.
