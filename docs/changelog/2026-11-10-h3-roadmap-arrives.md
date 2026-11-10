---
date: 2026-11-10
kind: migration
area: roadmap
prs: []
adrs: []
memory: [decision-tapestry-accepts-h3-h4-sequenced-2026-11-09, decision-module-homes-and-operator-answers-2026-11-10]
supersedes: null
---

# H3: the fleet roadmap arrives in hcs-coordination

**What:** lens-core's roadmap (hand-off H3, lens-core `docs/plans/2026-11-09-lens-core-handoffs.md`)
now lives in a self-contained `roadmap/` folder. It is separate from tapestry's older root
`ROADMAP.md`, which this does not replace. The folder holds:
- `roadmap.yaml`, the data: 35 items;
- `ROADMAP.md`, generated from it;
- `roadmap.py`, the checker;
- `tests/`, with 17 tests;
- `.github/workflows/roadmap.yml`, the CI.

Only the roadmap-check step of lens-core's `roadmap.yml` moved. Its spine and launcher tests go to
QuickPrime with H1 and H2.

**Adapted, not just copied:**
- **The checker reads the whole-system module list from a path.** It now lives in
  hcs-decomposition (H6), not beside the roadmap. The source is `--whole`, then a local
  `decomposition.json`, then `ROADMAP_WHOLE`. CI checks out `Lizo-RoadTown/hcs-decomposition`, using
  the new repo name rather than relying on a redirect.
- **13 items re-owned to the six modules.** Eight were owned by modules that no longer exist
  (access + tenancy, lens-ingest, lens-review, lens-serve, lens-observe, workflow oversight). Five
  were open lens-core items that belong elsewhere. Each change carries a `note` citing its decision.
  Eight became `superseded`: the four sibling `*-derives-plan` items, both module-repo items, the
  oversight-home question (H5) and the one-candidate-flow hypothesis. Every module now owns at least
  one item, which the checker requires (`roadmap.py:118`).

**Verified:**
- `check` against hcs-decomposition's live `decomposition.json` passes (all 35 items valid, every
  module covered, ids valid).
- 17 tests pass with the whole; 16 pass and 1 is skipped without it.

**Still needed:** the `FLEET_READ_TOKEN` repo secret (operator), so CI can read the private
hcs-decomposition. Until then the workflow fails with a clear message. Per the hand-off conditions,
lens-core drops its copy only after CI passes here.
