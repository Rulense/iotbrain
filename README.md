# iotbrain 🧠

**The collective brain for edge-IoT development.** Install it into Claude Code and your agent starts with everything the community already knows about building on your device — and everything it learns in your sessions flows back into the brain for everyone. NVIDIA Jetson is the first fully seeded platform.

<!-- IOTBRAIN_STATS_START -->
**39** brain entries · **18** skills · **6** domains · **5** platforms — last updated 2026-07-18
<!-- IOTBRAIN_STATS_END -->

## Why

Edge-IoT development knowledge is scattered and perishable. How to deploy a model with TensorRT on a Jetson Orin Nano. Which CUDA × cuDNN × PyTorch combination actually works on JetPack 6. How to get a CSI camera into a DeepStream pipeline. How to package a library for aarch64. How to connect a fleet to a cloud backend. What breaks along the way, and how to get past it.

All of it exists — spread across vendor forums, sample repos, release notes, and the hard-won experience of engineers. None of it is in one place an agent (or a human) can reliably draw on. So every developer, and every AI coding agent, relearns each device from scratch.

## What it is

iotbrain is a **Claude Code plugin** with two parts:

**The Brain** — a grep-able knowledge base of markdown entries covering the whole edge-IoT development lifecycle. Not a troubleshooting database: a general knowledge store. Entry types:

| Type | What it captures | Example |
|---|---|---|
| `recipe` | A verified way to accomplish a task | Deploy YOLO with TensorRT on Orin Nano, end to end |
| `config` | A known-working configuration | JetPack 6.1 + PyTorch 2.5 wheel + cuDNN combo that works |
| `matrix` | Version compatibility knowledge | CUDA × TensorRT × framework support across JetPack releases |
| `gotcha` | A trap to avoid proactively | nvarguscamerasrc quirk on JP6.0 that silently drops frames |
| `fix` | An error and its verified solution | `libcudnn.so.8` import failure → exact resolution |

**The Skills** — how the agent puts the brain to work: a main `iot-dev` companion skill that identifies the device and vendor, then consults the brain for *any* edge-IoT task (NVIDIA Jetson today; Raspberry Pi, ESP32, and other boards as the brain grows), and a distiller skill that grows the brain. Domain skills for the major workflows (vision pipelines, IoT/edge connectivity, SDK and library development) arrive in v0.2. Bundled & companion skills: sixteen vendored device skills ship in `skills/` — nine NVIDIA Jetson skills plus seven from Seeed, D-Robotics, Espressif, and the Zephyr ecosystem — with the full ecosystem (including companion installs) catalogued in `SKILLS-CATALOG.md`.

## The loop — for every task, not just broken ones

```
 any edge-IoT task: build, deploy, integrate, optimize, debug
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
- **Version-aware.** Every entry is scoped to platform/SDK versions and device models (JetPack/L4T versions and Jetson models for today's entries). The agent checks applicability before trusting knowledge, so nothing stale gets confidently misapplied. Entries also carry a `company` field naming the device vendor — v0.1 content is NVIDIA Jetson, and the brain broadens to other edge-IoT vendors over time.
- **Human-reviewed growth.** The only write path into the shared brain is a pull request. The distiller formats entries; the community reviews truth. Nothing is published without the contributing user approving the exact content first. Knowledge you choose not to contribute stays in a private local overlay at `~/.iotbrain/local/`.
- **Transparent verification.** An entry is `verified` only when it worked on real hardware (confirmed by the contributor or the cited thread's author) or is stated by the vendor's current official docs, cited with a check date — everything else is honestly marked `unverified` until confirmed. Junk doesn't get in, and provenance is always transparent.

## What's inside

```
iotbrain/
├── skills/
│   ├── iot-dev/               # the companion: brain consultation for any edge-IoT task
│   ├── brain-distill/         # turns verified learnings into brain entries + PRs
│   ├── jetson-* (9)           # vendored NVIDIA device skills — see ATTRIBUTION.md
│   ├── … (7 more)             # vendored skills from Seeed, D-Robotics, Espressif, Zephyr
│   ├── vision-pipeline/       # (v0.2 — coming) cameras, GStreamer, DeepStream
│   ├── iot-connect/           # (v0.2 — coming) MQTT, cloud backends, fleet/edge deployment
│   └── sdk-build/             # (v0.2 — coming) building libraries & SDKs for edge targets
└── brain/
    ├── INDEX.md               # one line per entry — the map of what the brain knows
    ├── setup/                 # flashing, boot, OS install, recovery
    ├── ml-stack/              # CUDA, cuDNN, TensorRT, frameworks, model deployment
    ├── vision/                # cameras, capture, GStreamer, DeepStream pipelines
    ├── iot/                   # connectivity, cloud integration, fleet management
    ├── sdk-dev/               # building & packaging libraries/SDKs for the platform
    └── runtime/               # power modes, thermals, containers, performance
```

## Install

Two steps inside Claude Code (marketplace link coming soon — `OWNER` below is a placeholder until the public repo lands):

```
/plugin marketplace add Rulense/iotbrain
/plugin install iotbrain@iotbrain
```

Works whether Claude Code runs on the device itself or on a host machine reaching the device over SSH.

## Roadmap

- **v0.1 — the core.** Plugin scaffold, iot-dev + distiller skills, brain seeded across all six domains with battle-tested entries on the first platform (NVIDIA Jetson).
- **v0.2 — domain skills.** Vision pipeline, IoT connectivity, and SDK-building skills wired into the brain.
- **v1.0 — community scale.** Contribution tooling, entry lifecycle automation (outdated-marking on new platform releases), coverage across vendors and device families.

## Contributing

The brain only gets smarter if verified knowledge flows back. `CONTRIBUTING.md` defines the entry format and the verification bar: real hardware or current official docs, exact version/device frontmatter, sources linked. The `brain-distill` skill drafts a compliant entry and PR for you — review it, approve it, done.

---

*Built on a simple bet, backed by how the best coding agents already work: for a domain where package names, error strings, and device models are the search keys, curated markdown + grep beats any vector database — and a community PR flow beats any opaque memory service.*
