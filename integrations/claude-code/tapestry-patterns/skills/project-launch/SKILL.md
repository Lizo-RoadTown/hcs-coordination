---
name: project-launch
description: Use when creating ANY new project or repo for the operator, in any wording — "launch a project", "start a repo", "new project called X", "scaffold me a...", "set up a project for..." — or when a session discovers an existing repo that was never onboarded (missing .project-intelligence/, flagged by the tapestry-discipline session-start hook). The skeleton comes from the tapestry CLI, never hand-rolled; customization happens ON TOP of the minted skeleton.
---

# Project launch

## Core principle

**Every new project gets the same skeleton from the tapestry CLI, then gets customized on top.**
Never hand-roll the basics. The CLI is the single source of the skeleton (ADR 0004 lineage;
`scaffolding-canonical-tapestry-cli-three-systems-2026-11-07`: three scaffolders exist,
tapestry-cli on PyPI is canonical — `project-starter` and `claude-project-starter` are legacy).

The incident this skill exists to prevent: QuickPrime (2026-11-07) was "launched" with
hand-written docs *describing* the setup but no actual equipment — no registration, no
`.project-intelligence/`, no local memory wiring. The operator had to notice and ask.
Recorded in loom-memory `feedback-equip-new-projects-fully-not-just-docs-2026-11-07`.

## The sequence

1. **PROBE** — does the directory already exist? Is it already a git repo? Does
   `.project-intelligence/` already exist (then this is a re-equip or second-machine mint,
   not a launch)? Is the `tapestry` CLI on PATH (`tapestry -h`)? If the CLI is missing:
   `pip install tapestry-cli`, and if PyPI is behind what main needs, install from the
   tapestry repo checkout (`pip install -e packages/cli`).

2. **MINT THE SKELETON — before any custom content:**
   - New directory: `tapestry init --slug <slug> ...`
   - Existing directory/repo: `tapestry onboard --slug <slug> --name <Name> --description "..." --registry-url <registry URL from the tapestry repo's docs>`
   - The CLI's default registry URL is a placeholder — always pass `--registry-url`.
   - Slug is kebab-case, lowercase; it becomes `LOOM_PROJECT_ID`.

3. **VERIFY the minimum kit exists** (the CLI should have produced all of it — check, don't assume):

   | Piece | Where | Committed? |
   |---|---|---|
   | `.project-intelligence/` + registry UUID | repo root | NO — local/untracked |
   | `.env` with `LOOM_PROJECT_ID=<slug>` | repo root | NO |
   | `.mcp.json` → loom-memory, `${TAPESTRY_MEMORY_API_KEY}` env-ref (never a literal key) | repo root | NO |
   | `.claude/settings.json` enabling `tapestry-discipline@tapestry` + `tapestry-patterns@tapestry` | repo root | yes |
   | `.gitignore` covering `.env`, `.mcp.json`, `.project-intelligence/`, `.shared`, `.tapestry-shared.local` | repo root | yes |
   | CLAUDE.md / AGENTS.md | repo root | yes |
   | docs skeleton (adr/, architecture/) | docs/ | yes |

4. **CUSTOMIZE on top** — charter, domain docs, code, extra plugins (e.g. `lens-log`),
   project-specific rules. Customization never replaces skeleton pieces; it adds to them.

5. **RECORD** — write a loom-memory `project-<slug>-launched-<date>` record with the registry
   UUID and what was customized. If the repo will live on more than one machine, note what the
   other machine owes (its own `.project-intelligence/` mint + local files) per the
   `device-coordination` skill.

## Public-destined repos (boundary-ruled)

A repo that will go public with outside participants (e.g. QuickPrime) still gets the FULL kit —
the boundary rule changes **where pieces live, never whether they exist**:

- Committed tree: only public-safe pieces (plugin enablement, docs skeletons, .gitignore).
- Local untracked: ALL fleet wiring (.mcp.json, .env, .project-intelligence/). No fleet URLs,
  tenant IDs, keys, or memory content in any commit.
- **Scan everything the scaffolder wrote before committing** — templates can carry fleet
  vocabulary (caught live: an ADR template's "loom-memory keys" line). `grep -rn
  "onrender\|loom-\|lizo" <new files>` before the first commit.

## Anti-patterns

| Thought | Reality |
|---|---|
| "I'll write a CLAUDE.md describing the setup; the operator can run it later" | Documenting the kit is not equipping it. Run the CLI now. |
| "This project is special, I'll hand-roll a cleaner skeleton" | Customization goes ON TOP of the minted skeleton, never instead of it. |
| "It's public-destined, so skip the fleet equipment" | The kit still exists — it just lives in local untracked files. |
| "The registry is cold/slow, skip onboarding" | Free-tier cold starts take ~30-60s. Wait for it. If registration truly fails, leave a visible `REGISTRY-PENDING` note and record it in memory — never silently skip. |
| "The CLI isn't installed, I'll just copy files from another repo" | `pip install tapestry-cli` (or `-e packages/cli` from the tapestry checkout) takes one minute. |

## Backstop

The tapestry-discipline session-start hook warns when a repo enables the tapestry plugins but
has no `.project-intelligence/`. If that warning appears, this skill is the response: PROBE
whether it is (a) a never-onboarded project → onboard it, or (b) a fresh clone on a second
machine of an already-registered project → mint locally without creating a duplicate registry
row (check the slug against the registry first).
