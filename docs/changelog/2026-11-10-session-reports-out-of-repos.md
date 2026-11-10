---
date: 2026-11-10
kind: fix
area: integrations/claude-code/tapestry-discipline
prs: []
adrs: []
memory: [decision-operator-approvals-batch-2026-11-10]
supersedes: null
---

# Session reports leave the working repo (discipline 0.1.28)

**What:** the Stop hook no longer writes upskilling reports into `<repo>/docs/session-reports/`,
and it no longer commits them. This was the operator's decision 5 of 2026-11-10. Reports now go,
in order of preference, to:
1. `$TAPESTRY_SHARED_DIR/<project>/session-reports/`, the ADR-0010 shared space, which OneDrive syncs
   across the operator's machines;
2. the folder named by the repo's `.tapestry-shared.local` pointer, plus `session-reports/`;
3. `~/.claude/session-reports/<project>/` as a local fallback.

The folder is created only when a report is written, so the hook leaves no placeholder files. That
matches the base-module standard's rule against empty folders. The `_autocommit_report` function is
removed.

**Why:**
- Writing session text into whatever repo the session ran in carried personal content into project
  repos. QuickPrime's boundary rule forbids exactly that.
- The per-session commits were the fleet's main source of merge conflicts: 15 of 30 recent tapestry
  commits were `chore(session-report)`, and rebases conflicted repeatedly.

The loom-memory record of each report is unchanged. The existing tracked report files in each repo stay
as history. Nothing new is added to them.

**Tests:** the persistence tests now pin shared-space, pointer and fallback placement, that the repo is
never written, that git never runs, and that no folder is created for an empty report. 3 of the new tests
fail against the old code; the plugin suite passes (135).

**Consumers act on:** both machines run `catch-up-machine.ps1` and restart.
