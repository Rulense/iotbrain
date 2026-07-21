# tests/test_init_overlay.py
import subprocess
import sys
from pathlib import Path

from scripts.init_overlay import DOMAINS, init_overlay, main

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "init_overlay.py"


def test_fresh_create_makes_all_dirs_and_files(tmp_path):
    root = tmp_path / "local"
    results = init_overlay(root)
    assert set(DOMAINS) == {"setup", "ml-stack", "vision", "iot", "sdk-dev", "runtime"}
    for domain in DOMAINS:
        assert (root / domain).is_dir()
    assert (root / "README.md").is_file()
    assert (root / "_template.md").is_file()
    assert all(status == "created" for status, _ in results)
    # root + 6 domains + README + template
    assert len(results) == 9


def test_idempotent_rerun_never_clobbers_user_edits(tmp_path):
    root = tmp_path / "local"
    init_overlay(root)
    (root / "README.md").write_text("my custom notes\n", encoding="utf-8")
    (root / "_template.md").write_text("my custom template\n", encoding="utf-8")
    (root / "setup" / "my-entry.md").write_text("entry\n", encoding="utf-8")

    results = init_overlay(root)

    assert all(status == "skipped" for status, _ in results)
    assert (root / "README.md").read_text(encoding="utf-8") == "my custom notes\n"
    assert (root / "_template.md").read_text(encoding="utf-8") == "my custom template\n"
    assert (root / "setup" / "my-entry.md").read_text(encoding="utf-8") == "entry\n"


def test_template_matches_contributing_entry_template(tmp_path):
    root = tmp_path / "local"
    init_overlay(root)
    template = (root / "_template.md").read_text(encoding="utf-8")
    assert "platform_versions" in template
    assert "reproduced_by" in template
    assert "CONTRIBUTING.md" in template  # sync-source note
    # frontmatter fields stay aligned with the CONTRIBUTING.md template
    contributing = (REPO_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    for field in ("title:", "type:", "company:", "keys:", "platform_versions:",
                  "devices:", "status:", "verified_on:", "reproduced_by:", "sources:"):
        assert field in template
        assert field in contributing


def test_readme_created_with_overlay_explanation(tmp_path):
    root = tmp_path / "local"
    init_overlay(root)
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "overlay" in readme.lower()
    assert "brain-distill" in readme
    assert "never pushed" in readme.lower() or "ever pushed" in readme.lower()


def test_cli_custom_path_prints_created_then_skipped(tmp_path):
    root = tmp_path / "custom-overlay"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(root)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert (root / "runtime").is_dir()
    assert proc.stdout.count("created") == 9

    proc2 = subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(root)],
        capture_output=True, text=True,
    )
    assert proc2.returncode == 0
    assert proc2.stdout.count("skipped") == 9
    assert "created" not in proc2.stdout


def test_main_returns_zero(tmp_path, capsys):
    root = tmp_path / "local"
    assert main(["--path", str(root)]) == 0
    out = capsys.readouterr().out
    assert "created" in out
