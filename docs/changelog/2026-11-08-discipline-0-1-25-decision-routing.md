---
date: 2026-11-08
kind: feature
area: integrations/claude-code/tapestry-discipline
prs: []
adrs: []
memory: [feedback-module-design-questions-are-the-modules-to-research-2026-11-07]
supersedes: null
---

# discipline 0.1.25 — decision-routing check + session-report union-merge

**What:**

- **stop_audit check 3 (decision routing).** When a response hands items upward with
  phrases like "for Liz to decide" / "awaiting your decision", the Stop hook injects the
  routing rule the operator endorsed on 2026-11-07: the owning module researches its own
  design questions; the operator gets only direction/purpose, naming, operator-gate
  approvals, proprietary/privacy policy, and questions research could not settle.
  Promotion candidate relayed by lens-core; regex is deliberately narrow (explicit
  hand-ups only; verified silent on neutral mentions).
- **`.gitattributes`: `docs/session-reports/*.md merge=union`** — the auto session reports
  grow append-only in parallel on branches and machines; union-merge ends the recurring
  both-added rebase conflicts (4 manual resolutions on 2026-11-08 alone).

**Tests:** full discipline suite 123 passed; regex positive/negative fixtures verified.

**Consumers act on:** both machines `catch-up-machine.ps1` + restart after merge.
