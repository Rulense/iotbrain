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
    jetpack: ["6.1"]
    l4t: ["36.x"]
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


def test_verified_requires_verified_on(tmp_path):
    text = VALID.replace('verified_on: "Orin Nano, JetPack 6.1, 2026-07-01"\n', "")
    p = write(tmp_path / "brain" / "ml-stack" / "bad.md", text)
    errs = validate_entry(parse_entry(p), p)
    assert any("verified_on" in e for e in errs)


def test_empty_keys_fails(tmp_path):
    text = VALID.replace('keys:\n  - "ImportError: libexample.so.1"', "keys: []")
    p = write(tmp_path / "brain" / "ml-stack" / "bad.md", text)
    errs = validate_entry(parse_entry(p), p)
    assert any("keys" in e for e in errs)


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
