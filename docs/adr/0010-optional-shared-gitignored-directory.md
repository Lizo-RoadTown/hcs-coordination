# 0010 — optional shared git-ignored directory for cross-machine files

**Date:** 2026-11-07
**Status:** **Accepted** (ratified by the operator, 2026-11-07)

> Numbering: `0006`–`0009` are reserved by the loom-memory evolution decision log
> (`docs/decisions/loom-memory-evolution-log.md`: schema enrichment, store move,
> self-observer, retrieval). This ADR takes `0010` to avoid colliding with them.

## Context

The same git repositories are worked on across more than one machine. Some files must stay **out of git and GitHub entirely** — never committed, gitignored — yet still be available on every machine:

- private or third-party source material (for example, instructor notes, handouts, scans fed into a class repo),
- large assets that do not belong in version control.

GitHub is not the channel: a private repo still uploads and versions its contents, which is neither "stays local" nor appropriate for third-party material. And between two checkouts of the same repo there is no file-sharing path except git.

A research scan (2026-11-07) found no industry standard for "git-ignored but synced across machines." Two solution families exist: content-versioning layered on git (git-annex, DVC, git-lfs) and plain filesystem sync of a git-ignored directory the repo only references. For the constraints here — **optional**, **simple**, **cross-platform** (Windows/macOS/Linux), **outside GitHub**, **per-operator-chosen location** — the second family is correct, in its env-var-referenced form. The versioning tools fail either "simple" (git-annex/DVC) or "outside GitHub" (git-lfs and submodules keep files in git). Full findings: loom-memory `research-cross-machine-gitignored-sharing-convention-2026-11-07`.

Two hard facts from the research shape the decision:

1. **A cloud-sync client syncing a live `.git` directory corrupts repos** (partial writes to packfiles). The synced directory must live outside every git working tree; the repo references it, never contains it.
2. **Committed symlinks are not portable** — Git for Windows disables symlink creation by default (checks out as a text file, or needs admin / Developer Mode), and absolute targets differ per machine. An env-var path avoids this entirely.

## Decision

Define an **optional** convention. It establishes the *mechanism*; the *location* and the *sync engine* are the operator's choice.

- **One namespaced, absolute-path environment variable — `TAPESTRY_SHARED_DIR`** — points at an operator-chosen, externally-synced directory. An optional git-ignored dotfile fallback (`.tapestry-shared.local`, holding the absolute path) covers processes that do not inherit the environment.
- **Unset ⇒ the feature is off.** Nothing changes; git-ignored material simply stays local. This is the whole configuration surface — deliberately not heavier (it follows the GNU Stow `STOW_DIR` / XDG `*_HOME` idiom; the path must be absolute).
- **The operator chooses the sync engine** — OneDrive, Dropbox, Syncthing, a NAS, or nothing. Tapestry neither mandates nor bundles one; it only resolves the path.
- **The directory lives outside every git working tree.** The repo resolves `TAPESTRY_SHARED_DIR` at runtime and reads/writes under it. It never contains the directory and never symlinks it inward (the rule that prevents `.git` corruption).
- **Per-project subpath:** material for a project lives under `$TAPESTRY_SHARED_DIR/<project-slug>/` so projects do not collide in one shared root.
- **Two-layer guard against accidental commits.** Both layers run the same scan — reject anything staged/committed that resolves under the shared directory (or matches the project's private-material patterns):
  - **Local — a git pre-commit hook.** Fast feedback; blocks the commit before it is made, for every commit in that clone regardless of tool (terminal, IDE, or Claude via a shell). Installed by `tapestry init`.
  - **Authoritative — a CI/CD check.** Runs on every push and pull request and fails the build if forbidden material is present. This is the backstop that cannot be bypassed by `git commit --no-verify` or by a machine where the hook was never installed; it also blocks the merge. The pre-commit hook is the convenience; CI is the enforcement.

  If a project exposes a conventional in-repo mount name, that name is git-ignored.
- **For sensitive third-party material, prefer Syncthing (peer-to-peer) or an encrypted store over a consumer cloud folder** — a provider-hosted folder means the provider can access the files. This is a recommendation to the operator, not a constraint on the convention (which stays engine-agnostic).

| Concern | This convention |
|---|---|
| Where files live | operator-chosen dir, synced by whatever the operator runs |
| How the repo finds it | `TAPESTRY_SHARED_DIR` (absolute) + optional `.tapestry-shared.local` |
| If not configured | feature off; files stay local |
| Relationship to the repo | referenced, never contained; no committed symlinks |
| Versioning of the shared files | none — this is for material that should not be versioned |
| Keeping it out of git | git-ignore + outside the tree (primary); git pre-commit hook (local) + CI check (authoritative backstop) |

### Where it lands when built (out of scope for this ADR — a later plan)

- **`tapestry init`** (`packages/cli/tapestry_cli/init.py`) — the canonical, PyPI-distributed entry point every project goes through — seeds the `.gitignore` entry and prints per-OS setup for `TAPESTRY_SHARED_DIR`; if the var is set, records the per-project subpath; if unset, stays silent (local fallback). The base template `.gitignore` carries the same entry for the clone-and-use path.
- **The local guard is a git pre-commit hook**, installed by `tapestry init` (not a `tapestry-discipline` hook — that only fires inside Claude Code sessions and would miss manual commits). The repo has no pre-commit framework in use today, so this introduces one (or a `core.hooksPath`-based committed hook).
- **The authoritative guard is a CI workflow** under `.github/workflows/`, modeled on the existing `tests.yml` (runs on `push` + `pull_request`); it fails the check — and therefore the merge — if forbidden material is present.
- **Not** `project-starter` — it is the legacy standalone scaffolder; building only there would miss every project made with the CLI.

## Consequences

- Projects that do not need cross-machine private files are unaffected — the default is off.
- Cross-platform with no symlink or privilege requirements; Windows Developer Mode is explicitly not needed (a feature, not a gap).
- The operator owns the sync engine and its trust boundary; Tapestry does not take on a cloud dependency or pick a provider.
- The shared files are not versioned. That is intended: the convention is for material that should not be in history. Anything needing versioning belongs in git.
- Settled at ratification: the env-var name is `TAPESTRY_SHARED_DIR` (the operator was indifferent to the exact name), and the guard is **two-layer — git pre-commit (local) plus a CI check (authoritative)**, not a Claude-only discipline hook.
- Introducing a git pre-commit hook and a new CI check is net-new machinery for this repo (no pre-commit framework exists today). The implementation — the hook, the CI workflow, and the `tapestry init` wiring — is a follow-on plan, not part of this ADR.

## See also

- loom-memory `research-cross-machine-gitignored-sharing-convention-2026-11-07` — the research findings and tool comparison.
- loom-memory `feedback-shared-ignored-location-is-configurable-not-hardcoded-2026-11-07` — the operator constraints (optional, configurable, research-first).
- loom-memory `onedrive-cross-machine-handshake-test-2026-11-07` — the operator's own instance (OneDrive on two machines).
- loom-memory `scaffolding-canonical-tapestry-cli-three-systems-2026-11-07` — why the build lands in `tapestry init`, not `project-starter`.
