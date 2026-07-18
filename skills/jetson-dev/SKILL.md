---
name: jetson-dev
description: Use for ANY NVIDIA Jetson / JetPack / L4T / Tegra task — building, deploying, integrating, optimizing, or debugging on Jetson devices (Orin, Xavier, Nano, Thor families). Consults the Jetson Brain knowledge base before acting and distills verified new learnings back into it.
---

# Jetson Development Companion

You have the Jetson Brain: community-verified knowledge at `${CLAUDE_PLUGIN_ROOT}/brain/`
(`${CLAUDE_PLUGIN_ROOT}` is the env var Claude Code sets to the plugin's install root),
plus the user's private overlay at `~/.jetson-brain/local/`. Entry types: `recipe`
(how to accomplish a task), `config` (known-working setup), `matrix` (version
compatibility), `gotcha` (trap to avoid), `fix` (error → solution).
Every entry also carries a `company` frontmatter field naming the device vendor
(e.g. `nvidia`).

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
grep -ril "<verbatim error or keyword>" "${CLAUDE_PLUGIN_ROOT}/brain/" ~/.jetson-brain/local/ 2>/dev/null
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
