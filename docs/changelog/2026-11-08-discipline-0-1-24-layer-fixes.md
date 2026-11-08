---
date: 2026-11-08
kind: fix
area: integrations/claude-code/tapestry-discipline
prs: []
adrs: []
memory: [audit-check-layers-fleet-2026-11-08]
supersedes: null
---

# discipline 0.1.24 — agent-hook layer fixes from the check-layers audit

**What:** Four fixes that make the agent-hook layer do what it claims
(`docs/audits/2026-11-08-check-layers-audit.md` gaps E10 and the detector friction):

- **Runtime-citation check un-broken.** `pre_tool_use.py` `RUNTIME_PATHS` still listed
  Make_Skills' `platform/` and `web/` — tapestry's runtime (`services/`, `apps/`,
  `packages/`) never matched, so the check had never fired here. Paths added (legacy ones
  kept). The UserPromptSubmit reminder wording updated to match.
- **Scope gate converged (behavior change).** `pre_tool_use` / `user_prompt_submit` /
  `stop_audit` still carried the old hardcoded repo-name allowlist
  (Make_Skills/the-loom/tapestry/project-starter/`_common`) while `session_start` had been
  universalized. All four now share one gate: `LOOM_PROJECT_ID` set, or a
  `TAPESTRY_SCOPE_DIRS` substring match (case-insensitive). Make_Skills and the-loom keep
  working via the `LOOM_PROJECT_ID` already in their `.env`; `project-starter` (no `.env`)
  loses hook coverage unless opted in via `TAPESTRY_SCOPE_DIRS` — it is the retired
  scaffolder, accepted.
- **Repetition detector ignores non-user turns.** It fired on a subagent hand-back whose
  report quoted the detector's own trigger phrase, queueing a bogus correction stub.
  UserPromptSubmit now skips prompts that are agent-message / task-notification /
  system-reminder frames.
- **Upskilling re-warn softened (behavior change).** Since v0.1.20 a single git action after
  a report re-armed the warning — so pushing the very commit the report described triggered
  "UPSKILLING PASS NOT RUN" again (fired 3× on 2026-11-08). A git action since the report now
  re-arms only together with ≥ 2 new assistant turns. Whole-session thresholds unchanged.

**Tests:** the suite's 5 standing failures were real drift, now fixed — observer mocks gained
the newer `skill_name` kwarg; scope tests rewritten to pin the universal gate (including the
no-hardcoded-names guarantee); the re-warn test pins the new ≥ 2-turn rule. **123 passed, 0
failed** — ready to wire into CI (the audit's pipeline step 2).

**Consumers act on:** both machines run `scripts/catch-up-machine.ps1` + restart after merge.
