---
date: 2026-11-07
kind: feature
area: integrations/claude-code
prs: []
adrs: []
memory: [feedback-equip-new-projects-fully-not-just-docs-2026-11-07]
supersedes: null
---

# project-launch skill + not-onboarded session-start check (patterns 0.1.9, discipline 0.1.23)

**What:** Two layers that make "every new project gets the same CLI-minted skeleton" enforced
instead of remembered.

- **`tapestry-patterns:project-launch` skill (0.1.9)** — fires on any new-project request
  ("launch a project", "new repo called X", scaffold asks). Sequence: PROBE → mint the skeleton
  via the tapestry CLI (`tapestry init` / `tapestry onboard`, always with `--registry-url`) →
  verify the minimum kit (registration + .project-intelligence, .env/LOOM_PROJECT_ID,
  .mcp.json env-ref, plugins in .claude/settings.json, .gitignore, docs skeleton) → customize
  ON TOP → RECORD in loom-memory. Carries the boundary-rule variant for public-destined repos
  (full kit still exists; fleet wiring stays in local untracked files; scan scaffolder output
  for fleet vocabulary before committing).
- **tapestry-discipline session-start check (0.1.23)** — `_onboarding_warning()` in
  `scripts/session_start.py`: when the cwd is a git repo whose `.claude/settings.json` enables
  a tapestry plugin but `.project-intelligence/` is absent, the hook emits a loud
  "project not onboarded" context block — including for repos OUTSIDE the normal scope guard,
  since a project created without the CLI has no `LOOM_PROJECT_ID` and is exactly the repo the
  scope guard never reaches. Silent once minted. Functionally verified both ways.

**Why:** QuickPrime (2026-11-07) was launched with docs *describing* the setup but no actual
equipment; the operator had to notice and ask ("you didn't give quickprime any project
intelligence… Is there a reason?"), then asked for a guarantee that doesn't depend on
reminding the agent. Memory records recall the rule; the skill makes it the named procedure;
the hook catches whatever slips through.

**Consumers act on:** both machines run `scripts/catch-up-machine.ps1` + restart Claude Code
to get discipline 0.1.23 / patterns 0.1.9.

**Pre-existing, unrelated:** 5 discipline test failures (test_scope ×3, test_observer ×2) fail
identically on main in a local env; not introduced here.
