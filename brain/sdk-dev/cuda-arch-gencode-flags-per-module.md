---
title: "CUDA gencode/arch flags per Jetson module — Orin is sm_87, Xavier is sm_72 (wrong arch = no kernel image)"
type: matrix
company: nvidia
keys:
  - "-gencode arch=compute_87,code=sm_87"
  - "-gencode arch=compute_72,code=sm_72"
  - "no kernel image is available for execution on the device"
  - "named symbol not found"
  - "CMAKE_CUDA_ARCHITECTURES"
  - "CUDA_ARCH_BIN"
jetpack: ["all"]
l4t: ["all"]
devices: [all]
status: verified
verified_on: "Orin Nano Super, JetPack 6.2, 2025 (GitHub issue: PyPI aarch64 wheel built for sm75/80/90 failed at first kernel launch; source build with compute capability 87 fixed it)"
sources:
  - "https://github.com/bitsandbytes-foundation/bitsandbytes/issues/1930"
  - "https://arnon.dk/matching-sm-architectures-arch-and-gencode-for-various-nvidia-cards/"
  - "https://proventusnova.com/blog/opencv-cuda-jetson-installation-guide/"
  - "https://developer.ridgerun.com/wiki/index.php/NVIDIA_Jetson_AGX_Thor/Blackwell_GPU"
---
## Context
You are compiling CUDA code (your own kernels, OpenCV, bitsandbytes, any
CMake/CUDA project) for a Jetson. Jetson iGPUs have their own compute
capabilities that desktop-oriented build defaults usually omit — a binary
without your module's arch dies at the first kernel launch with
`no kernel image is available for execution on the device` (or, for
lazily-loaded kernels, `named symbol not found`). Applies to every JetPack
release because the arch is a hardware property of the module.

## Knowledge
| Module | Compute capability | nvcc flag | CMake `CMAKE_CUDA_ARCHITECTURES` | OpenCV `CUDA_ARCH_BIN` |
|---|---|---|---|---|
| Orin Nano / Orin NX / AGX Orin | 8.7 | `-gencode arch=compute_87,code=sm_87` | `87` | `8.7` |
| Xavier NX / AGX Xavier | 7.2 | `-gencode arch=compute_72,code=sm_72` | `72` | `7.2` |
| TX2 | 6.2 | `-gencode arch=compute_62,code=sm_62` | `62` | `6.2` |
| Nano / TX1 | 5.3 | `-gencode arch=compute_53,code=sm_53` | `53` | `5.3` |
| AGX Thor | 11.0 (CUDA 13; was named sm_101 in CUDA 12.8/12.9) | `-gencode arch=compute_110,code=sm_110` | `110` | `11.0` |

- CMake >= 3.18: `cmake -DCMAKE_CUDA_ARCHITECTURES=87 ..` (or
  `set(CMAKE_CUDA_ARCHITECTURES 87)` before enabling the CUDA language).
- OpenCV: `-D CUDA_ARCH_BIN=8.7 -D CUDA_ARCH_PTX=` — cmake output should show
  `NVIDIA GPU arch: 87`.
- sm_87 needs CUDA >= 11.4; sm_110 needs CUDA 13.

## Verify
- Device reports its arch: `python3 -c "import torch; print(torch.cuda.get_device_capability())"`
  → `(8, 7)` on any Orin; or run cuda-samples `deviceQuery`.
- Binary actually contains it: `cuobjdump --list-elf <binary_or_.so> | grep sm_87`.

## Gotchas
- Orin is sm_87, NOT sm_80/sm_86; Xavier is sm_72, NOT sm_70. The iGPUs have
  Jetson-specific minor versions, so desktop arch lists never cover them —
  the bitsandbytes aarch64 wheels (sm75/sm80/sm90) launched fine on servers
  and failed on every Orin.
- Projects that "auto-detect" arch on the build machine mis-detect when you
  cross-compile on x86; pin the arch explicitly.
- Emitting PTX for an older arch (e.g. `compute_72`) lets newer devices JIT
  the kernels, but with a long first-launch JIT stall on device; for a known
  fleet, list each real sm instead.
