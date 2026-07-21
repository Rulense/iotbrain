# tests/test_gen_updates.py
import textwrap

import pytest

from scripts.gen_updates import (
    KEYWORDS_HEADER,
    UPDATES_CAP,
    build_stats,
    build_updates,
    collect_keyword_map,
    first_sentence,
    index_scale_warning,
    main,
    patch_readme,
    render_keywords,
    render_readme_stats,
    skill_company,
)

ENTRY_TMPL = textwrap.dedent("""\
    ---
    title: %(title)s
    type: fix
    company: nvidia
    keys:
    %(keys)s
    platform_versions: ["JetPack 6.1"]
    devices: [orin-nano]
    status: unverified
    sources: ["https://example.com"]
    ---
    body
    """)


def entry_text(title, keys):
    return ENTRY_TMPL % {
        "title": title,
        "keys": "\n".join('  - "%s"' % k for k in keys),
    }


def row(title, date, **over):
    base = {"title": title, "type": "recipe", "domain": "ml-stack",
            "company": "nvidia", "date": date}
    base.update(over)
    return base


def test_build_stats_counts():
    entries = [
        row("a", "2026-07-01"),
        row("b", "2026-07-01", domain="vision"),
        row("c", "2026-07-02", domain="vision", company="raspberry-pi"),
    ]
    skills = [
        row("s1", "2026-07-01", type="skill", domain="skills", company="espressif"),
        row("s2", "2026-07-01", type="skill", domain="skills", company="nvidia"),
    ]
    assert build_stats(entries, skills) == {
        "entries": 3, "skills": 2, "domains": 2, "platforms": 3,
    }


def test_build_stats_empty():
    assert build_stats([], []) == {
        "entries": 0, "skills": 0, "domains": 0, "platforms": 0,
    }


def test_build_stats_excludes_all_from_platforms():
    # "all" marks vendor-neutral skills (iot-dev, brain-distill) — it is not
    # a platform and must not inflate the distinct-platforms count.
    entries = [row("a", "2026-07-01")]
    skills = [
        row("iot-dev", "2026-07-01", type="skill", domain="skills", company="all"),
        row("s2", "2026-07-01", type="skill", domain="skills", company="zephyr"),
    ]
    stats = build_stats(entries, skills)
    assert stats["platforms"] == 2  # nvidia + zephyr, not "all"
    assert stats["skills"] == 2


def test_build_updates_newest_first_tiebreak_alphabetical():
    entries = [row("beta", "2026-07-01"), row("alpha", "2026-07-01")]
    skills = [row("zeta", "2026-07-02", type="skill", domain="skills")]
    titles = [u["title"] for u in build_updates(entries, skills)]
    assert titles == ["zeta", "alpha", "beta"]


def test_build_updates_caps_rows():
    entries = [row("e%03d" % i, "2026-07-01") for i in range(UPDATES_CAP + 10)]
    assert len(build_updates(entries, [])) == UPDATES_CAP


def test_first_sentence_takes_first_and_drops_period():
    assert first_sentence("Short one. Second sentence.") == "Short one"


def test_first_sentence_truncates_long():
    sentence = first_sentence("word " * 40)
    assert len(sentence) <= 81
    assert sentence.endswith("…")


def test_skill_company_mapping():
    assert skill_company("jetson-llm-serve") == "nvidia"
    assert skill_company("iot-dev") == "all"
    assert skill_company("brain-distill") == "all"
    assert skill_company("rdk-peripheral-cookbook") == "d-robotics"
    assert skill_company("totally-unknown-skill") is None


README_DATA = {
    "stats": {"entries": 2, "skills": 1, "domains": 2, "platforms": 1},
    "updates": [row("newer", "2026-07-18"), row("older", "2026-07-01")],
}
README_TMPL = (
    "# proj\n\nintro paragraph\n\n"
    "<!-- IOTBRAIN_STATS_START -->\nstale hand-written line\n"
    "<!-- IOTBRAIN_STATS_END -->\n\nrest of the file\n"
)


def test_readme_stats_line_uses_newest_row_date_not_wall_clock():
    assert render_readme_stats(README_DATA) == (
        "**2** brain entries · **1** skills · **2** domains · **1** platforms"
        " — last updated 2026-07-18"
    )


def test_patch_readme_replaces_sentinel_region():
    out = patch_readme(README_TMPL, README_DATA)
    assert "stale hand-written line" not in out
    assert render_readme_stats(README_DATA) in out
    assert out.startswith("# proj\n\nintro paragraph\n\n<!-- IOTBRAIN_STATS_START -->\n")
    assert out.endswith("<!-- IOTBRAIN_STATS_END -->\n\nrest of the file\n")
    assert patch_readme(out, README_DATA) == out  # idempotent


def test_patch_readme_missing_sentinels_raises():
    with pytest.raises(RuntimeError):
        patch_readme("# no markers here\n", README_DATA)


def _mini_repo(tmp_path):
    (tmp_path / "brain").mkdir()
    skill = tmp_path / "skills" / "iot-dev"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: iot-dev\ndescription: Edge-IoT companion. More text.\n---\nbody\n")
    (tmp_path / "index.html").write_text(
        "<script>\n/*__IOTBRAIN_DATA_START__*/ x /*__IOTBRAIN_DATA_END__*/\n</script>\n")
    (tmp_path / "README.md").write_text(README_TMPL)
    return tmp_path


def test_check_flags_stale_readme(tmp_path, capsys):
    repo = _mini_repo(tmp_path)
    assert main(["--repo-root", str(repo)]) == 0            # generate all files
    assert main(["--check", "--repo-root", str(repo)]) == 0  # now clean
    readme = repo / "README.md"
    readme.write_text(readme.read_text().replace("brain entries", "brain entriez"))
    capsys.readouterr()
    assert main(["--check", "--repo-root", str(repo)]) == 1
    assert "README.md" in capsys.readouterr().out


def test_unmapped_skill_fails(tmp_path, capsys):
    skill = tmp_path / "skills" / "mystery-skill" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: mystery-skill\ndescription: Does things.\n---\n")
    (tmp_path / "brain").mkdir()
    assert main(["--check", "--repo-root", str(tmp_path)]) == 1
    assert "mystery-skill" in capsys.readouterr().err


def _write_entry(repo, rel, title, keys):
    p = repo / "brain" / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(entry_text(title, keys))


def test_collect_keyword_map_and_collisions(tmp_path):
    repo = _mini_repo(tmp_path)
    _write_entry(repo, "vision/a.md", "A", ["No cameras available", "camera not detected"])
    _write_entry(repo, "setup/b.md", "B", ["No cameras available", "boot hangs after flash"])
    mapping = collect_keyword_map(repo)
    assert mapping["camera not detected"] == ["vision/a.md"]
    # collision: one key, both targets
    assert mapping["No cameras available"] == ["setup/b.md", "vision/a.md"]


def test_render_keywords_sorted_one_line_per_key():
    text = render_keywords({
        "zeta key": ["iot/z.md"],
        "No cameras available": ["vision/a.md", "setup/b.md"],
    })
    assert text.startswith(KEYWORDS_HEADER)
    lines = text[len(KEYWORDS_HEADER):].splitlines()
    assert lines == [
        "No cameras available → setup/b.md · vision/a.md",
        "zeta key → iot/z.md",
    ]


def test_keywords_md_written_and_ignored_as_entry(tmp_path):
    repo = _mini_repo(tmp_path)
    _write_entry(repo, "vision/a.md", "A", ["k1", "camera not detected"])
    assert main(["--repo-root", str(repo)]) == 0
    kw = repo / "brain" / "KEYWORDS.md"
    assert "camera not detected → vision/a.md" in kw.read_text()
    # regenerating is idempotent: KEYWORDS.md itself is never treated as an
    # entry or fed back into the map
    assert main(["--check", "--repo-root", str(repo)]) == 0


def test_check_flags_stale_keywords(tmp_path, capsys):
    repo = _mini_repo(tmp_path)
    _write_entry(repo, "vision/a.md", "A", ["k1", "camera not detected"])
    assert main(["--repo-root", str(repo)]) == 0
    assert main(["--check", "--repo-root", str(repo)]) == 0
    # new entry (new keys) without regeneration → KEYWORDS.md is stale
    _write_entry(repo, "setup/b.md", "B", ["k2", "boot hangs after flash"])
    capsys.readouterr()
    assert main(["--check", "--repo-root", str(repo)]) == 1
    assert "KEYWORDS.md" in capsys.readouterr().out


def test_index_scale_warning_thresholds():
    assert index_scale_warning(250) is None
    warning = index_scale_warning(251)
    assert warning is not None
    assert warning.startswith("WARNING")
    assert "Scaling the INDEX" in warning and "251" in warning
    assert index_scale_warning(3, threshold=2) is not None


def test_check_warns_not_fails_over_threshold(tmp_path, capsys, monkeypatch):
    repo = _mini_repo(tmp_path)
    _write_entry(repo, "vision/a.md", "A", ["k1", "camera not detected"])
    _write_entry(repo, "setup/b.md", "B", ["k2", "boot hangs after flash"])
    assert main(["--repo-root", str(repo)]) == 0
    monkeypatch.setattr("scripts.gen_updates.INDEX_SPLIT_THRESHOLD", 1)
    capsys.readouterr()
    assert main(["--check", "--repo-root", str(repo)]) == 0  # warning ≠ failure
    assert "WARNING" in capsys.readouterr().out


def test_check_clean_on_real_repo():
    # updates.json and the index.html fallback are committed regenerated;
    # --check against the real repo must be clean.
    assert main(["--check"]) == 0
