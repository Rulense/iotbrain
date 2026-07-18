# Jetson Brain — Design Specification

**Date:** 2026-07-17
**Status:** Draft for review

## Overview

Jetson Brain is a public Claude Code plugin that gives coding agents an **overall brain for NVIDIA Jetson development** — a git-shared, grep-able markdown knowledge base covering the full development lifecycle (setup, ML stack, vision, IoT, SDK development, runtime/performance), plus the skills to use it and grow it. It is not a debugging tool and not personal session memory: it is collective, reviewed, version-scoped domain knowledge.

The universal loop: for **any** Jetson task, the agent consults the brain first, does the work (researching the internet where the brain is silent), and — when it verifies something new on real hardware — distills that learning into a structured entry and drafts a community pull request.

## Decisions made during brainstorming

| Decision | Choice |
|---|---|
| Sharing model | Git repo + pull requests (human review is the quality/anti-poisoning gate) |
| Audience | Public community on GitHub (knowledge must be public-safe) |
| Architecture | Claude Code plugin + file-based brain, grep retrieval (no vector DB, no server) |
| Scope | Whole Jetson dev lifecycle; five knowledge types; debugging is one facet |
| Decomposition | v0.1 core (plugin + jetson-dev + distiller + seeded brain), v0.2 builder skills |

## Goals

1. An installed agent solves known Jetson problems and executes known recipes **without re-research**, using version-appropriate knowledge.
2. New verified learnings flow back to the community with near-zero friction (distiller drafts everything; user reviews and approves).
3. Zero infrastructure for users: one plugin install, plain files, grep.
4. Knowledge stays trustworthy: verified-on-hardware bar, version scoping, PR review, explicit staleness lifecycle.

## Non-goals

- Personal/session memory (Claude Code's native auto-memory already does this).
- Semantic search, embeddings, vector databases, or any hosted service.
- Auto-publishing anything without explicit user approval of the exact content.
- Internal-NVIDIA or pre-release knowledge (public repo; public-safe only).

## Architecture

One public GitHub repo is simultaneously the Claude Code plugin and the brain:

```
jetson-brain/
├── .claude-plugin/plugin.json     # plugin manifest
├── skills/
│   ├── jetson-dev/SKILL.md        # companion skill: brain consultation for any Jetson task
│   ├── brain-distill/SKILL.md     # distiller: learnings → entries → PRs
│   ├── vision-pipeline/SKILL.md   # (v0.2) cameras, GStreamer, DeepStream
│   ├── iot-connect/SKILL.md       # (v0.2) MQTT, cloud backends, fleet/edge
│   └── sdk-build/SKILL.md         # (v0.2) libraries & SDKs for aarch64/L4T
├── brain/
│   ├── INDEX.md                   # one line per entry — the map
│   ├── setup/                     # flashing, boot, JetPack install, recovery
│   ├── ml-stack/                  # CUDA, cuDNN, TensorRT, frameworks, model deployment
│   ├── vision/                    # cameras, capture, GStreamer, DeepStream
│   ├── iot/                       # connectivity, cloud integration, fleet management
│   ├── sdk-dev/                   # building & packaging libraries/SDKs
│   └── runtime/                   # power modes, thermals, containers, performance
├── CONTRIBUTING.md                # entry format spec + verification bar + PR checklist
├── docs/                          # design specs, test scenarios
└── README.md                      # project page
```

**Retrieval is grep/read.** Package names, verbatim error strings, GStreamer element names, and device models are the search keys. The always-cheap path is `INDEX.md` (one line per entry); full entries are read on demand. No index build, nothing to go stale.

**Local overlay.** Entries a user hasn't (or won't) contribute live in `~/.jetson-brain/local/`, mirroring the `brain/` domain structure. The jetson-dev skill greps both the shipped brain and the overlay. This keeps knowledge usable immediately after distillation, before (or without) a PR, and gives private/company-specific knowledge a home outside the public repo.

## Components

### Brain entry format

One markdown file per entry. Frontmatter schema:

```markdown
---
title: <one-line, specific, includes key terms>
type: recipe | config | matrix | gotcha | fix
company: nvidia           # device vendor (nvidia | raspberry-pi | qualcomm | ...) — added 2026-07-17: brain broadens to all edge-IoT scenarios over time
keys:                     # verbatim grep targets: error strings, package names, element names
  - "ImportError: libcudnn.so.8: cannot open shared object file"
jetpack: ["6.0", "6.1"]   # applicable JetPack versions
l4t: ["36.x"]             # applicable L4T versions
devices: [orin-nano, orin-nx, agx-orin]   # or [all]
status: verified | unverified | outdated
verified_on: "AGX Orin, JetPack 6.1, 2026-07-10"
sources: ["https://forums.developer.nvidia.com/t/..."]
---
## Context        (when this applies / what you were trying to do)
## Knowledge      (the recipe / config / matrix / trap / root cause + fix)
## Verify         (how to confirm it worked / still holds)
## Gotchas        (near-miss variants, what makes it recur)
```

Body section names flex slightly by type (a `fix` uses "Root cause" + "Fix"; a `recipe` uses "Steps"), but Context / Verify are mandatory for all types. `INDEX.md` carries one line per entry: `- [title](domain/slug.md) — type, JetPack range, one-hook summary`.

### Skill: jetson-dev

Trigger: any Jetson/JetPack/L4T/Tegra-related task — building, deploying, integrating, optimizing, or debugging.

Behavior contract:
1. **Collect device facts** first: device model, JetPack/L4T version, relevant tool versions. Detect whether Claude Code is running on the Jetson itself (aarch64 + L4T present) or on a host reaching the device over SSH, and gather facts accordingly.
2. **Consult the brain**: scan `INDEX.md`, then grep `brain/` and `~/.jetson-brain/local/` for task keywords, package names, and (when debugging) verbatim error strings.
3. **Filter by applicability**: an entry matching the device/JetPack version is trusted; a version-mismatched entry is treated as a lead — "possibly relevant, verify before applying."
4. **Do the work**, applying known recipes/configs and proactively avoiding matching `gotcha` entries. Where the brain is silent, research (NVIDIA developer forums, GitHub issues, release notes) and experiment.
5. **After any verified new learning**, invoke brain-distill. "Verified" means the recipe/config/fix was confirmed working on the actual hardware, not merely found online.

### Skill: brain-distill

Trigger: invoked by jetson-dev (or any skill / the user) after a verified learning.

Behavior contract:
1. **Dedup check**: grep the brain for an existing entry covering the same knowledge. If found, prepare an *update* (extend version ranges, revise steps, flip status) instead of a new file.
2. **Draft the entry** in the format above, choosing the correct `type`, populating `keys` with verbatim strings, scrubbing anything session-private (paths, hostnames, credentials, proprietary code).
3. **Save to the local overlay** immediately — knowledge is never lost even if no PR happens.
4. **User approval gate**: show the user the exact entry content and ask whether to contribute it. Never open a PR, push, or publish anything without explicit approval of the shown content.
5. **On approval**: fork/clone via `gh`, branch, commit the entry + its `INDEX.md` line, open a PR with a description generated from the entry.

### Builder skills (v0.2): vision-pipeline, iot-connect, sdk-build

Shared contract, per pack: consult the brain **before and during** the task (surface matching `gotcha`/`config`/`matrix` entries for this JetPack/device proactively); carry the stable procedural how-to in their own SKILL.md bodies; route every verified new discovery through brain-distill. Stable knowledge lives in skills (changes via releases); volatile version-specific knowledge lives in the brain (changes via daily PRs).

### Plugin packaging

Standard Claude Code plugin: manifest + skills, installable from the plugin marketplace in one command; the brain ships inside the plugin so grep works from the install directory with no setup. Updates arrive via plugin update. No hooks and no MCP server in v0.1 — skills-only keeps the surface simple and the token overhead near zero (only skill names/descriptions sit in context until used).

## Error handling

- **Brain miss** → normal research path; not an error.
- **Version mismatch on a hit** → downgrade to "lead," verify before applying; if the old fix no longer works on the newer JetPack, distill an update marking the entry's version boundary.
- **`gh` unavailable / no auth / no fork permissions** → entry is already safe in the local overlay; tell the user how to contribute manually (file content + repo URL).
- **Malformed entries in the brain** (bad frontmatter from a merged PR) → jetson-dev ignores frontmatter it can't parse but still uses the body via grep; CONTRIBUTING's PR checklist + a CI format-lint on the repo prevent most of these at review time.
- **Conflicting entries** (two entries claim different fixes for the same symptom) → prefer the version/device-exact match, then the more recently `verified_on`; flag the conflict to the user and, once resolved on hardware, distill the correction.

## Quality control and knowledge lifecycle

- **Write path**: only human-reviewed PRs reach the shared brain. This is the anti-poisoning gate (memory poisoning is a formalized attack class — OWASP ASI06).
- **Verification bar** (CONTRIBUTING.md): worked on real hardware, verbatim `keys`, mandatory version/device frontmatter, sources linked, no secrets/private content.
- **Staleness**: entries are version-scoped by construction; `status: outdated` marks superseded knowledge (kept for older-JetPack users, with the boundary documented). New JetPack releases trigger a maintenance sweep (v1.0: automated issue-filing listing entries whose version ranges don't cover the new release).
- **CI on the repo**: frontmatter schema lint + INDEX.md consistency check on every PR.

## Testing

Scripted end-to-end scenarios, kept in `docs/test-scenarios/` so contributors can regression-test skill changes:

1. **Known-knowledge path**: a seeded issue/recipe is executed from the brain alone — no internet — with the correct version filtering applied.
2. **Growth path**: an unseeded problem goes research → verify → distill and produces a schema-valid entry in the local overlay.
3. **Publication gate**: the PR flow drafts correctly and demonstrably cannot publish without explicit user approval; private-content scrubbing verified.
4. **Proactive path** (v0.2): a builder skill surfaces a relevant seeded `gotcha` before the agent hits it.
5. **Format CI**: lint catches bad frontmatter and INDEX.md drift on PRs.

Seed target for v0.1: 5–10 battle-tested entries per domain (~30–60 entries) drawn from NVIDIA developer forum classics, each format-complete, so scenario 1 is testable across all six domains.

## Roadmap

- **v0.1 — the core**: plugin scaffold, jetson-dev + brain-distill skills, seeded brain (all six domains), CONTRIBUTING.md, CI lint, test scenarios 1–3 passing.
- **v0.2 — builder skills**: vision-pipeline, iot-connect, sdk-build wired to the brain; scenario 4.
- **v1.0 — community scale**: contribution tooling, staleness automation on JetPack releases, device-coverage expansion.

Each phase is its own plan → implementation cycle; v0.2 skills are content additions on a stable chassis, not new architecture.
