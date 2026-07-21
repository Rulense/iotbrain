# scripts/lint_brain.py
"""Lint iotbrain brain entries: frontmatter schema + INDEX.md consistency.

Usage: python3 scripts/lint_brain.py <brain-dir>
Exit 0 when clean, 1 with one error per line otherwise.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

DOMAINS = {"setup", "ml-stack", "vision", "iot", "sdk-dev", "runtime"}
TYPES = {"recipe", "config", "matrix", "gotcha", "fix"}
STATUSES = {"verified", "unverified", "outdated"}
LIST_FIELDS = ("keys", "platform_versions", "devices", "sources", "reproduced_by")
REQUIRED = ("title", "type", "keys", "company", "platform_versions", "devices", "status", "sources")
INDEX_LINK = re.compile(r"\]\(([^)]+\.md)\)")
# Every entry needs BOTH verbatim machine strings AND at least one
# plain-language symptom phrase (see CONTRIBUTING.md), so the floor is 2.
MIN_KEYS = 2
# Generated / structural files in brain/ that are not entries.
NON_ENTRY_FILES = {"INDEX.md", "KEYWORDS.md"}


class LintError(Exception):
    pass


def parse_entry(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise LintError(f"{path}: missing frontmatter")
    try:
        _, fm, _ = text.split("---\n", 2)
    except ValueError:
        raise LintError(f"{path}: unterminated frontmatter")
    try:
        meta = yaml.safe_load(fm)
    except yaml.YAMLError as e:
        raise LintError(f"{path}: bad YAML frontmatter: {e}")
    if not isinstance(meta, dict):
        raise LintError(f"{path}: frontmatter is not a mapping")
    return meta


def validate_entry(meta: dict, path: Path) -> list[str]:
    errs = []
    for field in REQUIRED:
        if field not in meta or meta[field] in (None, ""):
            errs.append(f"{path}: missing required field '{field}'")
    if meta.get("type") not in TYPES:
        errs.append(f"{path}: invalid type '{meta.get('type')}' (must be one of {sorted(TYPES)})")
    if meta.get("status") not in STATUSES:
        errs.append(f"{path}: invalid status '{meta.get('status')}' (must be one of {sorted(STATUSES)})")
    if meta.get("status") == "verified" and not meta.get("verified_on"):
        errs.append(f"{path}: status 'verified' requires 'verified_on'")
    for field in LIST_FIELDS:
        val = meta.get(field)
        if field in meta and (not isinstance(val, list) or len(val) == 0):
            errs.append(f"{path}: '{field}' must be a non-empty list")
    keys = meta.get("keys")
    if isinstance(keys, list) and 0 < len(keys) < MIN_KEYS:
        errs.append(
            f"{path}: 'keys' needs at least {MIN_KEYS} items — verbatim machine "
            f"strings plus at least one plain-language symptom phrase")
    return errs


def check_index(brain_dir: Path) -> list[str]:
    errs = []
    index = brain_dir / "INDEX.md"
    if not index.exists():
        return [f"{index}: INDEX.md missing"]
    # Ignore links inside inline code spans (e.g. the format example in the header).
    text = re.sub(r"`[^`\n]*`", "", index.read_text(encoding="utf-8"))
    indexed = set(INDEX_LINK.findall(text))
    actual = {
        str(p.relative_to(brain_dir))
        for p in brain_dir.rglob("*.md")
        if p.name not in NON_ENTRY_FILES
    }
    for missing in sorted(actual - indexed):
        errs.append(f"{index}: no index line for {missing}")
    for dead in sorted(indexed - actual):
        errs.append(f"{index}: dead link to {dead}")
    return errs


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 1
    brain_dir = Path(argv[0])
    errs: list[str] = []
    for p in sorted(brain_dir.rglob("*.md")):
        if p.name in NON_ENTRY_FILES:
            continue
        domain = p.relative_to(brain_dir).parts[0]
        if domain not in DOMAINS:
            errs.append(f"{p}: not in a known domain dir {sorted(DOMAINS)}")
        try:
            errs.extend(validate_entry(parse_entry(p), p))
        except LintError as e:
            errs.append(str(e))
    errs.extend(check_index(brain_dir))
    for e in errs:
        print(e)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
