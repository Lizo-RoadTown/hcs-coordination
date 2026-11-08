---
date: 2026-11-08
kind: chore
area: .github/workflows
prs: []
adrs: []
memory: [audit-check-layers-fleet-2026-11-08]
supersedes: null
---

# CI hardening: cli + plugin test legs, tests-before-publish, frontmatter guard

**What** (check-layers audit pipeline steps 2 and 4):

- `tests.yml` gains two matrix legs: **cli** (`packages/cli/tests`, 33 tests — previously ran
  nowhere) and **discipline-plugin** (`integrations/claude-code/tapestry-discipline/tests`,
  123 tests — green as of discipline 0.1.24). The install step now handles
  pyproject-only and no-deps packages.
- `publish-cli.yml` runs the cli test suite **before** building and publishing to PyPI —
  it used to publish untested.
- New `docs-frontmatter-check.yml` + `scripts/check_docs_frontmatter.py`: YAML-parses the
  frontmatter of all docs-site content pages (38 today). Catches in CI the exact failure
  class that broke every Vercel deploy for six PRs (unquoted `: ` in a description).
  Verified green on the real tree and red on a reproduction of the incident.
- `catch-up-machine.ps1` now activates `core.hooksPath=.githooks` in the clone it runs
  from — the ADR-0010 git-hook layer was built but inactive in tapestry's own clones.

**Deliberately deferred** (from the audit, awaiting operator decisions):
lint/type-check leg (needs a ruff/tsc config pass first — an unconfigured advisory lint job
would be permanently red, which is the noise this cleanup removes); branch protection
(operator, Settings → Branches — the audit's single highest-value step); secret scanning +
Dependabot (operator toggles); changelog-format validation.
