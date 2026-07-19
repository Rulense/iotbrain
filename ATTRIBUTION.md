# Attribution

This repository vendors third-party content. This file records provenance, licensing, and
exactly what was included or excluded.

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
