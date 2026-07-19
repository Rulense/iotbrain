# Skills Catalog

The Jetson skills ecosystem, in three tiers: what ships in this plugin, what to install
alongside it, and how everything was vetted.

## Bundled (ship with this plugin, under `skills/`)

Jetson Brain's own skills:

- **jetson-dev** — the companion: collects device facts, consults the brain before any Jetson task, applies version-matched knowledge, distills learnings back — Jetson Brain (this repo).
- **brain-distill** — turns a hardware-verified session learning into a brain entry and (with approval) a community PR — Jetson Brain (this repo).

Vendored NVIDIA device skills (from [NVIDIA-AI-IOT/jetson-device-skills](https://github.com/NVIDIA-AI-IOT/jetson-device-skills) @ `0a803703`; see `ATTRIBUTION.md`):

- **jetson-diagnostic** — read-only health snapshot: identity, memory, GPU, thermal, power, storage, services, top processes — NVIDIA-AI-IOT.
- **jetson-memory-audit** — memory-focused audit plus the drop_caches before/after verify loop for real reclamation deltas — NVIDIA-AI-IOT.
- **jetson-headless-mode** — plan-then-apply reclamation of GUI/daemon memory; dry-run by default, safe-listed reversible commands only — NVIDIA-AI-IOT.
- **jetson-inference-mem-tune** — picks the serving runtime (vLLM/SGLang/llama.cpp/TensorRT Edge-LLM) and memory launch flags from a live audit — NVIDIA-AI-IOT.
- **jetson-llm-serve** — stand up vLLM or SGLang serving with the Jetson-correct container path per generation (Thor vs Orin, JetPack level) — NVIDIA-AI-IOT.
- **jetson-llm-benchmark** — reproducible latency/throughput benchmarks for vLLM, llama.cpp, and Ollama with structured JSON output — NVIDIA-AI-IOT.
- **jetson-package** — Jetson-compatible containers and PyPI indexes; maps Orin SM 8.7 vs Thor SM 11.0 so generic ARM wheels don't get suggested — NVIDIA-AI-IOT.
- **jetson-speculative-decoding** — adds EAGLE-3 / draft-model speculation to a Jetson vLLM server when TPOT is the bottleneck — NVIDIA-AI-IOT.
- **jetson-print-device-info** — minimal read-only device info report (model, L4T, kernel, OS, power mode); upstream's reference example skill — NVIDIA-AI-IOT.

## Companion installs (useful alongside, not bundled)

- **jetson-bsp-skills** — [NVIDIA-AI-IOT/jetson-bsp-skills](https://github.com/NVIDIA-AI-IOT/jetson-bsp-skills), pinned commit `fdfafef0`. Host-side BSP customization workflow: 24 skills covering Jetson Linux BSP download, kernel/device-tree/bootloader customization, flashing, and related host workflows.
  - Install: `git clone https://github.com/NVIDIA-AI-IOT/jetson-bsp-skills && ./setup.sh --workspace <ws>`
  - Why not bundled: the skills are workspace-stateful — `setup.sh` installs them into a workspace with shared `context/` and `references/` state they depend on, so they are not self-contained files we can vendor.
- **VSS skills** — [NVIDIA-AI-Blueprints/video-search-and-summarization](https://github.com/NVIDIA-AI-Blueprints/video-search-and-summarization) `skills/` directory (Apache-2.0). Product operations skills for the Video Search and Summarization blueprint: 17 skills total — 16 stable on `main`, plus `vss-build-vision-agent` on the `feat/build-vision-agent-skill` branch tracked by open PR #727.
  - Why not bundled: scoped to the VSS product suite rather than general Jetson device development.
- **jetson-perf-investigator** (subagent) — from jetson-device-skills' `agents/` directory at the same pinned commit. A Claude Code subagent that orchestrates jetson-diagnostic, jetson-memory-audit, jetson-headless-mode, and jetson-inference-mem-tune into an end-to-end "Jetson is slow / hot / OOM" investigation.
  - Why not bundled: it invokes the skills via repo-relative paths (`bash skills/<name>/scripts/...`), which need fixing to this plugin's install root before it can run standalone; install manually after adjusting those paths.

## Legitimacy check

All catalog entries above were legitimacy-checked before inclusion: each comes from an
official NVIDIA GitHub organization (NVIDIA-AI-IOT, NVIDIA-AI-Blueprints), licenses were
verified (Apache-2.0 for source code; jetson-device-skills documentation additionally
CC-BY-4.0), and the vendored skills' scripts and instructions passed a security review
(no non-NVIDIA network calls, no pipe-to-shell execution, no credential exfiltration,
no unguarded destructive commands, no prompt-injection content). See `ATTRIBUTION.md`
for vendoring provenance.
