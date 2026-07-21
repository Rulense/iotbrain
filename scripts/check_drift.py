# scripts/check_drift.py
"""Report vendored upstreams whose default-branch HEAD moved from our pin.

ATTRIBUTION.md is the machine-read source of truth: each vendored upstream is
a `## <name>` section carrying `- **Upstream repository:** https://github.com/
<owner>/<repo>` and `- **Pinned commit:** \\`<sha>\\`` bullets (keep that exact
bullet format when adding upstreams). For every pin this script asks the
GitHub API (unauthenticated or with GITHUB_TOKEN) for the default branch's
HEAD sha and reports upstreams where HEAD != pin.

Streams: report lines on stdout, per-upstream resolution warnings on stderr.
Exit code is always 0 — the report is advisory; CI turns a non-empty report
into a tracking issue (see .github/workflows/freshness.yml).

Usage:
  python3 scripts/check_drift.py                       # live (network)
  python3 scripts/check_drift.py --input fixture.json  # offline fixtures

Fixture format (--input): {"pins": [{"name": ..., "repo": "owner/repo",
"commit": "<sha>"}, ...], "heads": {"owner/repo": "<sha>" | null, ...}} —
null marks an unreachable upstream. Stdlib only.
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

GITHUB_API = "https://api.github.com"
SECTION_RE = re.compile(r"^## +(.+?) *$", re.MULTILINE)
REPO_RE = re.compile(r"\*\*Upstream repository:\*\*\s*<?https://github\.com/([\w.-]+/[\w.-]+?)/?>?\s*$", re.MULTILINE)
COMMIT_RE = re.compile(r"\*\*Pinned commit:\*\*\s*`([0-9a-fA-F]{7,40})`")


def parse_attribution(text: str) -> "list[dict]":
    """Pins from ATTRIBUTION.md: [{'name', 'repo', 'commit'}, ...].
    A section yields a pin only when it has BOTH the repository and the
    pinned-commit bullet (prose sections are skipped)."""
    pins = []
    matches = list(SECTION_RE.finditer(text))
    for i, m in enumerate(matches):
        body = text[m.end():matches[i + 1].start() if i + 1 < len(matches) else len(text)]
        repo = REPO_RE.search(body)
        commit = COMMIT_RE.search(body)
        if repo and commit:
            pins.append({"name": m.group(1).strip(),
                         "repo": repo.group(1),
                         "commit": commit.group(1).lower()})
    return pins


def github_json(url: str, token: "str | None" = None, timeout: int = 20):
    """GET a GitHub API URL, parsed JSON. Raises on any failure."""
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "iotbrain-drift"}
    if token:
        headers["Authorization"] = "Bearer %s" % token
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def resolve_head(repo: str, token: "str | None" = None) -> "str | None":
    """Default-branch HEAD sha for owner/repo, None on any failure."""
    try:
        meta = github_json("%s/repos/%s" % (GITHUB_API, repo), token)
        branch = meta.get("default_branch") or "main"
        commit = github_json("%s/repos/%s/commits/%s" % (GITHUB_API, repo, branch), token)
        return (commit.get("sha") or "").lower() or None
    except (urllib.error.URLError, OSError, ValueError, KeyError):
        return None


def build_report(pins: "list[dict]", heads: "dict[str, str | None]") -> "list[str]":
    """One line per upstream whose HEAD moved from the pin. Unresolvable
    upstreams warn on stderr and are tolerated."""
    lines = []
    for pin in pins:
        repo, pinned = pin["repo"], pin["commit"].lower()
        head = heads.get(repo)
        if not head:
            print("warning: %s: could not resolve default-branch HEAD — "
                  "skipping" % repo, file=sys.stderr)
            continue
        head = head.lower()
        # Tolerate short pins: match on the shorter prefix.
        n = min(len(head), len(pinned))
        if head[:n] != pinned[:n]:
            lines.append("%s (%s): upstream HEAD %s moved from pinned %s"
                         % (repo, pin["name"], head[:12], pinned[:12]))
    return lines


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=None,
                        help="fixture JSON (offline): {'pins': [...], 'heads': {...}}")
    parser.add_argument("--repo-root", default=None,
                        help="repo root (default: parent of scripts/)")
    args = parser.parse_args(argv)
    repo_root = (Path(args.repo_root) if args.repo_root
                 else Path(__file__).resolve().parent.parent)

    if args.input:
        fixture = json.loads(Path(args.input).read_text(encoding="utf-8"))
        pins = fixture.get("pins") or []
        heads = fixture.get("heads") or {}
    else:
        text = (repo_root / "ATTRIBUTION.md").read_text(encoding="utf-8")
        pins = parse_attribution(text)
        if not pins:
            print("warning: no pins parsed from ATTRIBUTION.md", file=sys.stderr)
        token = os.environ.get("GITHUB_TOKEN") or None
        heads = {pin["repo"]: resolve_head(pin["repo"], token) for pin in pins}

    for line in build_report(pins, heads):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
