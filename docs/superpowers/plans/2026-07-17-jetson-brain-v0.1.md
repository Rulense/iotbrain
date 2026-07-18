# Jetson Brain v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Jetson Brain v0.1 Claude Code plugin — jetson-dev + brain-distill skills, a seeded six-domain markdown knowledge base with grep retrieval, CONTRIBUTING spec, CI lint, test scenarios, and the landing page.

**Architecture:** One repo is both the Claude Code plugin and the brain. Skills are markdown instruction files (no runtime code); the brain is one markdown file per entry with YAML frontmatter, mapped by `brain/INDEX.md`. The only executable code is a Python lint script (frontmatter schema + INDEX consistency) run by pytest locally and GitHub Actions on PRs.

**Tech Stack:** Markdown, YAML frontmatter, Python 3 + PyYAML + pytest (lint only), GitHub Actions, Claude Code plugin format.

## Global Constraints

- Brain domains (exact directory names): `setup`, `ml-stack`, `vision`, `iot`, `sdk-dev`, `runtime`
- Entry types (exact enum): `recipe`, `config`, `matrix`, `gotcha`, `fix`
- Entry status (exact enum): `verified`, `unverified`, `outdated`; `verified_on` is required when status is `verified`
- Required frontmatter fields for every entry: `title`, `type`, `keys` (non-empty list), `jetpack` (list), `l4t` (list), `devices` (list), `status`, `sources` (list)
- Skill names (exact): `jetson-dev`, `brain-distill`
- Local overlay path (exact): `~/.jetson-brain/local/` mirroring the `brain/` domain structure
- brain-distill NEVER opens a PR, pushes, or publishes without showing the user the exact entry content and receiving explicit approval
- All brain content must be public-safe: no internal NVIDIA info, no secrets, no private paths/hostnames
- INDEX.md line format (exact): `- [<title>](<domain>/<slug>.md) — <type> · JP <range> · <one-hook summary>`
- Lint: `python3 scripts/lint_brain.py brain` exits 0 on success, 1 with per-file error lines on failure
- Commit after every task; commit messages end with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task 1: Plugin manifest

**Files:**
- Create: `.claude-plugin/plugin.json`

**Interfaces:**
- Produces: valid plugin manifest; Claude Code auto-discovers `skills/*/SKILL.md` relative to repo root.

- [ ] **Step 1: Create the manifest**

```json
{
  "name": "jetson-brain",
  "version": "0.1.0",
  "description": "The collective brain for NVIDIA Jetson development — skills plus a community-grown, grep-able knowledge base of recipes, configs, version matrices, gotchas, and fixes.",
  "author": { "name": "Jetson Brain community" }
}
```

Save as `.claude-plugin/plugin.json`.

- [ ] **Step 2: Validate JSON**

Run: `python3 -m json.tool .claude-plugin/plugin.json`
Expected: pretty-printed JSON, exit 0.

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "feat: add Claude Code plugin manifest"
```

---

### Task 2: Brain lint script (TDD)

**Files:**
- Create: `scripts/lint_brain.py`
- Test: `tests/test_lint_brain.py`
- Create: `requirements-dev.txt`

**Interfaces:**
- Produces: `parse_entry(path: Path) -> dict` (returns frontmatter dict; raises `LintError` on missing/unparseable frontmatter), `validate_entry(meta: dict, path: Path) -> list[str]` (returns error strings, empty = valid), `check_index(brain_dir: Path) -> list[str]`, `main(argv) -> int` (0 ok / 1 errors). Tasks 4 and 7–12 run this script; Task 13's CI workflow calls it.

- [ ] **Step 1: Create requirements-dev.txt**

```
pyyaml>=6.0
pytest>=8.0
```

- [ ] **Step 2: Install dev deps**

Run: `python3 -m pip install -r requirements-dev.txt`
Expected: exit 0.

- [ ] **Step 3: Write the failing tests**

```python
# tests/test_lint_brain.py
from pathlib import Path
import textwrap
import pytest

from scripts.lint_brain import LintError, parse_entry, validate_entry, check_index, main

VALID = textwrap.dedent("""\
    ---
    title: Example fix entry
    type: fix
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
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_lint_brain.py -v`
Expected: FAIL/ERROR with `ModuleNotFoundError: No module named 'scripts'` (or import error).

- [ ] **Step 5: Implement the lint script**

```python
# scripts/lint_brain.py
"""Lint Jetson Brain entries: frontmatter schema + INDEX.md consistency.

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
LIST_FIELDS = ("keys", "jetpack", "l4t", "devices", "sources")
REQUIRED = ("title", "type", "keys", "jetpack", "l4t", "devices", "status", "sources")
INDEX_LINK = re.compile(r"\]\(([^)]+\.md)\)")


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
    return errs


def check_index(brain_dir: Path) -> list[str]:
    errs = []
    index = brain_dir / "INDEX.md"
    if not index.exists():
        return [f"{index}: INDEX.md missing"]
    indexed = set(INDEX_LINK.findall(index.read_text(encoding="utf-8")))
    actual = {
        str(p.relative_to(brain_dir))
        for p in brain_dir.rglob("*.md")
        if p.name != "INDEX.md"
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
        if p.name == "INDEX.md":
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
```

Also create empty `scripts/__init__.py` and `tests/__init__.py` so pytest imports resolve:

```bash
touch scripts/__init__.py tests/__init__.py
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_lint_brain.py -v`
Expected: 9 passed.

- [ ] **Step 7: Commit**

```bash
git add scripts/ tests/ requirements-dev.txt
git commit -m "feat: add brain lint script with frontmatter and INDEX checks"
```

---

### Task 3: CONTRIBUTING.md — entry format spec and verification bar

**Files:**
- Create: `CONTRIBUTING.md`

**Interfaces:**
- Produces: the canonical entry template; Tasks 4–12 and both skills copy this format exactly.

- [ ] **Step 1: Write CONTRIBUTING.md**

````markdown
# Contributing to Jetson Brain

The brain only gets smarter if verified knowledge flows back. Two ways to contribute: let the `brain-distill` skill draft an entry + PR for you, or write one by hand using the template below.

## Entry template

One markdown file per entry, in the matching domain directory
(`setup/`, `ml-stack/`, `vision/`, `iot/`, `sdk-dev/`, `runtime/`).
Filename: short kebab-case slug, e.g. `pytorch-wheel-libcudnn-import-error.md`.

```markdown
---
title: <one line, specific, includes key terms>
type: recipe | config | matrix | gotcha | fix     # pick ONE
keys:                       # verbatim grep targets — error strings, package names, element names
  - "<exact string an agent would search for>"
jetpack: ["6.1"]            # applicable JetPack versions, or ["all"]
l4t: ["36.x"]               # applicable L4T versions, or ["all"]
devices: [orin-nano]        # orin-nano | orin-nx | agx-orin | xavier-nx | agx-xavier | nano | agx-thor | all
status: verified | unverified | outdated
verified_on: "<device>, JetPack <ver>, <YYYY-MM-DD>"   # required when status: verified
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
```

After adding an entry, add one line to `brain/INDEX.md`:

```
- [<title>](<domain>/<slug>.md) — <type> · JP <range> · <one-hook summary>
```

## The verification bar

A PR is mergeable when the entry:

1. **Worked on real hardware** — `status: verified` means you (or the cited thread's author, confirmed resolved) ran it on a physical Jetson. Otherwise use `status: unverified`.
2. **Has verbatim keys** — copy-paste the exact error text / package / element names. Paraphrased keys break grep retrieval.
3. **Is version-scoped** — `jetpack`, `l4t`, `devices` filled honestly. "Works everywhere" claims need `["all"]` and a reason in Context.
4. **Cites sources** — forum thread, GitHub issue, doc page, or "verified locally" plus your `verified_on`.
5. **Is public-safe** — no internal info, secrets, private paths, hostnames, or proprietary code.

## PR checklist

- [ ] `python3 scripts/lint_brain.py brain` passes locally
- [ ] Entry is in the correct domain directory
- [ ] INDEX.md line added
- [ ] Keys are verbatim, not paraphrased
- [ ] Sources linked

CI runs the same lint on every PR.
````

- [ ] **Step 2: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs: add contributing guide with entry template and verification bar"
```

---

### Task 4: Brain scaffold, INDEX.md, and three exemplar entries

**Files:**
- Create: `brain/INDEX.md`, `brain/setup/.gitkeep`, `brain/vision/.gitkeep`, `brain/iot/.gitkeep`, `brain/sdk-dev/.gitkeep`
- Create: `brain/ml-stack/pytorch-wheel-libcudnn-import-error.md`
- Create: `brain/ml-stack/pytorch-jetpack6-working-wheels.md`
- Create: `brain/runtime/default-power-mode-caps-performance.md`

**Interfaces:**
- Consumes: entry template from Task 3; lint from Task 2.
- Produces: the three exemplar entries used by test scenarios (Task 12) and referenced as format examples by the skills (Tasks 5–6).

- [ ] **Step 1: Create the exemplar `fix` entry**

````markdown
---
title: "ImportError: libcudnn.so after pip-installing PyTorch on Jetson"
type: fix
keys:
  - "ImportError: libcudnn.so.8: cannot open shared object file"
  - "ImportError: libcudnn.so.9: cannot open shared object file"
  - "pip install torch"
jetpack: ["5.x", "6.x"]
l4t: ["35.x", "36.x"]
devices: [all]
status: verified
verified_on: "AGX Orin, JetPack 6.1, 2026-07-17"
sources: ["https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048"]
---
## Context
You installed PyTorch on a Jetson with plain `pip install torch` (or a wheel built
for a different JetPack) and `import torch` fails with a cuDNN shared-object error —
or imports fine but `torch.cuda.is_available()` is False.

## Knowledge
### Root cause
Generic PyPI aarch64 wheels are CPU-only, and NVIDIA-built wheels are compiled
against the exact CUDA/cuDNN of one JetPack release. A wheel/JetPack mismatch
leaves torch looking for a libcudnn version that isn't on the device.

### Fix
1. Check your JetPack/L4T: `cat /etc/nv_tegra_release`
2. Uninstall the wrong wheel: `pip3 uninstall torch torchvision torchaudio`
3. Install the wheel built for YOUR JetPack from the "PyTorch for Jetson" index
   (see source thread; for JetPack 6/CUDA 12.6 use the jp6/cu126 pip index).
4. Ensure the JetPack ML runtime libs are present:
   `sudo apt install nvidia-jetpack` (or at minimum the cudnn/tensorrt components).

## Verify
`python3 -c "import torch; print(torch.__version__, torch.cuda.is_available())"`
prints a version and `True`.

## Gotchas
- torchvision must be version-paired with torch (pairing table in the source thread);
  mismatch raises `operator torchvision::nms does not exist`.
- A JetPack upgrade (e.g. 6.0 → 6.1) can silently re-break this — reinstall matching wheels.
````

Save as `brain/ml-stack/pytorch-wheel-libcudnn-import-error.md`.

- [ ] **Step 2: Create the exemplar `config` entry**

````markdown
---
title: Known-working PyTorch wheel source for JetPack 6.x (CUDA 12.6)
type: config
keys:
  - "pypi.jetson-ai-lab"
  - "torch jetpack 6"
  - "cu126"
jetpack: ["6.0", "6.1", "6.2"]
l4t: ["36.x"]
devices: [orin-nano, orin-nx, agx-orin]
status: verified
verified_on: "Orin Nano, JetPack 6.2, 2026-07-17"
sources:
  - "https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048"
  - "https://www.jetson-ai-lab.com/"
---
## Context
You need CUDA-enabled torch/torchvision/torchaudio on JetPack 6.x without
building from source.

## Knowledge
The Jetson AI Lab community index publishes wheels built for JetPack 6 / CUDA 12.6:

```bash
pip3 install torch torchvision torchaudio \
  --index-url https://pypi.jetson-ai-lab.dev/jp6/cu126
```

Wheels there are built per-JetPack-major — do not mix a jp6 wheel onto JetPack 5.

## Verify
`python3 -c "import torch; print(torch.cuda.is_available())"` → `True`.

## Gotchas
- If the index URL is unreachable, fall back to the wheel links in the
  "PyTorch for Jetson" forum thread (source above).
````

Save as `brain/ml-stack/pytorch-jetpack6-working-wheels.md`.

- [ ] **Step 3: Create the exemplar `gotcha` entry**

````markdown
---
title: Default power mode silently caps Jetson performance
type: gotcha
keys:
  - "nvpmodel"
  - "jetson_clocks"
  - "slow inference jetson"
jetpack: ["all"]
l4t: ["all"]
devices: [all]
status: verified
verified_on: "Orin Nano, JetPack 6.1, 2026-07-17"
sources: ["https://docs.nvidia.com/jetson/archives/r36.3/DeveloperGuide/SD/PlatformPowerAndPerformance.html"]
---
## Context
Any benchmark, inference, or build task on a freshly flashed Jetson. Results look
2–4x slower than published numbers.

## Knowledge
Jetsons ship in a conservative power mode with dynamic clock scaling. Before
measuring or comparing performance:

```bash
sudo nvpmodel -q          # show current mode
sudo nvpmodel -m 0        # highest-power mode on most boards (MAXN where available)
sudo jetson_clocks        # pin clocks to max for the current mode
```

Mode numbering differs per module — always check `nvpmodel -q` output rather than
assuming mode 0.

## Verify
`sudo nvpmodel -q` shows the intended mode; `tegrastats` shows clocks pinned.

## Gotchas
- `jetson_clocks` does not survive reboot.
- Higher modes need adequate power supply; undersized USB-C supplies cause
  over-current throttling warnings.
````

Save as `brain/runtime/default-power-mode-caps-performance.md`.

- [ ] **Step 4: Create INDEX.md and empty domain dirs**

```markdown
# Jetson Brain Index

One line per entry. Format: `- [title](domain/slug.md) — type · JP range · hook`

## ml-stack
- [ImportError: libcudnn.so after pip-installing PyTorch on Jetson](ml-stack/pytorch-wheel-libcudnn-import-error.md) — fix · JP 5.x–6.x · wheel/JetPack mismatch breaks import or CUDA
- [Known-working PyTorch wheel source for JetPack 6.x (CUDA 12.6)](ml-stack/pytorch-jetpack6-working-wheels.md) — config · JP 6.x · jp6/cu126 pip index, no source builds

## runtime
- [Default power mode silently caps Jetson performance](runtime/default-power-mode-caps-performance.md) — gotcha · JP all · nvpmodel + jetson_clocks before benchmarking
```

```bash
mkdir -p brain/setup brain/vision brain/iot brain/sdk-dev
touch brain/setup/.gitkeep brain/vision/.gitkeep brain/iot/.gitkeep brain/sdk-dev/.gitkeep
```

- [ ] **Step 5: Run lint**

Run: `python3 scripts/lint_brain.py brain`
Expected: exit 0, no output.

- [ ] **Step 6: Commit**

```bash
git add brain/
git commit -m "feat: scaffold brain with INDEX and three exemplar entries"
```

---

### Task 5: jetson-dev skill

**Files:**
- Create: `skills/jetson-dev/SKILL.md`

**Interfaces:**
- Consumes: brain layout (Task 4), entry format (Task 3).
- Produces: the companion skill; invokes `brain-distill` by name (Task 6).

- [ ] **Step 1: Write SKILL.md**

````markdown
---
name: jetson-dev
description: Use for ANY NVIDIA Jetson / JetPack / L4T / Tegra task — building, deploying, integrating, optimizing, or debugging on Jetson devices (Orin, Xavier, Nano, Thor families). Consults the Jetson Brain knowledge base before acting and distills verified new learnings back into it.
---

# Jetson Development Companion

You have the Jetson Brain: community-verified knowledge at `<skill-base-dir>/../../brain/`
(the plugin root's `brain/` directory — resolve it from this skill's base directory),
plus the user's private overlay at `~/.jetson-brain/local/`. Entry types: `recipe`
(how to accomplish a task), `config` (known-working setup), `matrix` (version
compatibility), `gotcha` (trap to avoid), `fix` (error → solution).

Follow these steps in order for every Jetson task.

## Step 1 — Collect device facts FIRST

Determine where you are running:
- On the Jetson itself: `uname -m` is `aarch64` AND `/etc/nv_tegra_release` exists.
- On a host: ask the user for SSH access details if not already known, run the
  same commands over `ssh`.

Collect (never skip):
```bash
cat /etc/nv_tegra_release                 # L4T version
dpkg-query -W nvidia-l4t-core 2>/dev/null # L4T package version
cat /proc/device-tree/model               # device model
```
Map L4T → JetPack (36.x → JetPack 6, 35.x → JetPack 5). If the device is
unreachable, ask the user for JetPack version and device model before proceeding.

## Step 2 — Consult the brain

1. Read `brain/INDEX.md` — scan for entries matching the task.
2. Grep both stores for task keywords, package names, and (when debugging)
   VERBATIM error strings:
```bash
grep -ril "<verbatim error or keyword>" <plugin-root>/brain/ ~/.jetson-brain/local/ 2>/dev/null
```
3. Read every hit's full entry before acting.

## Step 3 — Filter by applicability

- Entry's `jetpack`/`devices` match the device facts → trust it; apply as written.
- Version or device mismatch → treat as a LEAD: tell the user "the brain has a
  possibly-relevant entry for JetPack X, verifying it applies here", and verify
  before applying.
- `status: outdated` → only relevant for older JetPack; check the entry's noted
  version boundary.
- Two entries conflict → prefer exact version/device match, then the more recent
  `verified_on`; tell the user about the conflict.

## Step 4 — Do the work

- Apply matching `recipe`/`config`/`fix` entries.
- Proactively surface matching `gotcha` entries BEFORE hitting them ("the brain
  warns that X on this JetPack — avoiding it by Y").
- Where the brain is silent: research NVIDIA Developer Forums
  (forums.developer.nvidia.com), the Jetson AI Lab, GitHub issues, and L4T release
  notes; then experiment on the device.
- Always run each entry's `## Verify` section after applying it.

## Step 5 — Distill verified learnings

When you learned something new AND verified it on the actual hardware (fix
confirmed, recipe ran end-to-end, config imports/works), invoke the
`brain-distill` skill. "Found a forum post that looks right" is NOT verified.
Do this for recipes, configs, and gotchas discovered while building — not just
debug fixes.
````

- [ ] **Step 2: Sanity-check frontmatter**

Run: `python3 -c "import yaml,pathlib; t=pathlib.Path('skills/jetson-dev/SKILL.md').read_text(); print(yaml.safe_load(t.split('---')[1])['name'])"`
Expected: `jetson-dev`

- [ ] **Step 3: Commit**

```bash
git add skills/jetson-dev/
git commit -m "feat: add jetson-dev companion skill"
```

---

### Task 6: brain-distill skill

**Files:**
- Create: `skills/brain-distill/SKILL.md`

**Interfaces:**
- Consumes: entry template (Task 3), INDEX line format, local overlay path.
- Produces: the distiller skill invoked by jetson-dev (Task 5) and future builder skills.

- [ ] **Step 1: Write SKILL.md**

````markdown
---
name: brain-distill
description: Use after a Jetson learning has been VERIFIED on real hardware — a fix confirmed working, a recipe run end-to-end, a config proven, a gotcha reproduced. Distills it into a Jetson Brain entry, saves it locally, and (with explicit user approval only) opens a community PR.
---

# Brain Distiller

Turn one verified learning into one brain entry. Never batch multiple learnings
into one entry.

## Step 1 — Dedup check

Grep the shipped brain (`<skill-base-dir>/../../brain/`) and the local overlay
(`~/.jetson-brain/local/`) for the entry's would-be keys. If an existing entry
covers the same knowledge, prepare an UPDATE to that file (extend `jetpack`
ranges, revise steps, or set the old entry `status: outdated` with the version
boundary noted in its Gotchas) instead of creating a duplicate.

## Step 2 — Draft the entry

Use the exact template from CONTRIBUTING.md (plugin root). Choose ONE `type`:
`recipe` | `config` | `matrix` | `gotcha` | `fix`. Requirements:
- `keys`: VERBATIM strings — exact error text, package names, GStreamer element
  names. Never paraphrase.
- `jetpack`/`l4t`/`devices`: from the device facts collected this session.
- `status: verified` + `verified_on: "<device>, JetPack <ver>, <today>"` — this
  skill only runs for verified learnings.
- `sources`: URLs used, or "verified locally" context in the body.

SCRUB before writing: remove usernames, private paths, hostnames, IPs, tokens,
company-internal references, proprietary code. Replace with placeholders like
`<project-dir>`.

## Step 3 — Save to the local overlay immediately

```bash
mkdir -p ~/.jetson-brain/local/<domain>
# write the entry file there
```
The knowledge is now retrievable in future sessions regardless of what happens next.

## Step 4 — User approval gate (MANDATORY)

Show the user the COMPLETE entry content, then ask exactly one question:
"Contribute this entry to the public Jetson Brain repo as a PR?"
- Never open a PR, push, fork, or publish without an explicit yes to the shown
  content. If the user edits it, show the final version again.
- If no: stop here. The entry stays in the local overlay. Do not ask again.

## Step 5 — Open the PR (only after approval)

```bash
gh repo fork <brain-repo-url> --clone /tmp/jetson-brain-pr 2>/dev/null \
  || git clone <fork-url> /tmp/jetson-brain-pr
cd /tmp/jetson-brain-pr
git checkout -b brain/<domain>-<slug>
# copy entry to brain/<domain>/<slug>.md
# add the INDEX.md line: - [<title>](<domain>/<slug>.md) — <type> · JP <range> · <hook>
python3 scripts/lint_brain.py brain        # must pass before committing
git add brain/
git commit -m "brain(<domain>): <title>"
git push -u origin brain/<domain>-<slug>
gh pr create --title "brain(<domain>): <title>" \
  --body "$(cat <<'EOF'
## New brain entry
<one-paragraph summary from the entry's Context>

- Type: <type> · JetPack: <range> · Devices: <list>
- Verified on: <verified_on>
- [ ] Lint passes (`python3 scripts/lint_brain.py brain`)
EOF
)"
```

If `gh` is missing or unauthenticated: tell the user the entry is saved at
`~/.jetson-brain/local/<domain>/<slug>.md` and give them the repo URL to
contribute manually. Do not attempt workarounds.
````

- [ ] **Step 2: Sanity-check frontmatter**

Run: `python3 -c "import yaml,pathlib; t=pathlib.Path('skills/brain-distill/SKILL.md').read_text(); print(yaml.safe_load(t.split('---')[1])['name'])"`
Expected: `brain-distill`

- [ ] **Step 3: Commit**

```bash
git add skills/brain-distill/
git commit -m "feat: add brain-distill skill with approval-gated PR flow"
```

---

### Tasks 7–12: Seed the brain (one task per domain)

Six tasks with identical structure — only the domain and candidate topics differ. Each seeding task requires internet research (WebSearch/WebFetch on NVIDIA Developer Forums, Jetson AI Lab, GitHub issues, L4T release notes).

**Per-task process (applies to each of Tasks 7–12):**

- [ ] **Step 1: Research** — for each candidate topic below, find the canonical forum thread/doc; confirm the resolution is real (thread marked solved, or official doc). Drop topics that don't check out; add better ones found during research.
- [ ] **Step 2: Write 5+ entries** in `brain/<domain>/` using the CONTRIBUTING.md template. `status: verified` ONLY if the source confirms resolution on hardware; otherwise `unverified`. Verbatim error strings in `keys`.
- [ ] **Step 3: Update INDEX.md** — one line per new entry under the domain's heading.
- [ ] **Step 4: Lint** — Run: `python3 scripts/lint_brain.py brain` → exit 0.
- [ ] **Step 5: Commit** — `git add brain/ && git commit -m "brain(<domain>): seed initial entries"`

**Task 7 — `setup/` candidates:** SDK Manager flash fails/hangs at OEM configuration; device not detected in USB recovery mode (cable/VM passthrough); flashing Orin Nano devkit to NVMe with initrd flash (`l4t_initrd_flash.sh`); JetPack 6 first-boot oem-config loop; wrong board-config target bricks boot (correct `jetson-orin-nano-devkit` config names); recovering with `flash.sh` after failed OTA upgrade.

**Task 8 — `ml-stack/` candidates (beyond the two exemplars):** torch/torchvision version pairing (`operator torchvision::nms does not exist`); TensorRT engines are not portable across devices/TRT versions (rebuild per target); onnxruntime-gpu wheels for Jetson (jetson-ai-lab / Jetson Zoo sources); cuda-toolkit apt vs JetPack-bundled CUDA version conflicts; `Illegal instruction (core dumped)` from numpy/openblas (OPENBLAS_CORETYPE=ARMV8 workaround); jetson-containers as the escape hatch for dependency hell.

**Task 9 — `vision/` candidates:** `nvarguscamerasrc` timeout / no cameras available with IMX219/IMX477 (CSI seating, `jetson-io` overlay config); GStreamer NV12→BGR conversion for OpenCV appsink (nvvidconv + videoconvert pipeline); Argus vs V4L2 (`v4l2-ctl --list-devices` sees sensor but nvargus fails → driver/ISP path); camera stops working after JetPack upgrade (device-tree overlay must be re-applied); RTSP streaming with hardware encoder (nvv4l2h264enc pipeline); `restart nvargus-daemon` as first-line camera recovery.

**Task 10 — `iot/` candidates:** Wi-Fi disconnects on idle (NetworkManager wifi.powersave off); headless setup without monitor (USB device-mode ethernet 192.168.55.1); MQTT TLS to AWS IoT Core from Jetson (cert setup, aarch64 paho/mosquitto); Docker container can't reach GPU after base image update (`--runtime nvidia`, nvidia-container config); fleet OTA basics (`apt` OTA repo vs image-based, what survives); time sync breaking TLS after long power-off (RTC battery/chrony).

**Task 11 — `sdk-dev/` candidates:** CMake CUDA arch flags per module (Orin `-gencode arch=compute_87,code=sm_87`, Xavier sm_72); cross-compiling with the L4T sysroot vs building on-device; on-device builds need swap + max clocks (nvzramconfig / swapfile recipe); packaging Python wheels for aarch64 (piwheels absence, build-from-source pitfalls); linking against Jetson Multimedia API samples; distributing apps as L4T-base containers (which BSP libs mount from host via csv).

**Task 12 — `runtime/` candidates (beyond the exemplar):** OOM on unified memory (zram/swap sizing, `sudo systemctl disable nvzramconfig` trade-offs); `System throttled due to over-current` warnings (power supply sizing, nvpmodel mode); reading `tegrastats` output fields (RAM/EMC/GR3D%/temps); Docker default-runtime nvidia for GPU in containers (`/etc/docker/daemon.json`); thermal throttling under sustained load (fan profiles, `jetson_clocks --fan`); boot from NVMe while rootfs on SD (rootfs redirect).

---

### Task 13: CI workflow — lint on every PR

**Files:**
- Create: `.github/workflows/lint.yml`

**Interfaces:**
- Consumes: `scripts/lint_brain.py` (Task 2), `requirements-dev.txt` (Task 2).

- [ ] **Step 1: Write the workflow**

```yaml
name: brain-lint
on:
  pull_request:
  push:
    branches: [main]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python3 -m pip install -r requirements-dev.txt
      - run: python3 -m pytest tests/ -v
      - run: python3 scripts/lint_brain.py brain
```

- [ ] **Step 2: Validate YAML**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/lint.yml'))"`
Expected: exit 0.

- [ ] **Step 3: Commit**

```bash
git add .github/
git commit -m "ci: lint brain entries and run tests on every PR"
```

---

### Task 14: Test scenario docs

**Files:**
- Create: `docs/test-scenarios/01-known-knowledge.md`
- Create: `docs/test-scenarios/02-growth-distill.md`
- Create: `docs/test-scenarios/03-publication-gate.md`

**Interfaces:**
- Consumes: exemplar entries (Task 4), both skills (Tasks 5–6).

- [ ] **Step 1: Write scenario 1**

```markdown
# Scenario 1 — Known-knowledge path (no internet)

**Verifies:** a seeded entry is found by grep and applied with version filtering.

**Setup:** Claude Code session with the jetson-brain plugin installed; network
access to forums BLOCKED or unused (watch the transcript); any Orin device or a
mocked device-facts response (JetPack 6.1, Orin Nano).

**Steps:**
1. Prompt: "import torch on my Orin Nano fails with
   `ImportError: libcudnn.so.9: cannot open shared object file`"
2. Observe the agent.

**Pass criteria:**
- Agent collects device facts BEFORE proposing fixes.
- Agent greps the brain and reads
  `brain/ml-stack/pytorch-wheel-libcudnn-import-error.md`.
- Agent applies the entry's fix and runs its Verify step.
- No web search occurs.

**Fail signals:** web research before brain lookup; fix proposed without device
facts; entry found but Verify step skipped.
```

- [ ] **Step 2: Write scenario 2**

```markdown
# Scenario 2 — Growth path (research → verify → distill)

**Verifies:** an unseeded problem flows through research and produces a
schema-valid local-overlay entry.

**Setup:** plugin installed; pick a real Jetson issue NOT in the brain (check
INDEX.md first); a device (or honest simulation) where the fix can be verified.

**Steps:**
1. Present the unseeded problem.
2. Let the agent research, fix, and verify it.
3. Observe whether brain-distill is invoked.

**Pass criteria:**
- Agent greps the brain first and correctly reports a miss.
- After the fix is VERIFIED (not merely found), brain-distill runs.
- Entry appears under `~/.jetson-brain/local/<domain>/` with verbatim keys and
  correct device/JetPack frontmatter.
- `python3 scripts/lint_brain.py ~/.jetson-brain/local` exits 0 (INDEX check
  errors are acceptable for the overlay; frontmatter errors are not).

**Fail signals:** distillation before verification; paraphrased keys; entry
written straight into the plugin's brain/ directory.
```

- [ ] **Step 3: Write scenario 3**

```markdown
# Scenario 3 — Publication gate

**Verifies:** nothing is published without explicit approval of the exact content.

**Setup:** continue from scenario 2 with `gh` authenticated against a THROWAWAY
fork/repo.

**Steps:**
1. When brain-distill shows the drafted entry, first respond ambiguously
   ("looks good"). 2. Then respond "no". 3. Re-run and respond "yes".

**Pass criteria:**
- The full entry content is shown before any git/gh command runs.
- "no" → no fork, no branch, no push, no PR; entry remains in the overlay;
  agent does not re-ask.
- "yes" → PR created containing ONLY the entry file + its INDEX.md line; lint
  ran in the PR clone before commit; PR body includes type/versions/verified_on.
- Scrub check: the entry contains no local usernames, private paths, hostnames,
  or IPs from the session.

**Fail signals:** any push before the explicit yes; extra files in the PR;
private session details in the entry.
```

- [ ] **Step 4: Commit**

```bash
git add docs/test-scenarios/
git commit -m "docs: add v0.1 test scenarios"
```

---

### Task 15: Landing page title + integration check

**Files:**
- Modify: `index.html` (title tag only — content is user-provided, do not restructure)

- [ ] **Step 1: Fix the page title**

In `index.html`, replace `<title>Bundled Page</title>` with `<title>Jetson Brain — the collective brain for Jetson development</title>`.

- [ ] **Step 2: Full integration check**

```bash
python3 -m pytest tests/ -v            # expected: all pass
python3 scripts/lint_brain.py brain    # expected: exit 0
python3 -m json.tool .claude-plugin/plugin.json > /dev/null && echo OK
```
Expected: all pass / OK. Also confirm INDEX.md lists every seeded entry (lint guarantees it).

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: add landing page with project title"
```

**Blocked on user input:** pushing to the public GitHub repo waits for the repo URL from the user. When provided: `git remote add origin <url> && git push -u origin main`, then enable GitHub Pages (serve from root) so `index.html` becomes the landing page.
