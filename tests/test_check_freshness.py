# tests/test_check_freshness.py
import json
import textwrap
from pathlib import Path

from scripts.check_freshness import (
    build_report,
    collect_platform_versions,
    main,
    major_minor,
    resolve_latest,
    spec_covers,
    specs_for_ecosystem,
)


def test_major_minor_parsing():
    assert major_minor("v5.5.1") == "5.5"
    assert major_minor("v4.2.0") == "4.2"
    assert major_minor("7.0") == "7.0"
    assert major_minor("7") == "7.0"          # bare major → .0
    assert major_minor("release-tag") is None


def test_spec_covers():
    assert spec_covers("6.x", "6.1")          # x-range covers the series
    assert spec_covers("6", "6.2")            # bare major covers the series
    assert spec_covers("6.1", "6.1")          # exact
    assert spec_covers("6.1.3", "6.1")        # patch release covers its series
    assert not spec_covers("6.1", "6.2")
    assert not spec_covers("5.x", "6.0")
    assert not spec_covers("6.10", "6.1")     # 6.10 is not a 6.1 patch


def test_specs_for_ecosystem_matching():
    versions = ["JetPack 6.x", "jetpack 7.x", "L4T 36.x", "ESP-IDF 5.3", "all"]
    assert specs_for_ecosystem(versions, "JetPack") == ["6.x", "7.x"]
    assert specs_for_ecosystem(versions, "ESP-IDF") == ["5.3"]
    # a bare "all" names no ecosystem and is never attributed to one
    assert specs_for_ecosystem(versions, "Zephyr") == []


def test_report_uncovered_ecosystem():
    lines = build_report({"ESP-IDF": "v5.5"}, ["JetPack 6.x"])
    assert len(lines) == 1
    assert lines[0].startswith("ESP-IDF: latest release v5.5 (series 5.5)")


def test_report_covered_ecosystem_silent():
    assert build_report({"JetPack": "7.0"}, ["JetPack 7.x"]) == []
    assert build_report({"ESP-IDF": "v5.5.1"}, ["ESP-IDF 5.5"]) == []


def test_report_failed_source_tolerated(capsys):
    # One ecosystem's source failed (None) — warn on stderr, still report
    # the others on stdout.
    lines = build_report({"Zephyr": None, "ESP-IDF": "v5.5"}, [])
    captured = capsys.readouterr()
    assert [l.split(":")[0] for l in lines] == ["ESP-IDF"]
    assert "Zephyr" in captured.err and "could not resolve" in captured.err


def test_report_unparseable_version_tolerated(capsys):
    assert build_report({"Zephyr": "weird-tag"}, []) == []
    assert "unparseable" in capsys.readouterr().err


def test_resolve_latest_pinned_and_unknown():
    # no network involved for these source types
    assert resolve_latest({"type": "pinned", "latest": "7.0"}) == "7.0"
    assert resolve_latest({"type": "pinned"}) is None
    assert resolve_latest({"type": "carrier-pigeon"}) is None
    assert resolve_latest({"type": "github-release"}) is None  # no repo given


def test_collect_platform_versions_skips_generated(tmp_path):
    brain = tmp_path / "brain"
    (brain / "iot").mkdir(parents=True)
    (brain / "iot" / "a.md").write_text(textwrap.dedent("""\
        ---
        title: A
        type: fix
        company: espressif
        keys: ["k", "symptom phrase"]
        platform_versions: ["ESP-IDF 5.3", "all"]
        devices: [all]
        status: unverified
        sources: ["https://example.com"]
        ---
        body
        """))
    (brain / "INDEX.md").write_text("# index\n")
    (brain / "KEYWORDS.md").write_text("k → iot/a.md\n")
    assert collect_platform_versions(brain) == ["ESP-IDF 5.3", "all"]


FIXTURE = {
    "latest": {
        "JetPack": "7.0",       # covered below → not reported
        "ESP-IDF": "v5.5",      # uncovered → reported
        "Zephyr": None,          # failed source → warned, tolerated
    },
    "platform_versions": ["JetPack 7.x", "JetPack 6.x"],
}


def test_main_with_input_fixture(tmp_path, capsys):
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps(FIXTURE))
    assert main(["--input", str(fixture)]) == 0  # always exit 0 locally
    captured = capsys.readouterr()
    out_lines = captured.out.strip().splitlines()
    assert len(out_lines) == 1 and out_lines[0].startswith("ESP-IDF:")
    assert "Zephyr" in captured.err


def test_main_fixture_all_covered_prints_nothing(tmp_path, capsys):
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps(
        {"latest": {"JetPack": "7.0"}, "platform_versions": ["JetPack 7.x"]}))
    assert main(["--input", str(fixture)]) == 0
    assert capsys.readouterr().out == ""


def test_real_watchlist_is_valid():
    root = Path(__file__).resolve().parent.parent
    watchlist = json.loads((root / "watchlist.json").read_text())["watchlist"]
    ecosystems = {e["ecosystem"] for e in watchlist}
    assert {"JetPack", "ESP-IDF", "Zephyr", "MicroPython"} <= ecosystems
    for entry in watchlist:
        source = entry["source"]
        if source["type"] == "pinned":
            assert source["latest"]
            assert "comment" in entry  # maintainers must know to bump it
        else:
            assert source["type"] == "github-release" and "/" in source["repo"]
