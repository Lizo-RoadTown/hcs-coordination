import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import roadmap  # noqa: E402

DEFN = {"version": 1, "role": "whole", "module": "lens-core",
        "modules": ["lens-core", "lens-ingest"], "proposed": ["access + tenancy"]}


def item(**kw):
    base = {"id": "a", "title": "A", "outcome": "o", "horizon": "now", "firmness": "firm",
            "status": "proposed", "owner": "lens-core", "exit_check": "pytest"}
    base.update(kw)
    return base


def doc(*items, **kw):
    d = {"version": 1, "owners": ["operator"], "parked": ["lens-ingest", "access + tenancy"],
         "items": list(items)}
    d.update(kw)
    return d


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "decomposition.json").write_text(json.dumps(DEFN), encoding="utf-8")
    return tmp_path


def errors(repo, d):
    return roadmap.check(d, roadmap.module_map(repo))


def test_valid_roadmap_has_no_errors(repo):
    assert errors(repo, doc(item())) == []


def test_module_map_reads_modules_and_proposed(repo):
    assert roadmap.module_map(repo) == {"lens-core", "lens-ingest", "access + tenancy"}


def test_missing_required_field(repo):
    bad = item()
    del bad["outcome"]
    assert any("outcome" in e for e in errors(repo, doc(bad)))


def test_bad_enum_values(repo):
    errs = errors(repo, doc(item(horizon="soon", firmness="maybe", status="wip")))
    assert len([e for e in errs if "must be one of" in e]) == 3


def test_duplicate_ids(repo):
    assert any("duplicate" in e for e in errors(repo, doc(item(), item())))


def test_owner_must_be_in_module_map_or_owners(repo):
    assert any("owner" in e for e in errors(repo, doc(item(owner="lens-nowhere"))))
    assert not any("owner" in e for e in errors(repo, doc(item(owner="operator"))))


def test_unknown_dependency_and_cycle(repo):
    errs = errors(repo, doc(item(id="a", depends_on=["zzz"])))
    assert any("unknown" in e for e in errs)
    errs = errors(repo, doc(item(id="a", depends_on=["b"]), item(id="b", depends_on=["a"])))
    assert any("cycle" in e for e in errs)


def test_in_progress_needs_dependencies_done(repo):
    errs = errors(repo, doc(item(id="a", status="in-progress", depends_on=["b"]), item(id="b")))
    assert any("not done" in e for e in errs)
    ok = doc(item(id="a", status="in-progress", depends_on=["b"]),
             item(id="b", status="done", evidence=["abc123"]))
    assert errors(repo, ok) == []


def test_done_needs_evidence(repo):
    assert any("evidence" in e for e in errors(repo, doc(item(status="done"))))


def test_firm_needs_exit_check(repo):
    assert any("exit_check" in e for e in errors(repo, doc(item(exit_check=""))))


def test_loose_needs_decide_when_and_cannot_be_built(repo):
    errs = errors(repo, doc(item(firmness="loose", exit_check=None)))
    assert any("decide_when" in e for e in errs)
    errs = errors(repo, doc(item(firmness="loose", decide_when="x", status="in-progress")))
    assert any("only firm" in e for e in errs)


def test_every_module_needs_an_item_or_parked(repo):
    errs = errors(repo, doc(item(), parked=[]))
    assert any("lens-ingest" in e for e in errs) and any("access + tenancy" in e for e in errs)


def test_render_groups_by_horizon_and_lists_done_last(repo):
    d = doc(item(id="n1", title="Now thing"), item(id="l1", title="Later thing", horizon="later"),
            item(id="d1", title="Done thing", status="done", evidence=["abc123"]))
    md = roadmap.render(d)
    assert md.index("## Now") < md.index("Now thing") < md.index("## Later") < md.index("Later thing")
    assert md.index("## Done") < md.index("Done thing")
    assert "generated from roadmap.yaml" in md


def test_cli_check_flags_stale_markdown(repo, capsys):
    (repo / "roadmap.yaml").write_text(yaml.safe_dump(doc(item())), encoding="utf-8")
    assert roadmap.main(["render", "--root", str(repo)]) == 0
    assert roadmap.main(["check", "--root", str(repo)]) == 0
    (repo / "ROADMAP.md").write_text("old", encoding="utf-8")
    assert roadmap.main(["check", "--root", str(repo)]) == 1
    assert "ROADMAP.md is out of date" in capsys.readouterr().out


def test_real_roadmap_is_valid():
    # The whole-system module list lives in hcs-decomposition (H6). CI checks it out and sets
    # ROADMAP_WHOLE; locally, point ROADMAP_WHOLE at a hcs-decomposition clone.
    import os
    whole = os.environ.get("ROADMAP_WHOLE")
    if not whole:
        pytest.skip("ROADMAP_WHOLE not set (path to hcs-decomposition's decomposition.json)")
    root = Path(__file__).resolve().parents[1]
    assert roadmap.main(["check", "--root", str(root), "--whole", whole]) == 0


def test_component_ids_must_cover_the_map_and_be_unique(repo):
    data = dict(DEFN, ids={"lens-core": "pr-001", "lens-ingest": "pr-002"})
    (repo / "decomposition.json").write_text(json.dumps(data), encoding="utf-8")
    errs = roadmap.check_ids(repo)
    assert any("access + tenancy" in e for e in errs)
    data["ids"]["access + tenancy"] = "pr-002"
    (repo / "decomposition.json").write_text(json.dumps(data), encoding="utf-8")
    assert any("pr-002" in e and "more than one" in e for e in roadmap.check_ids(repo))
    data["ids"]["access + tenancy"] = "x-3"
    (repo / "decomposition.json").write_text(json.dumps(data), encoding="utf-8")
    assert any("pr-NNN" in e for e in roadmap.check_ids(repo))
    data["ids"]["access + tenancy"] = "pr-003"
    data["ids"]["gone"] = "pr-004"
    (repo / "decomposition.json").write_text(json.dumps(data), encoding="utf-8")
    assert any("gone" in e for e in roadmap.check_ids(repo))


def test_component_ids_optional_until_declared(repo):
    assert roadmap.check_ids(repo) == []
