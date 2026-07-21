# tests/test_check_drift.py
import json
import textwrap
from pathlib import Path

from scripts.check_drift import build_report, main, parse_attribution

SNIPPET = textwrap.dedent("""\
    # Attribution

    Intro prose, no pins here.

    ## Vendor One skills

    - **Upstream repository:** https://github.com/vendor-one/skills
    - **Pinned commit:** `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`

    ### What was vendored

    stuff

    ## License texts

    Prose-only section — must not yield a pin.

    ## Vendor Two (short pin)

    - **Upstream repository:** https://github.com/vendor-two/repo.name
    - **Pinned commit:** `abc1234`
    """)


def test_parse_attribution_snippet():
    pins = parse_attribution(SNIPPET)
    assert [p["repo"] for p in pins] == ["vendor-one/skills", "vendor-two/repo.name"]
    assert pins[0] == {"name": "Vendor One skills",
                       "repo": "vendor-one/skills",
                       "commit": "a" * 40}
    assert pins[1]["commit"] == "abc1234"


def test_parse_attribution_real_file():
    root = Path(__file__).resolve().parent.parent
    pins = parse_attribution((root / "ATTRIBUTION.md").read_text())
    by_repo = {p["repo"]: p["commit"] for p in pins}
    assert len(pins) == 5
    assert by_repo["NVIDIA-AI-IOT/jetson-device-skills"] == \
        "0a803703b2e6fe4fc36e5dac3507bcde7fd8c9dc"
    assert by_repo["espressif/esp-dl"] == "77a8a624a5c91c56a35e76ba5edc00fa32addd08"
    assert "beriberikix/zephyr-agent-skills" in by_repo


PINS = [
    {"name": "One", "repo": "vendor-one/skills", "commit": "a" * 40},
    {"name": "Two", "repo": "vendor-two/repo", "commit": "b" * 40},
]


def test_report_drift_detected():
    heads = {"vendor-one/skills": "c" * 40, "vendor-two/repo": "b" * 40}
    lines = build_report(PINS, heads)
    assert len(lines) == 1
    assert lines[0].startswith("vendor-one/skills (One):")
    assert "c" * 12 in lines[0] and "a" * 12 in lines[0]


def test_report_no_drift_is_empty():
    heads = {"vendor-one/skills": "a" * 40, "vendor-two/repo": "b" * 40}
    assert build_report(PINS, heads) == []


def test_report_short_pin_prefix_matches():
    pins = [{"name": "Two", "repo": "v/r", "commit": "abc1234"}]
    assert build_report(pins, {"v/r": "abc1234" + "f" * 33}) == []
    assert len(build_report(pins, {"v/r": "dead123" + "f" * 33})) == 1


def test_report_failed_head_tolerated(capsys):
    heads = {"vendor-one/skills": None, "vendor-two/repo": "c" * 40}
    lines = build_report(PINS, heads)
    captured = capsys.readouterr()
    assert len(lines) == 1 and lines[0].startswith("vendor-two/repo")
    assert "vendor-one/skills" in captured.err


def test_main_with_input_fixture(tmp_path, capsys):
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps({
        "pins": PINS,
        "heads": {"vendor-one/skills": "c" * 40, "vendor-two/repo": None},
    }))
    assert main(["--input", str(fixture)]) == 0  # always exit 0 locally
    captured = capsys.readouterr()
    out = captured.out.strip().splitlines()
    assert len(out) == 1 and out[0].startswith("vendor-one/skills")
    assert "vendor-two/repo" in captured.err
