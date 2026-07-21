---
title: "nvcc fatal: Unsupported gpu architecture 'compute_110' — Thor is sm_110 and needs CUDA 13-era toolchains"
type: fix
company: nvidia
keys:
  - "nvcc fatal   : Unsupported gpu architecture 'compute_110'"
  - "compute_110"
  - "sm_110"
  - "no kernel image is available for execution on the device"
  - "cuda build fails on thor"
platform_versions: ["JetPack 7.x", "L4T 38.x", "CUDA 13.x"]
devices: [agx-thor]
status: verified
verified_on: "doc checked 2026-07-21 (forum-confirmed resolution, AGX Thor, JetPack 7.0)"
sources:
  - "https://forums.developer.nvidia.com/t/jetpack-7-0-thor-cumotion-curobo-build-fails-nvcc-fatal-unsupported-gpu-architecture-compute-110/348679"
  - "https://developer.nvidia.com/blog/whats-new-in-cuda-toolkit-13-0-for-jetson-thor-unified-arm-ecosystem-and-more"
  - "https://arnon.dk/matching-sm-architectures-arch-and-gencode-for-various-nvidia-cards/"
---
## Context
Building CUDA code on a Jetson AGX Thor (directly, or via a JIT extension path
like `torch.utils.cpp_extension` — cuRobo/cuMotion hit this) fails with
`nvcc fatal   : Unsupported gpu architecture 'compute_110'` (in the PyTorch case
followed by `RuntimeError: Error building extension`). Or a prebuilt binary runs
but every kernel launch dies with
`no kernel image is available for execution on the device`.

## Knowledge
### Root cause
Thor's Blackwell iGPU is CUDA compute capability **11.0**. Under CUDA 13.0+ that
is `sm_110` / `compute_110` (the same silicon was transitionally called `sm_101`
in CUDA 12.8/12.9 and renumbered in 13.0). Any component of the build chain that
predates CUDA 13 — an older nvcc, or a framework wheel built for cu126/cu128
whose arch list stops at sm_87/sm_90 — either rejects `compute_110` at compile
time or ships no sm_110 kernels, which surfaces at runtime as "no kernel image".

### Fix
1. Build with the CUDA 13 toolchain that JetPack 7 installs — check with
   `nvcc --version` (needs release 13.0+).
2. For your own code, target Thor explicitly:
   `-gencode=arch=compute_110,code=sm_110`
   (Jetson Orin remains `sm_87`; see `sdk-dev/cuda-arch-gencode-flags-per-module.md`.)
3. For PyTorch-based stacks, use a cu130 build — the resolution in the source
   thread:
   `python3 -m pip install torch==2.9.0+cu130 --index-url https://download.pytorch.org/whl/cu130`
4. For Isaac ROS / cuRobo / cuMotion, upgrade to Isaac ROS 4.0 — NVIDIA's
   confirmed answer: "Isaac ROS 4.0 has full support for JetPack 7.0 and AGX
   Thor" — instead of patching arch flags by hand.

## Verify
`nvcc --version` reports 13.x; a rebuild proceeds past the gencode step; and
`python3 -c "import torch; print(torch.cuda.get_device_capability())"` prints
`(11, 0)` on Thor with a working wheel.

## Gotchas
- `TORCH_CUDA_ARCH_LIST="11.0"` only helps if the underlying nvcc is CUDA 13+;
  with an older nvcc you get the same fatal.
- There is also `sm_110a` (arch-specific features, not forward-compatible) —
  don't ship `code=sm_110a` binaries expecting them to run on future chips.
- Containers built for L4T r36/CUDA 12 hit the runtime variant of this on Thor;
  use r38/JP7 (cu130) images instead.
