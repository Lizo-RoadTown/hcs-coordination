---
date: 2026-11-10
kind: chore
area: repo-wide
prs: []
adrs: []
memory: [decision-repo-renames-hcs-prefix-2026-11-10]
supersedes: null
---

# References updated for the rename tapestry → hcs-coordination

**What:** after the operator renamed the repo (`Lizo-RoadTown/tapestry` → `Lizo-RoadTown/hcs-coordination`),
the load-bearing references now use the new name. GitHub redirects the old one only while no new repo
takes it.
- The install command shown to users: `/plugin marketplace add Lizo-RoadTown/hcs-coordination`, in
  CLAUDE.md, AGENTS.md, README.md, and the hints the CLI prints from `tapestry init` and
  `tapestry onboard`.
- The `repository` and `homepage` links in `.claude-plugin/marketplace.json`, both plugins'
  `plugin.json` files, `packages/cli/pyproject.toml` and the CLI README.

**What did not change (deliberately):**
- The marketplace **name** stays `tapestry`, so every installed plugin ID (`tapestry-discipline@tapestry`,
  `tapestry-patterns@tapestry`) and every consuming repo's `enabledPlugins` keeps working.
- `LOOM_PROJECT_ID=tapestry`, memory project tags, Surveyor's module key `tapestry` (pr-012), and the
  local folder name keep the old names, per the rename decision.
- Artifact refs keep the name they were captured under (see `2026-11-10-self-observer-follows-repo-renames.md`).
- About 40 historical docs keep the old name in their narrative.

**Also corrected (raised by a drift check):** CORE DIRECTIVE 1 in CLAUDE.md and AGENTS.md said "no JWT
header is needed". Production memory requires the key, and anonymous requests return 401.
