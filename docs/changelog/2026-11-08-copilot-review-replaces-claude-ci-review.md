---
date: 2026-11-08
kind: decision
area: .github
prs: []
adrs: []
memory: [coord-minipc-pr190-merged-2026-11-08]
supersedes: 2026-09-05-agentic-code-review.md
---

# Copilot code review replaces the Claude CI review workflow

**What:** Removes `.github/workflows/agentic-review.yml` (the two advisory Claude review
jobs from #163) and adds `.github/copilot-instructions.md`, which carries the surviving
substance of the custom review prompt: defer to deterministic CI, review only the diff,
the four focus areas (correctness / reuse / simplify / efficiency), the dev-tooling-vs-
runtime distinction, the CLAUDE.md tone rule, and the repo conventions reviews should
enforce (append-only migrations, two-mode rule, plugin version guard, change trail,
env-ref-only secrets).

**Why:** The Claude jobs required a `secrets.ANTHROPIC_API_KEY` that was never provisioned —
every PR since #163 showed two red checks that failed in ~23s at authentication, reviewing
nothing. The operator already pays for GitHub Copilot, whose code review does the same
advisory job with no key management and no separate API billing. Decision made 2026-11-08
("I pay for copilot on github").

**Operator action to complete the switch:** enable automatic Copilot review on pull
requests in the repo settings on github.com (Settings → Rules/Branches), or request a
Copilot review per-PR. Copilot reads `copilot-instructions.md` automatically.

**Security note:** the removed security job was a stock `claude-code-security-review`
action; Copilot review includes its own security eye, and the deterministic
`private-files-check.yml` guard is unaffected.
