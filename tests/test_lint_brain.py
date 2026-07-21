# tests/test_lint_brain.py
from pathlib import Path
import textwrap
import pytest

from scripts.lint_brain import LintError, parse_entry, validate_entry, check_index, main

VALID = textwrap.dedent("""\
    ---
    title: Example fix entry
    type: fix
    company: nvidia
    keys:
      - "ImportError: libexample.so.1"
      - "example library import fails"
    platform_versions: ["JetPack 6.1", "L4T 36.x"]
    devices: [orin-nano]
    status: verified
    verified_on: "Orin Nano, JetPack 6.1, 2026-07-01"
    sources: ["https://forums.developer.nvidia.com/t/example"]
    ---
    ## Context
    x
    ## Knowledge
    x
    ## Verify
    x
    """)


def write(p: Path, text: str) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    return p


def test_valid_entry_passes(tmp_path):
    p = write(tmp_path / "brain" / "ml-stack" / "example.md", VALID)
    assert validate_entry(parse_entry(p), p) == []


def test_missing_frontmatter_raises(tmp_path):
    p = write(tmp_path / "brain" / "ml-stack" / "bad.md", "# no frontmatter\n")
    with pytest.raises(LintError):
        parse_entry(p)


def test_bad_type_fails(tmp_path):
    p = write(tmp_path / "brain" / "ml-stack" / "bad.md", VALID.replace("type: fix", "type: banana"))
    errs = validate_entry(parse_entry(p), p)
    assert any("type" in e for e in errs)


def test_missing_company_fails(tmp_path):
    text = VALID.replace("company: nvidia\n", "")
    p = write(tmp_path / "brain" / "ml-stack" / "bad.md", text)
    errs = validate_entry(parse_entry(p), p)
    assert any("company" in e for e in errs)


def test_missing_platform_versions_fails(tmp_path):
    text = VALID.replace('platform_versions: ["JetPack 6.1", "L4T 36.x"]\n', "")
    p = write(tmp_path / "brain" / "ml-stack" / "bad.md", text)
    errs = validate_entry(parse_entry(p), p)
    assert any("platform_versions" in e for e in errs)


def test_reproduced_by_must_be_list(tmp_path):
    text = VALID.replace(
        "status: verified\n",
        'reproduced_by: "not a list"\nstatus: verified\n')
    p = write(tmp_path / "brain" / "ml-stack" / "bad.md", text)
    errs = validate_entry(parse_entry(p), p)
    assert any("reproduced_by" in e for e in errs)
    ok = VALID.replace(
        "status: verified\n",
        'reproduced_by: ["forum user, Orin NX, JetPack 6.1, 2026-07-10"]\n'
        "status: verified\n")
    p2 = write(tmp_path / "brain" / "ml-stack" / "good.md", ok)
    assert validate_entry(parse_entry(p2), p2) == []


def test_verified_requires_verified_on(tmp_path):
    text = VALID.replace('verified_on: "Orin Nano, JetPack 6.1, 2026-07-01"\n', "")
    p = write(tmp_path / "brain" / "ml-stack" / "bad.md", text)
    errs = validate_entry(parse_entry(p), p)
    assert any("verified_on" in e for e in errs)


KEYS_BLOCK = 'keys:\n  - "ImportError: libexample.so.1"\n  - "example library import fails"'


def test_empty_keys_fails(tmp_path):
    text = VALID.replace(KEYS_BLOCK, "keys: []")
    p = write(tmp_path / "brain" / "ml-stack" / "bad.md", text)
    errs = validate_entry(parse_entry(p), p)
    assert any("keys" in e for e in errs)


def test_single_key_fails_floor(tmp_path):
    # ≥2 keys required: verbatim machine strings + a symptom phrase.
    text = VALID.replace(KEYS_BLOCK, 'keys:\n  - "ImportError: libexample.so.1"')
    p = write(tmp_path / "brain" / "ml-stack" / "bad.md", text)
    errs = validate_entry(parse_entry(p), p)
    assert any("at least 2" in e and "symptom" in e for e in errs)


def test_two_keys_pass_floor(tmp_path):
    p = write(tmp_path / "brain" / "ml-stack" / "good.md", VALID)
    assert validate_entry(parse_entry(p), p) == []


def test_check_index_ignores_keywords_md(tmp_path):
    # brain/KEYWORDS.md is generated (like INDEX.md) — never flagged as
    # missing an index line.
    brain = tmp_path / "brain"
    write(brain / "ml-stack" / "example.md", VALID)
    write(brain / "KEYWORDS.md", "# Keyword → entry map\nk → ml-stack/example.md\n")
    write(brain / "INDEX.md",
          "- [Example fix entry](ml-stack/example.md) — fix · JP 6.1 · example\n")
    assert check_index(brain) == []


def test_real_brain_passes_with_key_floor():
    # Every committed entry must carry ≥2 keys (verbatim + symptom phrase).
    brain = Path(__file__).resolve().parent.parent / "brain"
    assert main([str(brain)]) == 0
    entries = [p for p in brain.rglob("*.md")
               if p.name not in ("INDEX.md", "KEYWORDS.md")]
    assert len(entries) == 39
    for p in entries:
        assert len(parse_entry(p)["keys"]) >= 2, p


def test_index_missing_entry_fails(tmp_path):
    brain = tmp_path / "brain"
    write(brain / "ml-stack" / "example.md", VALID)
    write(brain / "INDEX.md", "# Index\n")  # no line for example.md
    errs = check_index(brain)
    assert any("example.md" in e for e in errs)


def test_index_dead_link_fails(tmp_path):
    brain = tmp_path / "brain"
    write(brain / "INDEX.md",
          "- [Ghost](ml-stack/ghost.md) — fix · JP 6.x · gone\n")
    errs = check_index(brain)
    assert any("ghost.md" in e for e in errs)


def test_index_ignores_links_in_code_spans(tmp_path):
    brain = tmp_path / "brain"
    write(brain / "ml-stack" / "example.md", VALID)
    write(brain / "INDEX.md",
          "Format: `- [title](domain/slug.md) — type · JP range · hook`\n"
          "- [Example fix entry](ml-stack/example.md) — fix · JP 6.1 · example\n")
    assert check_index(brain) == []


def test_main_on_valid_brain(tmp_path):
    brain = tmp_path / "brain"
    write(brain / "ml-stack" / "example.md", VALID)
    write(brain / "INDEX.md",
          "- [Example fix entry](ml-stack/example.md) — fix · JP 6.1 · example\n")
    assert main([str(brain)]) == 0


def test_main_on_invalid_brain(tmp_path):
    brain = tmp_path / "brain"
    write(brain / "ml-stack" / "bad.md", VALID.replace("type: fix", "type: banana"))
    write(brain / "INDEX.md",
          "- [Example fix entry](ml-stack/bad.md) — fix · JP 6.1 · example\n")
    assert main([str(brain)]) == 1
