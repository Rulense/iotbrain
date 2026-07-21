# Attribution

This repository vendors third-party content. This file records provenance, licensing, and
exactly what was included or excluded.

> **Machine-read:** `scripts/check_drift.py` (weekly CI) parses each upstream's
> `- **Upstream repository:** https://github.com/<owner>/<repo>` and
> `- **Pinned commit:** ` `` `<sha>` `` bullets below to detect upstream drift.
> Keep that exact bullet format when adding or re-pinning an upstream.

## NVIDIA jetson-device-skills

- **Upstream repository:** https://github.com/NVIDIA-AI-IOT/jetson-device-skills
- **Pinned commit:** `0a803703b2e6fe4fc36e5dac3507bcde7fd8c9dc`
- **Upstream copyright:** Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
- **Licenses (dual):**
  - Source code (`scripts/*.sh`, `*.py`): **Apache-2.0**
  - Documentation (`SKILL.md`, `references/*.md`): **CC-BY-4.0**

### What was vendored

The following 9 skills were copied into `skills/<name>/`, preserving each skill's
`SKILL.md`, `scripts/`, and `references/` content:

| Skill | Files vendored |
|---|---|
| `jetson-diagnostic` | SKILL.md, scripts/ (common.sh, detect_jetson.sh, mem_summary.sh, runtime_probes.sh, snapshot.sh), references/ (nvmap-clients.md, tegrastats-fields.md) |
| `jetson-memory-audit` | SKILL.md, scripts/ (audit.sh, drop_caches.sh), references/ (DESIGN.md) |
| `jetson-headless-mode` | SKILL.md, scripts/ (plan.sh, apply.sh) |
| `jetson-inference-mem-tune` | SKILL.md, scripts/ (recommend.py) |
| `jetson-llm-serve` | SKILL.md |
| `jetson-llm-benchmark` | SKILL.md, scripts/ (bench_vllm.sh, bench_llama_cpp.sh, bench_ollama.sh) |
| `jetson-package` | SKILL.md, scripts/ (artifact_hints.sh), references/ (ghcr-images.md, pypi-jetson-ai-lab.md) |
| `jetson-speculative-decoding` | SKILL.md |
| `jetson-print-device-info` | SKILL.md |

**All vendored files are unmodified — byte-identical to the upstream files at the pinned
commit.** No changes were made to code or documentation, so no CC-BY-4.0 change-marking is
required. Upstream SPDX copyright/license headers in every script are preserved as-is.

Cross-skill layout note: several scripts source the shared detector at
`../../jetson-diagnostic/scripts/detect_jetson.sh`. Because all 9 skills are vendored as
siblings under `skills/`, these relative paths resolve exactly as they do upstream.

### What was excluded, and why

Excluded from every vendored skill directory:

- `skill.oms.sig` — NVIDIA's OMS signature files sign the original upstream packaging;
  any repackaging (such as vendoring into this plugin) invalidates them. Provenance is
  instead recorded here via the pinned commit and byte-identical guarantee.
- `skill-card.md` — upstream catalog/marketing card, not needed at runtime.
- `BENCHMARK.md` — upstream skill-eval benchmark results, not needed at runtime.
- `evals/` — upstream evaluation fixtures, not needed at runtime.

Also not vendored from the upstream repository:

- `agents/jetson-perf-investigator.md` — a Claude Code subagent that orchestrates these
  skills via repo-relative paths; it needs path adjustments to run standalone, so it is
  catalogued in `SKILLS-CATALOG.md` (Companion installs) instead of being bundled.
- `install.sh`, top-level `README.md`, `SECURITY.md` — installer and repo docs specific
  to the upstream layout.

### Security review

Prior to vendoring, every script and SKILL.md body in the 9 skills was reviewed for
network calls to non-NVIDIA hosts, pipe-to-shell patterns, credential exfiltration,
unguarded destructive commands, and prompt-injection-style instructions. No issues were
found; details are in the vendoring task report.

## Seeed Studio ai-skills

- **Upstream repository:** https://github.com/Seeed-Studio/ai-skills
- **Pinned commit:** `2746e676e81d85dc073e523407235725efe2f8ca`
- **Upstream copyright:** Copyright (c) 2026 Seeed Studio
- **License:** MIT (verified in upstream `LICENSE` at the pinned commit)

### What was vendored

| Skill | Files vendored |
|---|---|
| `ee-datasheet-master` | SKILL.md, README.md, PDF_STRATEGY.md, TEMPLATES.md, scripts/ (pdf_tools.py, requirements.txt) |
| `schematic-analyzer` | SKILL.md, README.md, SCHEMATIC_STRATEGY.md, patterns/ (i2c.yaml, usb.yaml), scripts/ (full tools tree + requirements.txt) |

**All vendored files are unmodified — byte-identical to the upstream files at the pinned
commit.** Excluded: `evals/` (evaluation fixtures) and `tests/` (upstream test suites) —
not needed at runtime.

## D-Robotics moss

- **Upstream repository:** https://github.com/D-Robotics/moss
- **Pinned commit:** `28fc435da4c0fcd7245fc85a0897d5039074190e`
- **Upstream copyright:** Copyright (c) 2025-2026 D-Robotics
- **License:** MIT (verified in upstream `LICENSE` at the pinned commit)

### What was vendored

| Skill | Files vendored |
|---|---|
| `rdk-peripheral-cookbook` | SKILL.md, references/ (gpio-commands.md, hardware-notes.md, rdk-can-and-board-io.md), scripts/can_mode.py |

Upstream path: `packages/moss-agent/assets/rdk-knowledge/skills/rdk-peripheral-cookbook/`.
**All vendored files are unmodified — byte-identical to the upstream files at the pinned
commit.** The complete skill directory was vendored (no exclusions were needed).

## Espressif esp-dl agent skills

- **Upstream repository:** https://github.com/espressif/esp-dl
- **Pinned commit:** `77a8a624a5c91c56a35e76ba5edc00fa32addd08`
- **Upstream copyright:** Copyright (c) 2021 Espressif Systems (Shanghai) Co., Ltd.
- **License:** MIT (verified in upstream `LICENSE` at the pinned commit)

### What was vendored

| Skill | Files vendored |
|---|---|
| `espdl-operator` | SKILL.md, references/ (esp-dl-templates.md, esp-ppq-checklist.md), assets/docker/ (Dockerfile, docker_requirements.txt) |
| `espdl-quantize` | SKILL.md, references/ (contract.md, decision_playbook.md, ppq_methods.md, setting_json_schema.md), scripts/ (analysis_helpers.py, apply_setting.py, compare_iterations.py, run_iteration.py), assets/ (example contracts, extra_requirements.txt) |

Upstream path: `tools/agents/skills/`. **All vendored files are unmodified —
byte-identical to the upstream files at the pinned commit.** Excluded from
`espdl-quantize`: `evals/` and `tests/` — not needed at runtime. Note: the two bundled
example contracts under `espdl-quantize/assets/example_quantize_*/` download calibration
data and pretrained weights from `dl.espressif.com`, pytorch.org, and Ultralytics/GitHub
when run; the skill's own scripts perform no network I/O.

## zephyr-agent-skills (Jonathan Beri)

- **Upstream repository:** https://github.com/beriberikix/zephyr-agent-skills
- **Pinned commit:** `ed63cdfb8cdfbeb5946ea39c33f4aa6bcf3a5cce`
- **License:** Apache-2.0 (verified in upstream `LICENSE` at the pinned commit)

### What was vendored

| Skill | Files vendored |
|---|---|
| `devicetree` | SKILL.md, references/ (dt_syntax.md, dt_bindings.md, dt_overlays.md), scripts/overlay_include_check.py, assets/app_overlay_template.overlay |
| `hardware-io` | SKILL.md, references/ (sensors.md, pinctrl_gpio.md, soc_config.md), scripts/gpio_alias_check.py, assets/sensor_poll_template.c |

**All vendored files are unmodified — byte-identical to the upstream files at the pinned
commit.** Excluded: `skill-meta.yaml` — matcher metadata for the upstream `zephyr-cli
skills suggest` tool, not consumed by the Claude Code skill loader.

### Security review (multi-vendor batch)

Prior to vendoring, every file in all 7 skill directories above (~29,600 lines) was given
a full-content security read for prompt-injection-style instructions, network calls to
non-vendor hosts, pipe-to-shell execution, credential access, and unguarded destructive
commands. All 7 skills passed; details are in the vendoring task report.

## License texts

Verbatim license texts for all vendored upstreams are included in `third_party_licenses/`. This repository itself is licensed under Apache-2.0 (see `LICENSE`).
