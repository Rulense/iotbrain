# scripts/gen_updates.py
"""Generate website data: stats + Latest Additions.

Collects brain entries (brain/<domain>/*.md frontmatter) and skills
(skills/*/SKILL.md frontmatter), dates each row from git history
(first-add date), and writes:

  - updates.json                        — fetched by index.html at runtime
  - index.html fallback region          — the baked-in copy between the
    /*__IOTBRAIN_DATA_START__*/ ... /*__IOTBRAIN_DATA_END__*/ sentinels

Usage:
  python3 scripts/gen_updates.py            # regenerate both files in place
  python3 scripts/gen_updates.py --check    # exit 1 if either file is stale

Requires full git history for correct dates (CI: checkout fetch-depth: 0).
Stdlib + pyyaml only.
"""
from __future__ import annotations

import argparse
import datetime
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

try:  # imported as a package module (tests: from scripts.gen_updates import ...)
    from scripts.lint_brain import LintError, parse_entry
except ImportError:  # run directly: python3 scripts/gen_updates.py
    from lint_brain import LintError, parse_entry

# --- Skill → company map ------------------------------------------------------
# Company attribution for vendored skills. Skills named jetson-* — plus our own
# jetson-dev and brain-distill — are NVIDIA's; every OTHER vendored skill MUST
# have an explicit entry below. `gen_updates.py --check` (run in CI) fails and
# lists any skills/<name>/ directory that has no mapping, so add new vendored
# skills here when you vendor them.
OUR_SKILLS = {"jetson-dev", "brain-distill"}
VENDOR_COMPANY = {
    "ee-datasheet-master": "seeed",
    "schematic-analyzer": "seeed",
    "rdk-peripheral-cookbook": "d-robotics",
    "espdl-operator": "espressif",
    "espdl-quantize": "espressif",
    "devicetree": "zephyr",
    "hardware-io": "zephyr",
}

UPDATES_CAP = 60
TITLE_SENTENCE_LIMIT = 80
START_MARK = "/*__IOTBRAIN_DATA_START__*/"
END_MARK = "/*__IOTBRAIN_DATA_END__*/"


class UnmappedSkillError(Exception):
    """Raised when a skills/<name>/ dir has no company mapping."""


def skill_company(skill_dir: str) -> "str | None":
    if skill_dir.startswith("jetson-") or skill_dir in OUR_SKILLS:
        return "nvidia"
    return VENDOR_COMPANY.get(skill_dir)


def git_first_add_date(repo_root: Path, path: Path) -> str:
    """First-add date (YYYY-MM-DD) from git; today for not-yet-committed files."""
    rel = str(path.relative_to(repo_root))
    try:
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--follow",
             "--format=%ad", "--date=short", "-1", "--", rel],
            cwd=str(repo_root), capture_output=True, text=True, check=False,
        ).stdout.strip()
    except OSError:
        out = ""
    return out or datetime.date.today().isoformat()


def first_sentence(text: str, limit: int = TITLE_SENTENCE_LIMIT) -> str:
    """First sentence of a description, whitespace-collapsed, ~limit chars."""
    text = " ".join(str(text).split())
    sentence = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0].rstrip()
    if sentence.endswith("."):
        sentence = sentence[:-1]
    if len(sentence) > limit:
        sentence = sentence[:limit].rsplit(" ", 1)[0].rstrip(" ,;:·—-") + "…"
    return sentence


def parse_skill_meta(path: Path) -> dict:
    """Frontmatter of a SKILL.md. Prefers lint_brain.parse_entry; falls back to
    a line-based reader for vendored skills whose frontmatter is not strict
    YAML (we only need `name` and `description`)."""
    try:
        return parse_entry(path)
    except LintError:
        pass
    meta: dict = {}
    key = None
    buf: "list[str]" = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for line in lines[1:]:  # skip opening ---
        if line.strip() == "---":
            break
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            if key:
                meta[key] = " ".join(buf).strip()
            key = m.group(1)
            val = m.group(2).strip()
            buf = [] if val in ("|", ">", "|-", ">-", "|+", ">+") else [val]
        elif key:
            buf.append(line.strip())
    if key:
        meta[key] = " ".join(buf).strip()
    for k, v in meta.items():
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
            meta[k] = v[1:-1]
    return meta


def collect_entries(repo_root: Path) -> "list[dict]":
    """One row per brain entry: title/type/domain/company/date."""
    brain = repo_root / "brain"
    rows = []
    for path in sorted(brain.rglob("*.md")):
        if path.name == "INDEX.md":
            continue
        meta = parse_entry(path)
        rows.append({
            "title": str(meta.get("title", path.stem)),
            "type": str(meta.get("type", "")),
            "domain": path.relative_to(brain).parts[0],
            "company": str(meta.get("company", "")),
            "date": git_first_add_date(repo_root, path),
        })
    return rows


def collect_skills(repo_root: Path) -> "list[dict]":
    """One row per skills/*/SKILL.md; raises UnmappedSkillError if any skill
    directory is missing from the company map."""
    rows = []
    unmapped = []
    for path in sorted((repo_root / "skills").glob("*/SKILL.md")):
        skill_dir = path.parent.name
        company = skill_company(skill_dir)
        if company is None:
            unmapped.append(skill_dir)
            continue
        meta = parse_skill_meta(path)
        name = str(meta.get("name", skill_dir))
        rows.append({
            "title": "%s — %s" % (name, first_sentence(meta.get("description", ""))),
            "type": "skill",
            "domain": "skills",
            "company": company,
            "date": git_first_add_date(repo_root, path),
        })
    if unmapped:
        raise UnmappedSkillError(", ".join(sorted(unmapped)))
    return rows


def build_stats(entries: "list[dict]", skills: "list[dict]") -> dict:
    companies = set()
    for row in entries + skills:
        company = row.get("company")
        if isinstance(company, list):
            companies.update(str(c) for c in company)
        elif company:
            companies.add(str(company))
    return {
        "entries": len(entries),
        "skills": len(skills),
        "domains": len({row["domain"] for row in entries}),
        "platforms": len(companies),
    }


def build_updates(entries: "list[dict]", skills: "list[dict]",
                  cap: int = UPDATES_CAP) -> "list[dict]":
    """All rows, newest date first, tie-break alphabetical by title; capped."""
    rows = sorted(entries + skills, key=lambda r: r["title"])
    rows.sort(key=lambda r: r["date"], reverse=True)
    return rows[:cap]


def render_json(data: dict) -> str:
    """updates.json text: stats on one line, one update row per line."""
    stats = json.dumps(data["stats"], ensure_ascii=False)
    rows = ",\n".join(
        "    " + json.dumps(row, ensure_ascii=False) for row in data["updates"]
    )
    return '{\n  "stats": %s,\n  "updates": [\n%s\n  ]\n}\n' % (stats, rows)


def patch_index_html(html: str, data: dict) -> str:
    """Replace the baked fallback between the sentinel comments.

    The payload is json.dumps output, which is a valid JS object literal."""
    if START_MARK not in html or END_MARK not in html:
        raise RuntimeError(
            "index.html: sentinel markers %s / %s not found" % (START_MARK, END_MARK))
    head, rest = html.split(START_MARK, 1)
    _, tail = rest.split(END_MARK, 1)
    body = render_json(data).rstrip("\n").replace("\n", "\n  ")
    region = "\n  const FALLBACK = %s;\n  " % body
    return head + START_MARK + region + END_MARK + tail


def _diff_summary(name: str, old: str, new: str, max_lines: int = 20) -> str:
    diff = list(difflib.unified_diff(
        old.splitlines(), new.splitlines(),
        fromfile="%s (committed)" % name, tofile="%s (regenerated)" % name,
        lineterm=""))
    shown = diff[:max_lines]
    if len(diff) > max_lines:
        shown.append("... (%d more diff lines)" % (len(diff) - max_lines))
    return "\n".join(shown)


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if updates.json or the index.html fallback is stale")
    parser.add_argument("--repo-root", default=None,
                        help="repo root (default: parent of scripts/)")
    args = parser.parse_args(argv)
    repo_root = (Path(args.repo_root) if args.repo_root
                 else Path(__file__).resolve().parent.parent)

    try:
        entries = collect_entries(repo_root)
        skills = collect_skills(repo_root)
    except UnmappedSkillError as e:
        print("error: skills with no company mapping: %s" % e, file=sys.stderr)
        print("add them to VENDOR_COMPANY in scripts/gen_updates.py", file=sys.stderr)
        return 1

    data = {"stats": build_stats(entries, skills),
            "updates": build_updates(entries, skills)}

    updates_path = repo_root / "updates.json"
    index_path = repo_root / "index.html"
    new_json = render_json(data)
    old_html = index_path.read_text(encoding="utf-8")
    try:
        new_html = patch_index_html(old_html, data)
    except RuntimeError as e:
        print("error: %s" % e, file=sys.stderr)
        return 1

    if args.check:
        old_json = updates_path.read_text(encoding="utf-8") if updates_path.exists() else ""
        stale = []
        if old_json != new_json:
            stale.append(_diff_summary("updates.json", old_json, new_json))
        if old_html != new_html:
            stale.append(_diff_summary("index.html", old_html, new_html))
        if stale:
            print("stale generated data — run: python3 scripts/gen_updates.py")
            for block in stale:
                print(block)
            return 1
        return 0

    updates_path.write_text(new_json, encoding="utf-8")
    index_path.write_text(new_html, encoding="utf-8")
    print("wrote %s and patched %s (%d entries, %d skills, %d update rows)" % (
        updates_path, index_path, data["stats"]["entries"],
        data["stats"]["skills"], len(data["updates"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
