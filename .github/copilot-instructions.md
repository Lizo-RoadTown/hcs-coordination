# Copilot instructions — tapestry

Tapestry is the operator's system-of-record monorepo: platform services under `services/`,
the docs site under `apps/docs-site/`, Claude Code plugins under `integrations/claude-code/`,
the CLI under `packages/cli/`, operating docs under `docs/`.

## Code review

Reviews here are advisory: comment, never approve or request changes on the author's behalf.

**Defer to deterministic CI.** Required checks already cover tests (`tests.yml`), plugin
version alignment (`plugin-version-check.yml`), the change-trail guard, and the private-files
check. Do not restate what a linter, type-checker, or test run would catch — if a
deterministic tool would flag it, stay silent and let that check speak.

Review only the diff. Focus on what deterministic CI cannot see:

- **Correctness** — real bugs, logic errors, edge cases, unsafe assumptions.
- **Reuse** — an existing helper, util, or pattern in this repo that the change should use
  instead of reimplementing.
- **Simplify** — clearer or smaller equivalents of the changed code.
- **Efficiency** — avoidable work, N+1 patterns, needless allocations or extra passes.

Distinguish **dev-tooling from runtime**: `scripts/`, `docs/`, `integrations/claude-code/`
are tooling; `services/`, `packages/`, `apps/` are runtime or shipped code. Hold runtime
changes to a stricter bar (error paths, tenancy, fail-closed behavior).

Prefer a few high-confidence comments over broad speculation. If the diff looks good, say so
briefly and leave nothing inline.

## Conventions that apply to suggestions

- **Tone (CLAUDE.md "Tone")**: plain, direct, descriptive. Describe what *is*, not what it
  isn't. No marketing voice, in code comments and docs alike.
- **Migrations are append-only**: never suggest editing a landed file under
  `infra/migrations/` — a correction is a new numbered migration plus an
  `infra/migrations/APPLIED.md` ledger row.
- **Two-mode rule**: services consider both `PLATFORM_MODE=self_host` (default) and
  `=hosted`; flag changes that silently assume one mode.
- **Plugin version guard**: any change under `integrations/claude-code/<plugin>/` that alters
  behavior needs the version bumped in BOTH `.claude-plugin/marketplace.json` and that
  plugin's `.claude-plugin/plugin.json` (they must match).
- **Change trail**: substantive changes carry a `docs/changelog/` entry in the same PR.
- **Secrets**: nothing under version control ever contains a literal key, token, or JWT —
  env-refs only (e.g. `${TAPESTRY_MEMORY_API_KEY}`). Flag any literal credential immediately.
