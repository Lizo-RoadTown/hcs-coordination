# Check-layers audit: what actually guards the fleet (2026-11-08)

Two read-only audits, run in parallel: one deep on tapestry's check layers, one across 21
fleet repos. This report is the synthesis. Evidence citations are in the per-audit findings;
the loudest facts come first.

## The three loudest findings

1. **A live credential sits in a public repo.** `claude-skills-marketplace` (PUBLIC) tracks
   `.env` containing a Grafana Cloud OTLP auth header. Containment is committed locally
   (untracked + gitignored, commit `3eceadd`, push operator-gated). Still required, operator
   only: **rotate the Grafana Cloud token** and scrub the repo history. Until rotation, the
   token in history is usable by anyone.
2. **Nothing anywhere is a required check.** Tapestry's main branch has no protection and no
   rulesets (`gh api .../branches/main/protection` → 404). Every green/red check is advisory;
   any red can be merged past — and was, for two months of dead review jobs. The same is true
   fleet-wide (only `lens-core` and `Loom_MCP` even run tests in CI).
3. **The CLI publishes to PyPI untested.** `publish-cli.yml` builds and publishes
   `packages/cli` with no test step, and `packages/cli/tests` (including the private-files
   guard tests) is absent from `tests.yml`'s matrix.

## Tapestry: the four layers as they actually run

| Layer | Exists | Reality |
|---|---|---|
| CI (GitHub Actions) | 5 workflows (6th retiring in PR #192) | All advisory — no branch protection. tests.yml runs 7 service suites (agent-context non-blocking) but misses `packages/cli` and the discipline plugin's ~1,870 lines of hook tests. **No linter, no type-checker, no frontmatter check, no secret scanner, no dependency audit, anywhere.** |
| Git hooks (pre-commit) | `.githooks/` + `check_private_committed.py` | **Not active in tapestry's own clone** (`core.hooksPath` unset — it's set per-clone by `tapestry init`, and tapestry itself never ran it). Fails open if no Python is found. Scans only `.shared`/`.tapestry-shared.local`, nothing else. |
| Agent hooks (discipline plugin) | 4 hooks, never block | Working: session snapshot + recall + not-onboarded warning; PROBE reminders; creation-command PROBE; stop audit. **Broken: the runtime-citation check can never fire in tapestry** — `pre_tool_use.py:109` still lists Make_Skills paths (`platform/`, `web/`); tapestry's runtime is `services/`, `apps/`, `packages/`. |
| Advisory review (Copilot, PR #192) | instructions written | Both the old Claude prompt and the new Copilot instructions tell the reviewer to "leave lint/type issues to CI" — **and no such CI exists**, so lint/type issues are currently nobody's job. (Instructions amended in #192 to stop claiming checks are "required.") |

Also found: `audit_concrete_rules.py` is an orphaned check (wired to nothing);
`docs/migration-cicd/` prescribes six hard-block workflows plus verifiers
(drift-catcher, parity, static checks) — none were ever built; the changelog format
(`docs/changelog/README.md:31-50`) is specified but never validated.

## Fleet: repo types and what each actually has

**Class/teaching repos (11):** che2301, che2301-walkthroughs, ime2390, ime3261, mte2070,
mfe2010, mfe2010l, che2301l, fall-2026-hub, organometallics-bootcamp, education-lab.
- 7 have the ADR-0010 private-files guard (CI + hook); **mfe2010, mfe2010l, che2301l,
  education-lab do not** — and mfe2010's `core.hooksPath` points at a `.githooks/` directory
  that doesn't exist, so no hooks run there at all.
- **No class repo enables tapestry-discipline/tapestry-patterns** — they run the
  education-lab plugin set (learning-core, stem-walkthroughs, discovery-apps) or nothing.
  No repo anywhere enables both sets. (Decision for the operator — see below.)
- Four class repos contain real code with tests that nothing runs: che2301 (`circuit-lab`,
  27 test files), ime3261, mte2070 (`s5-lab`), mfe2010 (`foundry`).
- che2301-walkthroughs has no CLAUDE.md, no `.claude/`, no onboarding, and doesn't ignore
  `.env`/`.mcp.json`.

**Code/platform repos (10):** lens-core, surveyor, Loom_MCP, QuickPrime, AWG, IAKM,
education-plugins, claude-skills-marketplace, SDE_Extraction, loom-platform.
- Only **lens-core** and **Loom_MCP** run tests in CI (Loom_MCP tests one service of several;
  `packages/auth` untested there; repo not onboarded).
- **SDE_Extraction is the biggest gap**: the most code in the fleet (30 py + 30 ts, eslint and
  pyproject configs present) with **zero workflows** and legacy plugins only.
- **surveyor**: 17 Python files, 10 tests, no CI, no lint.
- claude-skills-marketplace's `validate.yml` calls pytest with no tracked test files — the
  step likely passes vacuously.
- **The ADR-0010 guard exists in zero code/platform repos** — it was rolled out to class
  repos only.
- No linter runs in CI anywhere in the fleet.

**Housekeeping flags:** `.project-intelligence/` is tracked in every onboarded repo except
QuickPrime, while the project-launch skill and QuickPrime treat it as local/untracked — the
rule needs one answer (see decisions). Literal `onrender.com` URLs appear in tracked files of
~12 repos: consistent with the env-ref convention when it's URL + `${TAPESTRY_MEMORY_API_KEY}`
(keys stay out; URLs are fine per tapestry's own tracked `.mcp.json`), but education-lab's
`.env.template` and a few stragglers are worth one pass. No literal `sk-`/`ghp_`/`Bearer ey`
tokens found in any tracked file outside the one `.env` leak.

## What belongs in the pipelines (tapestry first)

Ordered by value-per-effort; each is small and independent:

1. **Branch protection on main** (operator, ~2 min in Settings → Branches or a ruleset):
   require `tests`, `plugin version check`, `private files check`, and Vercel. This single
   step converts the entire existing CI layer from advisory to real.
2. **Add the two missing test legs to `tests.yml`**: `packages/cli/tests` and
   `integrations/claude-code/tapestry-discipline/tests` (fix the 5 env-dependent failures
   while wiring, or mark them). Make `publish-cli.yml` run the cli tests before publishing.
3. **Lint + type-check leg**: ruff (services, packages, plugin scripts) + `astro check` /
   `tsc --noEmit` for the apps that have configs. Start advisory, flip to required after a
   clean week. This also makes the Copilot instructions' "defer to CI" true.
4. **Frontmatter guard**: a 20-line CI step that YAML-parses frontmatter of every
   `apps/docs-site/src/content/docs/**/*.md` — the exact class of failure that cost six PRs.
5. **Secret scan**: gitleaks (or GitHub secret-scanning push protection, free on public
   repos) — directly motivated by finding #1. Plus Dependabot alerts (free, one settings
   toggle).
6. **Changelog format check**: extend `check_changelog.py` to validate the frontmatter
   fields/kind enum it already documents.
7. **Activate tapestry's own git hook**: `git config core.hooksPath .githooks` in each clone
   (one line in `catch-up-machine.ps1` makes it fleet-automatic).
8. **Fix the stale runtime paths** in `pre_tool_use.py:109` (`platform/`,`web/` →
   `services/`,`apps/`,`packages/`) so the citation check does its job (discipline 0.1.24).

## Generalization: per-repo-type baselines

**Every repo (universal floor):** `.gitignore` covering `.env`/`.mcp.json`/`.shared`/
`.tapestry-shared.local`; CLAUDE.md + AGENTS.md; onboarded (`.project-intelligence` minted);
the ADR-0010 private-files guard (hook + CI); `.github/copilot-instructions.md` (a trimmed
generic version: tone, env-ref-only secrets, diff-only advisory review).

**Class repos add:** nothing heavier — unless the repo contains an embedded app (circuit-lab,
foundry, s5-lab): then that app's tests get one tiny CI workflow. Class repos keep their
education-domain plugin set.

**Code-heavy repos add:** tests in CI (all suites, not one), ruff/eslint + type-check in CI,
branch protection once checks are green, secret scanning. Immediate candidates, worst-first:
SDE_Extraction, surveyor, Loom_MCP (complete its matrix), lens-core (add lint).

**Plugin/marketplace repos add:** manifest validation (claude-skills-marketplace's
`validate.yml` is the model — once its vacuous pytest step is fixed), markdownlint, secret
scanning (they're public).

**Starter-stage repos (QuickPrime, AWG, loom-platform):** universal floor only; code checks
arrive with the first real code (the project-launch skill should seed the floor, which means
the tapestry CLI templates carry it — `tapestry init` already seeds guard + gitignore as of
0.1.8, so new repos are covered; this baseline work is for the existing fleet).

## Decisions only the operator can make

1. **Rotate the Grafana Cloud token + approve the history scrub** of
   claude-skills-marketplace (and push the containment commit `3eceadd`). Urgent.
2. **Branch protection on tapestry main** — which checks to require.
3. **Plugin layering**: should class repos run tapestry-discipline alongside the
   education-lab set, or is domain-separation intentional? (No repo currently runs both;
   the answer determines what the class baseline includes.)
4. **`.project-intelligence/`: tracked or local?** The fleet tracks it; the newest rule says
   local. One answer, then the fleet conforms.
5. How much of `docs/migration-cicd/`'s prescribed pipeline (six workflows, drift-catcher,
   parity) is still wanted vs superseded — build or retire the doc's claims.

## Sources

- Tapestry layer audit + fleet inventory: two Explore agents, this session (read-only;
  evidence cited per-file in their findings, preserved in the session transcript).
- loom-memory: `coord-minipc-pr190-merged-2026-11-08`, `principle-three-boundary-hook-stack-agent-vs-git-vs-ci-2026-11-07`, `architecture-tracking-gap-analysis-2026-11-07`.
- Related: `docs/changelog/2026-11-08-copilot-review-replaces-claude-ci-review.md`, ADR 0010,
  `docs/migration-cicd/01-pipeline-architecture.md`.
