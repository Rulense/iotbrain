---
name: iot-dev
description: Use for ANY edge-IoT device task — building, deploying, integrating, optimizing, or debugging on embedded and edge boards. Covers NVIDIA Jetson / JetPack / L4T / Tegra (Orin, Xavier, Nano, Thor families) today, with Raspberry Pi, ESP32, and other boards as the brain grows. Consults the iotbrain knowledge base before acting and distills verified new learnings back into it.
---

# Edge-IoT Development Companion

You have the iotbrain: community-verified knowledge at `${CLAUDE_PLUGIN_ROOT}/brain/`
(`${CLAUDE_PLUGIN_ROOT}` is the env var Claude Code sets to the plugin's install root),
plus the user's private overlay at `~/.iotbrain/local/`. Entry types: `recipe`
(how to accomplish a task), `config` (known-working setup), `matrix` (version
compatibility), `gotcha` (trap to avoid), `fix` (error → solution).
Every entry also carries a `company` frontmatter field naming the device vendor
(e.g. `nvidia`).

Follow these steps in order for every edge-IoT task.

## Step 1 — Identify the device and vendor FIRST

Determine the board, its vendor/company, and its OS/SDK version before doing
anything else. If you are on a host rather than the device, ask the user for
SSH access details if not already known and run detection over `ssh`. If the
device is unreachable or the facts are not detectable, ask the user for the
board model and OS/SDK version before proceeding.

Worked example — NVIDIA Jetson (company `nvidia`):
- On the Jetson itself: `uname -m` is `aarch64` AND `/etc/nv_tegra_release` exists.
- Collect (never skip):
```bash
cat /etc/nv_tegra_release                 # L4T version
dpkg-query -W nvidia-l4t-core 2>/dev/null # L4T package version
cat /proc/device-tree/model               # device model
```
- Map L4T → JetPack (36.x → JetPack 6, 35.x → JetPack 5).

## Step 2 — Consult the brain

Entries are company-scoped: match entries whose `company` value is the
device's vendor.

1. Read `brain/INDEX.md` — scan for entries matching the task.
2. Grep both stores for task keywords, package names, and (when debugging)
   VERBATIM error strings:
```bash
grep -ril "<verbatim error or keyword>" "${CLAUDE_PLUGIN_ROOT}/brain/" ~/.iotbrain/local/ 2>/dev/null
```
3. Read every hit's full entry before acting.

## Step 3 — Filter by applicability

- Entry's `company` matches the device's vendor AND its version/device fields
  (e.g. `jetpack`/`devices` for Jetson entries) match the device facts → trust
  it; apply as written.
- Entry's `company` is a different vendor → skip it; knowledge does not
  transfer across vendors.
- Version or device mismatch within the right company → treat as a LEAD: tell
  the user "the brain has a possibly-relevant entry for <platform version> X,
  verifying it applies here", and verify before applying.
- `status: outdated` → only relevant for older platform releases; check the
  entry's noted version boundary.
- Two entries conflict → prefer exact version/device match, then the more recent
  `verified_on`; tell the user about the conflict.

## Step 4 — Do the work

When a more specific installed skill covers the task — `jetson-diagnostic`,
`jetson-memory-audit`, or another vendored device skill bundled with this
plugin, or a companion skill from `SKILLS-CATALOG.md` — use that skill for the
doing. Consult the brain first either way (Steps 2–3): brain entries tell you
which knowledge applies to this device before the specialist skill acts.

- Apply matching `recipe`/`config`/`fix` entries.
- Proactively surface matching `gotcha` entries BEFORE hitting them ("the brain
  warns that X on this platform release — avoiding it by Y").
- Where the brain is silent: research the vendor's developer forums, docs, and
  release notes (for Jetson: forums.developer.nvidia.com, the Jetson AI Lab,
  and L4T release notes) plus GitHub issues; then experiment on the device.
- Always run each entry's `## Verify` section after applying it.

## Step 5 — Distill verified learnings

When you learned something new AND verified it on the actual hardware (fix
confirmed, recipe ran end-to-end, config imports/works), invoke the
`brain-distill` skill. "Found a forum post that looks right" is NOT verified.
Do this for recipes, configs, and gotchas discovered while building — not just
debug fixes.
