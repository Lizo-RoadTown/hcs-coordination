#!/usr/bin/env python3
"""The roadmap: roadmap.yaml is the source of truth; ROADMAP.md is generated from it.

    python scripts/roadmap.py check    # validate roadmap.yaml and that ROADMAP.md is current
    python scripts/roadmap.py render   # regenerate ROADMAP.md

Rules come from the approved method (docs/plans/2026-10-21-roadmap-method-proposal.md):
only firm items are built, done needs evidence, loose items name what decides them, and
every owner is a module in decomposition.json (or a listed outside owner).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml

REQUIRED = ("id", "title", "outcome", "horizon", "firmness", "status", "owner")
HORIZONS = ("now", "next", "later")
FIRMNESS = ("firm", "loose", "hypothesis")
STATUSES = ("proposed", "in-progress", "blocked", "done", "dropped", "superseded")
BUILDING = ("in-progress", "done")


def _whole_path(root) -> Path:
    """The whole-system decomposition.json: `root` may be the file itself or a folder holding it.
    In hcs-coordination the whole lives in hcs-decomposition (H6), passed in via --whole."""
    p = Path(root)
    return p if p.is_file() else p / "decomposition.json"


def module_map(root: Path) -> set[str]:
    data = json.loads(_whole_path(root).read_text(encoding="utf-8"))
    return set(data.get("modules", [])) | set(data.get("proposed", []))


ID_PATTERN = re.compile(r"^pr-\d{3}$")


def check_ids(root: Path) -> list[str]:
    """Stable program-layer IDs: once decomposition.json declares "ids", every module and
    proposed repo needs a unique pr-NNN. IDs are never reused; a removed module's ID moves
    to "retired_ids"."""
    data = json.loads(_whole_path(root).read_text(encoding="utf-8"))
    ids = data.get("ids")
    if ids is None:
        return []
    errs: list[str] = []
    names = set(data.get("modules", [])) | set(data.get("proposed", []))
    errs.extend(f"module '{m}' has no pr- ID in decomposition.json 'ids'" for m in sorted(names - set(ids)))
    errs.extend(f"'ids' names '{m}', which is not a module or proposed repo (move its ID to 'retired_ids')"
                for m in sorted(set(ids) - names))
    retired = list((data.get("retired_ids") or {}).values())
    seen: dict[str, str] = {}
    for name, cid in sorted(ids.items()):
        if not isinstance(cid, str) or not ID_PATTERN.match(cid):
            errs.append(f"'{name}' has ID {cid!r}; IDs must look like pr-NNN")
        elif cid in seen:
            errs.append(f"{cid} is used by more than one module ('{seen[cid]}', '{name}')")
        elif cid in retired:
            errs.append(f"{cid} is retired and cannot be reused ('{name}')")
        seen.setdefault(cid, name)
    return errs


def _cycles(deps: dict[str, list[str]]) -> list[str]:
    found, state = [], {}

    def visit(node: str, path: list[str]) -> None:
        state[node] = "open"
        for nxt in deps.get(node, []):
            if state.get(nxt) == "open":
                found.append(" -> ".join(path[path.index(nxt):] + [nxt]))
            elif nxt in deps and nxt not in state:
                visit(nxt, path + [nxt])
        state[node] = "closed"

    for node in deps:
        if node not in state:
            visit(node, [node])
    return found


def check(doc: dict, modules: set[str]) -> list[str]:
    errs: list[str] = []
    if doc.get("version") != 1:
        errs.append("'version' must be 1")
    items = doc.get("items") or []
    owners = modules | set(doc.get("owners") or [])
    by_id: dict[str, dict] = {}
    for it in items:
        iid = it.get("id", "?")
        for field in REQUIRED:
            if not it.get(field):
                errs.append(f"{iid}: missing '{field}'")
        for field, allowed in (("horizon", HORIZONS), ("firmness", FIRMNESS), ("status", STATUSES)):
            if it.get(field) and it[field] not in allowed:
                errs.append(f"{iid}: '{field}' must be one of {', '.join(allowed)}")
        if iid in by_id:
            errs.append(f"{iid}: duplicate id")
        by_id[iid] = it
        if it.get("owner") and it["owner"] not in owners:
            errs.append(f"{iid}: owner '{it['owner']}' is not a module in decomposition.json "
                        "or a listed outside owner")
        if it.get("firmness") == "firm" and not it.get("exit_check"):
            errs.append(f"{iid}: a firm item needs an exit_check")
        if it.get("firmness") in ("loose", "hypothesis"):
            if not it.get("decide_when"):
                errs.append(f"{iid}: a {it['firmness']} item needs decide_when (the fact that decides it)")
            if it.get("status") in BUILDING:
                errs.append(f"{iid}: only firm items may be in progress or done")
        if it.get("status") == "done" and not it.get("evidence"):
            errs.append(f"{iid}: a done item needs evidence")
    deps = {i: list(it.get("depends_on") or []) for i, it in by_id.items()}
    for iid, ds in deps.items():
        for d in ds:
            if d not in by_id:
                errs.append(f"{iid}: depends on unknown item '{d}'")
            elif by_id[iid].get("status") in BUILDING and by_id[d].get("status") != "done":
                errs.append(f"{iid}: is {by_id[iid]['status']} but '{d}' is not done")
    errs.extend(f"dependency cycle: {c}" for c in _cycles(deps))
    covered = {it.get("owner") for it in items} | set(doc.get("parked") or [])
    errs.extend(f"module '{m}' has no item and is not parked" for m in sorted(modules - covered))
    return errs


def _cell(value) -> str:
    if isinstance(value, list):
        value = ", ".join(str(v) for v in value)
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def render(doc: dict) -> str:
    items = doc.get("items") or []
    out = ["# Roadmap", "",
           "<!-- generated from roadmap.yaml by roadmap/roadmap.py; edit roadmap.yaml, not this file -->",
           "",
           "One roadmap for the six modules. Only **firm** items are built; **loose** and **hypothesis**",
           "items name the fact that decides them. Owners are checked against the whole-system module",
           "list in hcs-decomposition. Method: hcs-observatory `docs/plans/2026-10-21-roadmap-method-proposal.md`.",
           ""]
    open_items = [i for i in items if i.get("status") not in ("done", "dropped", "superseded")]
    for horizon in HORIZONS:
        rows = [i for i in open_items if i.get("horizon") == horizon]
        if not rows:
            continue
        out += [f"## {horizon.capitalize()}", "",
                "| id | item | outcome | owner | firmness | status | depends on | exit check / decides it |",
                "|---|---|---|---|---|---|---|---|"]
        for i in rows:
            gate = i.get("exit_check") if i.get("firmness") == "firm" else f"decide when: {i.get('decide_when')}"
            out.append("| " + " | ".join(_cell(v) for v in (
                i.get("id"), i.get("title"), i.get("outcome"), i.get("owner"), i.get("firmness"),
                i.get("status"), i.get("depends_on"), gate)) + " |")
        out.append("")
    closed = [i for i in items if i not in open_items]
    if closed:
        out += ["## Done", "", "| id | item | owner | status | evidence |", "|---|---|---|---|---|"]
        for i in closed:
            out.append("| " + " | ".join(_cell(v) for v in (
                i.get("id"), i.get("title"), i.get("owner"), i.get("status"), i.get("evidence"))) + " |")
        out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("command", choices=("check", "render"))
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent))
    ap.add_argument("--whole", default=None,
                    help="path to the whole-system decomposition.json (hcs-decomposition). "
                         "Default: a decomposition.json in --root if present, else env ROADMAP_WHOLE")
    args = ap.parse_args(argv)
    root = Path(args.root)
    if args.whole:
        whole = Path(args.whole)
    elif (root / "decomposition.json").is_file():
        whole = root
    else:
        whole = Path(os.environ.get("ROADMAP_WHOLE") or root)
    doc = yaml.safe_load((root / "roadmap.yaml").read_text(encoding="utf-8")) or {}
    md_path = root / "ROADMAP.md"
    if args.command == "render":
        md_path.write_text(render(doc), encoding="utf-8", newline="\n")
        return 0
    errs = check(doc, module_map(whole)) + check_ids(whole)
    current = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    if current.replace("\r\n", "\n") != render(doc):
        errs.append("ROADMAP.md is out of date: run python roadmap/roadmap.py render")
    for e in errs:
        print(e)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
