---
title: "JetPack 7 aligns Jetson with SBSA — one CUDA 13 Arm toolkit for Thor and Arm servers, but Orin (sm_87) stays on the old path"
type: gotcha
company: nvidia
keys:
  - "Server Base System Architecture"
  - "SBSA"
  - "CUDA 13.0"
  - "sm_87"
  - "same cuda binary on server and jetson"
  - "separate jetson cuda toolkit"
platform_versions: ["JetPack 7.x", "CUDA 13.x", "L4T 38.x"]
devices: [agx-thor, agx-orin]
status: verified
verified_on: "doc checked 2026-07-21"
sources:
  - "https://developer.nvidia.com/blog/whats-new-in-cuda-toolkit-13-0-for-jetson-thor-unified-arm-ecosystem-and-more"
  - "https://forums.developer.nvidia.com/t/jetpack-7-0-jetson-linux-38-2-for-nvidia-jetson-thor-is-now-live/343128"
  - "https://github.com/OE4T/meta-tegra/blob/master/docs/release-notes/JetPack-7.0-L4T-R38.2.x-Notes.md"
---
## Context
Teams carrying JetPack 5/6 assumptions — "Jetson needs its own CUDA toolkit,
its own containers, binaries aren't portable off-device" — misplan JetPack 7
work in both directions: they keep maintaining split toolchains for Thor
(unnecessary), or they assume Orin got the same unification (it didn't).

## Knowledge
What SBSA alignment actually changes with JetPack 7 / CUDA 13 on Thor:

- **One Arm toolkit.** "CUDA 13.0 streamlines development for Arm platforms by
  unifying the CUDA toolkit across server-class and embedded devices" — no more
  separate SBSA-server vs Jetson-specific CUDA installs for Thor. Standard
  arm64 (SBSA) CUDA packaging is the Thor path.
- **Build once, deploy to Thor.** You can compile on an Arm server (e.g. GB200)
  and run the identical binary on Thor — the CUDA blog calls this out as a
  supported flow, which also lets CI consolidate on one container lineage.
- **The Orin exception (the gotcha):** "The only exception is Orin (sm_87),
  which will continue on its current path for now." Even on JetPack 7.2, Orin
  keeps the Jetson-specific CUDA integration — SBSA-only artifacts are not an
  Orin story. Plan separate build targets: sm_110 (Thor) via the unified
  toolkit, sm_87 (Orin) via the Jetson path.
- **Server-style platform pieces on Thor:** UEFI/SBSA firmware expectations,
  Ubuntu 24.04 + kernel 6.8 base, the open GPU driver with working `nvidia-smi`
  (JetPack 7.1 adds MIG), unified initrd flashing, and full-coherence unified
  virtual memory (GPU kernels can use plain `malloc()`/`mmap()` host memory).
- Toolchain cleanup: the old pinned-gcc-for-nvcc dance is gone (meta-tegra
  dropped its `gcc-for-nvcc` recipes because CUDA 13 accepts current compilers).

## Verify
On Thor: `nvidia-smi` works and `nvcc --version` reports 13.x from a standard
arm64 CUDA install. A CUDA binary built on an SBSA Arm server with
`-gencode=arch=compute_110,code=sm_110` runs unmodified on Thor.

## Gotchas
- Don't ship one "aarch64" artifact and expect Thor + Orin coverage: the unified
  toolkit covers Thor; Orin still needs its sm_87 Jetson-path build.
- SBSA alignment does not make Thor a dGPU system — it's still an iGPU with
  unified memory; sizing assumptions from PCIe GPUs (separate VRAM) stay wrong.
- Habits keyed to legacy L4T (e.g. parsing `/etc/nv_tegra_release`, Orin-era
  flashing flows) need re-checking on the r38+ layout before being scripted in.
