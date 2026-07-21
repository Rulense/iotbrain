---
title: "nvidia-smi 'No devices were found' on AGX Thor — GSP firmware init fails when the open/SBSA GPU driver wasn't applied"
type: fix
company: nvidia
keys:
  - "No devices were found"
  - "RmInitAdapter: Cannot initialize GSP firmware RM"
  - "kgspWaitForRmInitDone failed"
  - "thor gpu not detected"
  - "cuInit error 999"
platform_versions: ["JetPack 7.x", "L4T 38.x"]
devices: [agx-thor]
status: unverified
sources:
  - "https://forums.developer.nvidia.com/t/jetson-agx-thor-gpu-not-detected-nvidia-smi-no-devices-found-jetpack-7-1-l4t-38-4-0/357392"
  - "https://docs.nvidia.com/jetson/archives/r38.2/DeveloperGuide/IN/QuickStart.html"
---
## Context
An AGX Thor boots fine into Ubuntu 24.04 (JetPack 7.x), but the GPU is gone:
`nvidia-smi` prints `No devices were found`, `torch.cuda.is_available()` is
False, and `cuInit` returns error 999. `dmesg` shows the driver failing early:
`RmInitAdapter: Cannot initialize GSP firmware RM` and
`kgspWaitForRmInitDone failed` (kernel_gsp_gh100.c). Seen on JetPack 7.1 /
L4T 38.4.0, driver 580.65.06.

## Knowledge
### Root cause
Thor's GPU runs the SBSA-style open GPU driver stack, and its GSP (GPU System
Processor) firmware only initializes with that flavor installed. The official
rootfs prep for Thor is `sudo ./apply_binaries.sh --openrm` (Quick Start: "For
Jetson Thor devices"). An image prepared without it — typically a manual BSP
assembly or custom rootfs pipeline that reused Orin-era steps — boots, but the
GPU driver can't bring up GSP firmware, so no CUDA device exists.

### Fix
Per NVIDIA staff in the source thread: "you will need to flash the device with
--openrm. Since Thor requires SBSA driver to work." Concretely, on the flashing
host:
1. In `Linux_for_Tegra/`, re-run `sudo ./apply_binaries.sh --openrm` against
   your rootfs.
2. Reflash: `sudo ./l4t_initrd_flash.sh jetson-agx-thor-devkit internal`
   (see `setup/thor-devkit-unified-initrd-flash.md`).
SDK Manager's standard JetPack 7 flow applies the correct driver automatically —
this bites hand-rolled flashes.

## Verify
After reflash, `nvidia-smi` lists the Thor GPU, `dmesg | grep -i gsp` shows no
RmInitAdapter errors, and `python3 -c "import torch; print(torch.cuda.is_available())"`
prints True.

## Gotchas
- Marked unverified: the fix is NVIDIA-staff-stated in the thread, but the
  original poster never confirmed the reflash result there.
- Don't chase container/runtime settings first — if `nvidia-smi` fails on the
  host with GSP errors in dmesg, no `--runtime nvidia` flag will help.
- Error 999 (CUDA_ERROR_UNKNOWN) from cuInit on Thor is this class of problem
  (driver/firmware), not an application bug.
