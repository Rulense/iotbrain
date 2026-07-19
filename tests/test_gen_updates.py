# tests/test_gen_updates.py
from scripts.gen_updates import (
    UPDATES_CAP,
    build_stats,
    build_updates,
    first_sentence,
    main,
    skill_company,
)


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
    assert skill_company("brain-distill") == "nvidia"
    assert skill_company("rdk-peripheral-cookbook") == "d-robotics"
    assert skill_company("totally-unknown-skill") is None


def test_unmapped_skill_fails(tmp_path, capsys):
    skill = tmp_path / "skills" / "mystery-skill" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: mystery-skill\ndescription: Does things.\n---\n")
    (tmp_path / "brain").mkdir()
    assert main(["--check", "--repo-root", str(tmp_path)]) == 1
    assert "mystery-skill" in capsys.readouterr().err


def test_check_clean_on_real_repo():
    # updates.json and the index.html fallback are committed regenerated;
    # --check against the real repo must be clean.
    assert main(["--check"]) == 0
