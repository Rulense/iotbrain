# Jetson Brain 🧠

**The collective brain for NVIDIA Jetson development.** Install it into Claude Code and your agent starts with everything the community already knows about building on Jetson — and everything it learns in your sessions flows back into the brain for everyone.

## Why

Jetson development knowledge is scattered and perishable. How to deploy a model with TensorRT on an Orin Nano. Which CUDA × cuDNN × PyTorch combination actually works on JetPack 6. How to get a CSI camera into a DeepStream pipeline. How to package a library for aarch64. How to connect a fleet to a cloud backend. What breaks along the way, and how to get past it.

All of it exists — spread across NVIDIA forum threads, sample repos, release notes, and the hard-won experience of engineers. None of it is in one place an agent (or a human) can reliably draw on. So every developer, and every AI coding agent, relearns Jetson from scratch.

## What it is

Jetson Brain is a **Claude Code plugin** with two parts:

**The Brain** — a grep-able knowledge base of markdown entries covering the whole Jetson development lifecycle. Not a troubleshooting database: a general knowledge store. Entry types:

| Type | What it captures | Example |
|---|---|---|
| `recipe` | A verified way to accomplish a task | Deploy YOLO with TensorRT on Orin Nano, end to end |
| `config` | A known-working configuration | JetPack 6.1 + PyTorch 2.5 wheel + cuDNN combo that works |
| `matrix` | Version compatibility knowledge | CUDA × TensorRT × framework support across JetPack releases |
| `gotcha` | A trap to avoid proactively | nvarguscamerasrc quirk on JP6.0 that silently drops frames |
| `fix` | An error and its verified solution | `libcudnn.so.8` import failure → exact resolution |

**The Skills** — how the agent puts the brain to work: a main Jetson development skill that consults the brain for *any* Jetson task, and a distiller skill that grows the brain. Domain skills for the major workflows (vision pipelines, IoT/edge connectivity, SDK and library development) arrive in v0.2. Bundled & companion skills: nine NVIDIA device skills ship vendored in `skills/`, with the full ecosystem (including companion installs) catalogued in `SKILLS-CATALOG.md`.

## The loop — for every task, not just broken ones

```
   any Jetson task: build, deploy, integrate, optimize, debug
                            │
                            ▼
              consult the brain (grep, version-aware)
                            │
              ┌─────────────┴──────────────┐
        brain knows                  brain is silent
              │                            │
     apply known recipes,        figure it out: research the
     configs, avoid gotchas      internet, experiment, verify
              │                            │
              └─────────────┬──────────────┘
                            ▼
          learned something new & verified?
                            │
                            ▼
        distill it into the brain → community PR
```

Building a vision pipeline that works produces a `recipe`. Finding a wheel combo that imports cleanly produces a `config`. Losing an hour to a silent camera driver quirk produces a `gotcha`. Debugging is just one of the ways the brain grows.

## How it works

- **No infrastructure.** The brain is plain markdown in this repo. Retrieval is grep — exact error strings, package names, and device models are the search keys, which is what agents search best. No vector database, no Docker, no index to go stale.
- **Version-aware.** Every entry is scoped to JetPack/L4T versions and device models. The agent checks applicability before trusting knowledge, so nothing stale gets confidently misapplied. Entries also carry a `company` field — v0.1 content is NVIDIA Jetson, and the brain broadens to other edge-IoT vendors over time.
- **Human-reviewed growth.** The only write path into the shared brain is a pull request. The distiller formats entries; the community reviews truth. Nothing is published without the contributing user approving the exact content first. Knowledge you choose not to contribute stays in a private local overlay at `~/.jetson-brain/local/`.
- **Transparent verification.** An entry is `verified` only when it worked on real hardware (confirmed by the contributor or the cited thread's author) or is stated by current official NVIDIA docs, cited with a check date — everything else is honestly marked `unverified` until confirmed. Junk doesn't get in, and provenance is always transparent.

## What's inside

```
jetson-brain/
├── skills/
│   ├── jetson-dev/            # the companion: brain consultation for any Jetson task
│   ├── brain-distill/         # turns verified learnings into brain entries + PRs
│   ├── jetson-* (9)           # vendored NVIDIA device skills — see ATTRIBUTION.md
│   ├── vision-pipeline/       # (v0.2 — coming) cameras, GStreamer, DeepStream
│   ├── iot-connect/           # (v0.2 — coming) MQTT, cloud backends, fleet/edge deployment
│   └── sdk-build/             # (v0.2 — coming) building libraries & SDKs for aarch64/L4T
└── brain/
    ├── INDEX.md               # one line per entry — the map of what the brain knows
    ├── setup/                 # flashing, boot, JetPack install, recovery
    ├── ml-stack/              # CUDA, cuDNN, TensorRT, frameworks, model deployment
    ├── vision/                # cameras, capture, GStreamer, DeepStream pipelines
    ├── iot/                   # connectivity, cloud integration, fleet management
    ├── sdk-dev/               # building & packaging libraries/SDKs for the platform
    └── runtime/               # power modes, thermals, containers, performance
```

## Install

Two steps inside Claude Code once the repo is public (repo URL coming soon):

```
/plugin marketplace add <owner>/jetson-brain
/plugin install jetson-brain@jetson-brain
```

Works whether Claude Code runs on the Jetson itself or on a host machine reaching the device over SSH.

## Roadmap

- **v0.1 — the core.** Plugin scaffold, jetson-dev + distiller skills, brain seeded across all six domains with battle-tested entries.
- **v0.2 — domain skills.** Vision pipeline, IoT connectivity, and SDK-building skills wired into the brain.
- **v1.0 — community scale.** Contribution tooling, entry lifecycle automation (outdated-marking on new JetPack releases), coverage across the Jetson lineup.

## Contributing

The brain only gets smarter if verified knowledge flows back. `CONTRIBUTING.md` defines the entry format and the verification bar: real hardware or current official docs, exact version/device frontmatter, sources linked. The `brain-distill` skill drafts a compliant entry and PR for you — review it, approve it, done.

---

*Built on a simple bet, backed by how the best coding agents already work: for a domain where package names, error strings, and device models are the search keys, curated markdown + grep beats any vector database — and a community PR flow beats any opaque memory service.*
