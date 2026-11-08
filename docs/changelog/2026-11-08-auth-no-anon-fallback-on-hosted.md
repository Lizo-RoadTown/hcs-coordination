---
date: 2026-11-08
kind: fix
area: packages/auth
prs: []
adrs: []
memory: [auth-fallback-fix-pr34-pending-rollout-2026-11-07, observer-registry-deployment-verified-2026-11-07]
supersedes: null
---

# auth: anonymous requests no longer inherit the self-host tenant on hosted deployments

**What:** `loom_auth.auth_bridge.verify_bearer` fell back to `SELF_HOST_TENANT_ID`
on ANY request without an Authorization header — even when `LOOM_JWT_PUBLIC_KEY`
was configured. On the public Render URLs this served (and accepted writes to)
the self-host tenant's data with no credentials; verified live against
loom-architecture-registry on 2026-11-07. `loom-project-registry` deploys from
THIS repo, so the same gap was live here. Self-host mode now requires BOTH no
header AND no configured public key — which is what the module's own two-mode
commitment already documented. No header + key set → 401. New test file
`packages/auth/python/tests/test_auth_bridge.py` pins every mode.

**Why it was silent:** every known caller (self-observer cron, web dashboard,
discipline-adapter observer, loom-cli without `--token`) relied on the anonymous
fallback, so nothing ever exercised the hosted path and nothing failed.

**Rollout coupling:** merging this changes live behavior on the next deploy.
`OBSERVER_JWT` must be set on the tapestry self-observer cron (it reads it —
`services/self-observer/config.py`), and `skill-making`'s `ack_sender` still
posts anonymously (follow-up). Mirror of the-loom PR #34, which carries the
dashboard and adapter token support plus the full provisioning checklist.
