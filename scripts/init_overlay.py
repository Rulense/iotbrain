#!/usr/bin/env python3
"""Idempotently initialize the private iotbrain overlay at ~/.iotbrain/local/.

Creates the six domain directories, a README.md explaining the overlay, and
_template.md (the CONTRIBUTING.md entry template). Existing files and
directories are never clobbered — re-running is always safe. Prints one line
per item: created or skipped.

Usage:
  python3 scripts/init_overlay.py                 # ~/.iotbrain/local/
  python3 scripts/init_overlay.py --path <dir>    # custom root (tests)

Stdlib only.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

DOMAINS = ("setup", "ml-stack", "vision", "iot", "sdk-dev", "runtime")

README_CONTENT = """\
# iotbrain local overlay

This is your PRIVATE knowledge overlay. The `iot-dev` skill consults it right
beside the shared brain on every task, and the `brain-distill` skill saves
newly verified learnings here first.

- **Private.** Nothing here is ever pushed or published automatically.
- **Consulted.** Entries here are grepped alongside the shared brain
  (`brain/` in the iotbrain plugin) and filtered by the same
  company/platform-version applicability rules.
- **Contributable later.** Any entry can be promoted to the public iotbrain
  repo via the `brain-distill` skill — only with your explicit approval of
  the exact content.

One markdown file per entry, in the matching domain directory
(`setup/`, `ml-stack/`, `vision/`, `iot/`, `sdk-dev/`, `runtime/`).
Start from `_template.md`.
"""

# Entry template copied from CONTRIBUTING.md ("Entry template" section).
# Keep in sync manually with that source when the template changes.
TEMPLATE_CONTENT = """\
<!-- Copied from CONTRIBUTING.md "Entry template" — keep in sync manually
     with that source. Fill every field; pick ONE type. -->
---
title: <one line, specific, includes key terms>
type: recipe | config | matrix | gotcha | fix     # pick ONE
company: nvidia             # device vendor: nvidia | raspberry-pi | qualcomm | nxp | ...
keys:                       # verbatim grep targets — error strings, package names, element names
  - "<exact string an agent would search for>"
platform_versions: ["JetPack 6.1", "L4T 36.x"]   # platform/SDK version scope, or ["all"]
devices: [orin-nano]        # orin-nano | orin-nx | agx-orin | xavier-nx | agx-xavier | nano | agx-thor | all
status: verified | unverified | outdated
verified_on: "<device>, JetPack <ver>, <YYYY-MM-DD>"   # required when status: verified
reproduced_by: ["<who/context>, <device>, <version>, <YYYY-MM-DD>"]   # optional second confirmations
sources: ["https://..."]    # forum threads, docs, release notes
---
## Context
When this applies / what you were trying to do.

## Knowledge
The recipe steps / working config / version matrix / trap / root cause and fix.
Exact commands. For a `fix`, use subheadings "Root cause" and "Fix".

## Verify
How to confirm it worked (or still holds).

## Gotchas
Near-miss variants, what makes it recur. (Optional but encouraged.)
"""


def init_overlay(root: Path) -> "list[tuple[str, str]]":
    """Create the overlay under `root`. Returns (status, relative-path) pairs,
    status in {"created", "skipped"}. Never overwrites existing files."""
    results = []
    dirs = [root] + [root / d for d in DOMAINS]
    for d in dirs:
        if d.is_dir():
            results.append(("skipped", str(d)))
        else:
            d.mkdir(parents=True, exist_ok=True)
            results.append(("created", str(d)))
    for name, content in (("README.md", README_CONTENT),
                          ("_template.md", TEMPLATE_CONTENT)):
        path = root / name
        if path.exists():
            results.append(("skipped", str(path)))
        else:
            path.write_text(content, encoding="utf-8")
            results.append(("created", str(path)))
    return results


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", default=None,
                        help="overlay root (default: ~/.iotbrain/local)")
    args = parser.parse_args(argv)
    root = Path(args.path).expanduser() if args.path else Path.home() / ".iotbrain" / "local"
    for status, path in init_overlay(root):
        print("%s  %s" % (status, path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
