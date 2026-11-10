---
date: 2026-11-10
kind: fix
area: services/self-observer
prs: []
adrs: []
memory: [decision-repo-renames-hcs-prefix-2026-11-10]
supersedes: null
---

# self-observer follows GitHub repo-rename redirects

**What happened:** on 2026-11-10 the operator renamed the six module repos (tapestry →
hcs-coordination, Loom_MCP → hcs-memory, and so on). GitHub keeps the old names working through
redirects, but its API answers an old name with **HTTP 301**. The scanner's httpx client
(`github_scanner.py:159`) did not follow redirects, which is httpx's default. Every scan of an
old name, whether a static-core target (`config.py:80`) or a registry-discovered repo, therefore
landed in the "not 200" branch, printed a warning and **returned with nothing scanned**. The
live 6-hourly cron kept reporting success. That is a silent blind spot.

**Fix:** `follow_redirects=True` on the scanner's client. Entries keep the repo name they were
scanned under (`target.repo`), so artifact refs stay consistent with what B1 captures (the
plugin marketplace is registered under the old name too). Moving refs to the new names is a
separate, coordinated decision, like the `LOOM_PROJECT_ID` remap.

**Evidence:**
- A raw API GET of the old name returns 301.
- The real scanner, run against GitHub with the old name: 0 entries before the fix, **24
  entries** after.
- New regression test `tests/test_scanner_redirects.py` (a mock 301 then 200) **fails without
  the fix** and passes with it.
- Suite: 86 passed.
