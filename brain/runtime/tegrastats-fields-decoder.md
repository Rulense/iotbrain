---
title: "Reading tegrastats output — RAM/lfb, SWAP, CPU %@MHz, EMC_FREQ, GR3D_FREQ, temps, VDD power rails"
type: matrix
company: nvidia
keys:
  - "tegrastats"
  - "GR3D_FREQ"
  - "EMC_FREQ"
  - "lfb"
  - "VDD_CPU_GPU_CV"
jetpack: ["all"]
l4t: ["all"]
devices: [all]
status: verified
verified_on: "Field definitions per NVIDIA L4T r36.5 and r35.6.2 Developer Guide (Tegrastats Utility); docs retrieved 2026-07-18"
sources:
  - "https://docs.nvidia.com/jetson/archives/r36.5/DeveloperGuide/AT/JetsonLinuxDevelopmentTools/TegrastatsUtility.html"
  - "https://docs.nvidia.com/jetson/archives/r35.6.2/DeveloperGuide/AT/JetsonLinuxDevelopmentTools/TegrastatsUtility.html"
---
## Context
`tegrastats` is the built-in live telemetry tool (`nvidia-smi` does not exist
on Jetson). One dense line per interval — this entry decodes the fields.
Applies to all Jetsons/JetPacks; exact field set varies by module (engines the
module lacks don't appear).

Sample (Orin Nano shape):
```
RAM 3162/7620MB (lfb 8x4MB) SWAP 0/3810MB (cached 0MB) CPU [1%@1510,0%@1510,...]
EMC_FREQ 0%@2133 GR3D_FREQ 0%@[305] VIC off APE 200 cpu@50.031C tj@50.031C
VDD_IN 4952mW/4952mW VDD_CPU_GPU_CV 1013mW/1013mW VDD_SOC 1544mW/1544mW
```

## Knowledge
| Field | Example | Meaning |
|---|---|---|
| `RAM X/Y (lfb NxZ)` | `RAM 3162/7620MB (lfb 8x4MB)` | Used/total RAM. `lfb` = largest contiguous free block: N blocks of Z MB. RAM includes GPU allocations — unified memory. |
| `SWAP X/Y (cached Z)` | `SWAP 0/3810MB (cached 0MB)` | Used/total swap (zram by default) plus swap cache. |
| `CPU [X%@F,...]` | `CPU [1%@1510,off,...]` | Per-core load % **relative to the core's current frequency** F (MHz); `off` = core offline. |
| `EMC_FREQ X%@F` | `EMC_FREQ 0%@2133` | Memory-controller bandwidth utilization % and EMC frequency (MHz). |
| `GR3D_FREQ X%@[F,...]` | `GR3D_FREQ 45%@[621]` | GPU busy % and per-GPC frequency (two GPC values on AGX Orin). |
| Engine fields | `NVDEC off`, `VIC 0%@115`, `APE 200` | Codec/vision/audio engines: frequency when active, `off` when power-gated. Modules without an engine omit it (Orin Nano has no NVENC). |
| Temps `name@T C` | `cpu@50.031C gpu@49.031C tj@50.031C` | Thermal zone temperatures; `tj` = highest junction temperature. |
| `VDD_* X/YmW` | `VDD_IN 4952mW/4952mW` | Rail power: instantaneous / average since tegrastats started. `VDD_IN` = total board input; `VDD_CPU_GPU_CV`, `VDD_SOC` = major internal rails. |

Useful invocations:
```bash
sudo tegrastats                       # sudo exposes extra fields on some releases
tegrastats --interval 1000            # ms between samples
tegrastats --logfile /tmp/tegrastats.log &
```

## Verify
Run a known GPU load (e.g. a TensorRT benchmark) — `GR3D_FREQ` % rises and
`VDD_IN` climbs; idle again drops both.

## Gotchas
- CPU % is relative to the **current** DVFS frequency: `100%@729` is far less
  work than `100%@1984`. Pin clocks (`sudo jetson_clocks`) before comparing
  runs — see `runtime/default-power-mode-caps-performance.md`.
- There is no per-process GPU memory: GPU usage lives inside the single `RAM`
  number (see `runtime/oom-killed-unified-memory.md`).
- Frequencies capped below max while util is high usually mean thermal or
  over-current throttling, not a nvpmodel setting — see
  `runtime/thermal-throttling-trip-points.md` and
  `runtime/over-current-throttling-warning.md`.
- For a friendlier view, `jtop` (pip package `jetson-stats`) renders the same
  counters interactively.
