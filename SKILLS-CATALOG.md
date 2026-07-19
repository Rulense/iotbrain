# Skills Catalog

The edge-IoT skills ecosystem, in three tiers: what ships in this plugin, what to install
alongside it, and how everything was vetted.

## Bundled (ship with this plugin, under `skills/`)

iotbrain's own skills:

- **iot-dev** — the companion: identifies the device and vendor, consults the brain before any edge-IoT task, applies version-matched knowledge, distills learnings back — iotbrain (this repo).
- **brain-distill** — turns a hardware-verified session learning into a brain entry and (with approval) a community PR — iotbrain (this repo).

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

## Ecosystem catalog — researched & vetted 2026-07-18

A deep-research sweep across GitHub (filename:SKILL.md × hardware keywords, org-by-org
sweeps of 40+ vendor orgs) and vendor announcements. Legitimacy bar: publisher
verification, content reads, safety scan, license, activity.

### Newly bundled (vendored into `skills/`; see `ATTRIBUTION.md` for pinned commits)

- **ee-datasheet-master** — [Seeed-Studio/ai-skills](https://github.com/Seeed-Studio/ai-skills) — Seeed Studio (official) — MIT — datasheet extraction with strict PDF-only rules, board-agnostic — all.
- **schematic-analyzer** — [Seeed-Studio/ai-skills](https://github.com/Seeed-Studio/ai-skills) — Seeed Studio (official) — MIT — KiCad/Cadence schematic analysis, board-agnostic — all.
- **rdk-peripheral-cookbook** — [D-Robotics/moss](https://github.com/D-Robotics/moss) — D-Robotics/Horizon (official) — MIT — cross-platform GPIO/I2C/CAN peripheral guidance incl. RPi/Jetson/Rockchip mapping — d-robotics, nvidia, raspberry-pi, rockchip.
- **espdl-operator** — [espressif/esp-dl](https://github.com/espressif/esp-dl) `tools/agents/skills/` — Espressif (official) — MIT — implement NN operators for ESP32-S3/P4 — espressif.
- **espdl-quantize** — [espressif/esp-dl](https://github.com/espressif/esp-dl) `tools/agents/skills/` — Espressif (official) — MIT — quantize NN models for ESP-DL — espressif.
- **devicetree** — [beriberikix/zephyr-agent-skills](https://github.com/beriberikix/zephyr-agent-skills) — Jonathan Beri (Golioth CEO) — Apache-2.0 — Zephyr RTOS devicetree work, any Zephyr board — zephyr (nordic, nxp, st, espressif).
- **hardware-io** — [beriberikix/zephyr-agent-skills](https://github.com/beriberikix/zephyr-agent-skills) — Jonathan Beri — Apache-2.0 — Zephyr hardware I/O, any Zephyr board — zephyr (nordic, nxp, st, espressif).

### Tier 1 — official vendor/foundation (reference, install from upstream)

- **NVIDIA/skills** — NVIDIA (official) — Apache-2.0 + CC-BY-4.0 — canonical ~250-skill catalog (jetson-*, deepstream-*, vss-*, holoscan-*, tao-*, doca-*, physical-ai-*), daily-synced, docs.nvidia.com/skills; mirrors our three source repos — nvidia.
- **NVIDIA-AI-IOT/jetson-ai-lab** (`.agents/skills`) — NVIDIA (official) — jetson-ai-lab code-samples/verify-build/model-catalog-inference — nvidia.
- **NVIDIA-AI-IOT/inference_builder** — NVIDIA (official) — Apache-2.0 — generates Python inference pipelines — nvidia.
- **NVIDIA-AI-IOT/DeepStream_Coding_Agent** + **NVIDIA/DeepStream** `skills/` + **NVIDIA-TAO/tao-skill-bank** — NVIDIA (official) — Apache-2.0 — DeepStream coding agent; 60+ TAO skills — nvidia.
- **espressif/esp-claw** + **esp-claw-skills-lab** — Espressif (official) — Apache-2.0/MIT — on-device ESP32 agent skills (1833★); note: espressif/skills catalog repo is currently an empty placeholder — watch it — espressif.
- **anthropics/claude-plugins-official** → cwc-makers plugin (m5-onboard, cardputer-buddy) — Anthropic (official) — M5Stack/ESP32 detect/flash/provision — espressif, m5stack.
- **Seeed-Projects/Seeed-Jetson-DevelopTool** — Seeed (official) — MIT — largest third-party Jetson set (~95 skills): BSP build, JetPack flash incl. WSL2, OTA (Allxon), Frigate/Ollama/YOLO/DeepStream/GR00T deploy — nvidia, seeed.
- **Seeed-Studio/ai-skills** (rest) — Seeed Studio (official) — MIT — also cv181x-media, onnx-to-cvimodel (reCamera CV181x) — seeed, sophgo.
- **qualcomm/qai-appbuilder** (`tools/skills`) — Qualcomm (official) — verify LICENSE text before vendoring — QAIRT/QNN/SNPE conversion/quantization/NPU inference on Snapdragon; also qualcomm/cpp-aarch64-build-agent-skill (BSD-3) — qualcomm.
- **airockchip/clawchips** — Rockchip (official) — MIT — rk-asr/tts/vl/rag/benchmark/adb (Chinese-language; assumes on-device ModelHub) — rockchip.
- **D-Robotics/moss** (rest) — D-Robotics (official) — MIT — 20 skills: RDK X5/S100 board skills + jetson/rpi/rk knowledge packs — d-robotics.
- **luxonis/skills** — Luxonis (official) — Apache-2.0 — OAK/DepthAI bring-up→PoC→troubleshoot, ships as Claude Code plugin — luxonis.
- **hailo-ai/hailo-apps** + **hailo-media-library** — Hailo (official) — MIT — hl-build-* app skills, cross-compile (RPi AI Kit/HAT) — hailo, raspberry-pi.
- **TexasInstruments/tinyml-tensorlab** — TI (official) — BSD-3 — tinyml-workflow-agent: train→compile→CCS flash — ti.
- **renesas/renesas-skills** — Renesas (official) — BSD-3 — configure-renesas-debug — renesas.
- **analogdevicesinc/analog-attach** — Analog Devices (official) — Apache-2.0 — DTS/DTSO editing + remote deploy — analog-devices.
- **MicrosoftDocs/Agent-Skills** — Microsoft (official) — CC-BY-4.0 — azure-iot-edge/hub/operations/central/defender-for-iot subset — microsoft.
- Reference-only (repo-internal or ecosystem): **pigweed-project/pigweed** (Apache-2.0), **project-chip/connectedhomeip** Matter skills (Apache-2.0), **pytorch/executorch** executorch-kb, **alibaba/MNN** opencl-optimize, **edgeimpulse** example skills (BSD-3-Clear).

### Tier 2 — credible community (reference; per-skill read before any vendoring)

- **beriberikix/zephyr-agent-skills** — Jonathan Beri — Apache-2.0 — full 21-skill Zephyr catalog + zephyr-cli router (we vendor 2) — zephyr.
- **SensorsIot/Universal-Embedded-Workbench** — Andreas Spiess — MIT — 14 ESP32 flash-test workbench skills — espressif.
- **BrownFineSecurity/iothackbot** — Matt Brown (803★) — MIT — 13 IoT security-research skills; offensive by design — authorized security testing only — all.
- **arpitg1304/robotics-agent-skills** — community — Apache-2.0 — production ROS2 patterns; also wimblerobotics/ros2-copilot-skills (Apache-2.0, 158 Nav2/TF/costmap skills) — ros2.
- **andrewleech/claude-mpy-marketplace** — MicroPython core contributor — MIT — mpy-ci Docker CI — micropython.
- **BenGardiner/bitbake-yocto-agent-skills** (Apache-2.0) + **Higangssh/yocto-agent-skills** (MIT) — community — Yocto/BitBake — yocto.
- **easyzoom/aix-skills** — community — MIT — 75+ MCU library-integration skills (stm32-hal, nrf-connect, tflite-micro, lvgl, mcuboot…) — per-skill read before use — st, nordic.
- **wedsamuel1230/arduino-skills** — community — MIT — arduino-cli workflows — arduino.
- **sammcj/agentic-coding** — community — Apache-2.0 — raspberry-pi admin skill — raspberry-pi.

### Reference-only: unlicensed and GPL sources

- Unlicensed (reference-only until licensed; filing license-request issues recommended): **adafruit/Agent_Skills** (CircuitPython/I2C — official Adafruit!), **m5stack/AIFlow**, **themactep/thingino-skills**, **klutchell/claude-skills** (balenify), **mpous/ai-skills**, **pedrominatel/esp-workshops**.
- GPL — reference only, do not vendor: **sunfounder/pironman5** (GPL-2.0; also instructs curl|sudo bash from own repo), **wolfSSL/wolfHAL** (GPL-3.0), **ailyProject/aily-blockly** (GPL-3.0), **konosubakonoakua/xilinx-skills** (GPL-2.0).

### Warning: rejected sources

Do not install from aggregator/mirror skill collections without provenance (e.g. the
43.5k★ "agentic-awesome-skills" and its ~15 scraper mirrors): Snyk's ToxicSkills research
(2026) found prompt injection in ~36% of sampled aggregator skills. Watch for
brand-squatting orgs ("NVIDIA-dev", created 2026-03, is not NVIDIA), fake Anthropic
branding ("Anthropic-Cybersecurity-Skills" repos — no such skills exist in any anthropics
org), namespace collisions (Zephyr-the-deploy-platform ≠ Zephyr RTOS; pi ≠ Raspberry Pi;
pico ≠ RPi Pico), and unverifiable offensive-security bundles. Scraped marketplaces
(mcpmarket, lobehub, skillsllm, agent-skills.cc) are listings, not publishers. Always
resolve to the upstream publisher's own repository before installing anything.
