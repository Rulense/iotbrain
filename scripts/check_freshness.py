# scripts/check_freshness.py
"""Report watched ecosystems whose latest release has no brain coverage.

Reads watchlist.json (repo root): one entry per watched ecosystem, each with a
source that resolves its latest version — "github-release" (GitHub API,
unauthenticated or with GITHUB_TOKEN) or "pinned" (maintainer-bumped, for
ecosystems with no reliable public API, e.g. JetPack). For every ecosystem it
compares the latest major.minor series against all `platform_versions` strings
in brain entries ("<Ecosystem> <range>", e.g. "JetPack 6.x", "ESP-IDF 5.3");
ecosystems whose latest series has ZERO covering entries land in the report.

Streams: report lines on stdout, per-entry resolution warnings on stderr.
Exit code is always 0 — the report is advisory; CI turns a non-empty report
into a tracking issue (see .github/workflows/freshness.yml).

Usage:
  python3 scripts/check_freshness.py                     # live (network)
  python3 scripts/check_freshness.py --input fixture.json  # offline fixtures

Fixture format (--input): {"latest": {"<ecosystem>": "<version>" | null, ...},
"platform_versions": ["JetPack 6.x", ...]} — null marks a failed source.
Stdlib + pyyaml only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

try:
    from scripts.lint_brain import LintError, parse_entry
except ImportError:
    from lint_brain import LintError, parse_entry

GITHUB_API = "https://api.github.com"
NON_ENTRY_FILES = {"INDEX.md", "KEYWORDS.md"}
VERSION_RE = re.compile(r"v?(\d+)(?:\.(\d+))?", re.IGNORECASE)


def github_json(url: str, token: "str | None" = None, timeout: int = 20):
    """GET a GitHub API URL, parsed JSON. Raises on any failure."""
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "iotbrain-freshness"}
    if token:
        headers["Authorization"] = "Bearer %s" % token
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def resolve_latest(source: dict, token: "str | None" = None) -> "str | None":
    """Latest version string for one watchlist source, None on failure.
    Failures never raise — each entry is tolerated independently."""
    stype = source.get("type")
    if stype == "pinned":
        return source.get("latest") or None
    if stype == "github-release":
        repo = source.get("repo")
        if not repo:
            return None
        try:
            data = github_json("%s/repos/%s/releases/latest" % (GITHUB_API, repo), token)
            return data.get("tag_name") or None
        except (urllib.error.URLError, OSError, ValueError, KeyError):
            return None
    return None


def major_minor(version: str) -> "str | None":
    """'v5.5.1' -> '5.5', '7.0' -> '7.0', '7' -> '7.0'; None if unparseable."""
    m = VERSION_RE.search(str(version))
    if not m:
        return None
    return "%s.%s" % (m.group(1), m.group(2) or "0")


def spec_covers(spec: str, series: str) -> bool:
    """Does a platform_versions range spec cover a major.minor series?

    '6.x' covers 6.*, '6' covers 6.*, '6.1' covers exactly 6.1,
    '6.1.3' covers 6.1. A bare 'all' platform_versions string names no
    ecosystem and is never attributed to one (handled by the caller).
    """
    spec = spec.strip()
    major = series.split(".", 1)[0]
    if spec == series:
        return True
    if spec.lower() in ("%s.x" % major, major):
        return True
    return spec.startswith(series + ".")


def collect_platform_versions(brain_dir: Path) -> "list[str]":
    """Every platform_versions string across all brain entries."""
    versions: "list[str]" = []
    for path in sorted(brain_dir.rglob("*.md")):
        if path.name in NON_ENTRY_FILES:
            continue
        try:
            meta = parse_entry(path)
        except LintError as e:
            print("warning: skipping unparseable entry: %s" % e, file=sys.stderr)
            continue
        versions.extend(str(v) for v in meta.get("platform_versions") or [])
    return versions


def specs_for_ecosystem(platform_versions: "list[str]", ecosystem: str) -> "list[str]":
    """Range specs of the strings naming this ecosystem ('JetPack 6.x' -> '6.x')."""
    prefix = ecosystem.lower() + " "
    return [v[len(prefix):].strip() for v in platform_versions
            if v.lower().startswith(prefix)]


def build_report(latest: "dict[str, str | None]",
                 platform_versions: "list[str]") -> "list[str]":
    """One line per ecosystem whose latest major.minor has zero covering
    entries. Unresolvable ecosystems (None / unparseable) warn on stderr."""
    lines = []
    for ecosystem in sorted(latest):
        version = latest[ecosystem]
        if not version:
            print("warning: %s: could not resolve latest version (source "
                  "failed or unavailable) — skipping" % ecosystem, file=sys.stderr)
            continue
        series = major_minor(version)
        if not series:
            print("warning: %s: unparseable version %r — skipping"
                  % (ecosystem, version), file=sys.stderr)
            continue
        specs = specs_for_ecosystem(platform_versions, ecosystem)
        if not any(spec_covers(spec, series) for spec in specs):
            lines.append("%s: latest release %s (series %s) has no covering "
                         "brain entry (%d %s-scoped entries checked)"
                         % (ecosystem, version, series, len(specs), ecosystem))
    return lines


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=None,
                        help="fixture JSON (offline): {'latest': {...}, "
                             "'platform_versions': [...]}")
    parser.add_argument("--repo-root", default=None,
                        help="repo root (default: parent of scripts/)")
    args = parser.parse_args(argv)
    repo_root = (Path(args.repo_root) if args.repo_root
                 else Path(__file__).resolve().parent.parent)

    if args.input:
        fixture = json.loads(Path(args.input).read_text(encoding="utf-8"))
        latest = fixture.get("latest") or {}
        platform_versions = fixture.get("platform_versions")
        if platform_versions is None:
            platform_versions = collect_platform_versions(repo_root / "brain")
    else:
        watchlist_path = repo_root / "watchlist.json"
        watchlist = json.loads(watchlist_path.read_text(encoding="utf-8"))
        token = os.environ.get("GITHUB_TOKEN") or None
        latest = {entry["ecosystem"]: resolve_latest(entry.get("source") or {}, token)
                  for entry in watchlist.get("watchlist", [])}
        platform_versions = collect_platform_versions(repo_root / "brain")

    for line in build_report(latest, platform_versions):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
