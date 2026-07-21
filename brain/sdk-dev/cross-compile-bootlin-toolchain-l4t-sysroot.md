---
title: "Cross-compiling for Jetson — Bootlin toolchain + L4T sysroot on x86, vs just building on-device"
type: recipe
company: nvidia
keys:
  - "CROSS_COMPILE"
  - "aarch64-buildroot-linux-gnu-"
  - "aarch64--glibc--stable-2022.08-1"
  - "TARGET_ROOTFS"
  - "--sysroot"
platform_versions: ["JetPack 5.x", "JetPack 6.x", "L4T 35.x", "L4T 36.x"]
devices: [all]
status: verified
verified_on: "Orin family, JetPack 6.x (L4T r36.x Developer Guide 'Jetson Linux Toolchain' + Multimedia API cross-platform support doc), docs checked 2026-07-17"
sources:
  - "https://docs.nvidia.com/jetson/archives/r36.5/DeveloperGuide/AT/JetsonLinuxToolchain.html"
  - "https://docs.nvidia.com/jetson/l4t-multimedia/cross_platform_support.html"
---
## Context
You need to build C/C++ (kernel, BSP, Multimedia API, or your app) for a
Jetson and are deciding between compiling on the device and cross-compiling
on an x86 host. Rule of thumb: on-device is simplest and always ABI-correct
(the compiler sees the real libs) but slow and RAM-bound; cross-compiling is
much faster but you must match NVIDIA's toolchain and give it a sysroot with
the target's exact libraries.

## Knowledge
### Official toolchain (r36.x)
NVIDIA specifies the Bootlin gcc 11.3.0 2022.08-1 aarch64 toolchain
(binutils 2.38, glibc 2.35), downloadable from the Jetson Linux page:

```bash
mkdir $HOME/l4t-gcc && cd $HOME/l4t-gcc
tar xf aarch64--glibc--stable-2022.08-1.tar.bz2
export CROSS_COMPILE=$HOME/l4t-gcc/aarch64--glibc--stable-2022.08-1/bin/aarch64-buildroot-linux-gnu-
```

(r35.x uses an older Bootlin gcc 9.3 toolchain — download the one linked
from YOUR release's docs, not the latest.)

### Sysroot for userspace apps
Per the Multimedia API cross-platform guide: clone the rootfs of a
provisioned device (backup flash produces a `.raw` image), mount it, and
point the compiler at it:

```bash
mkdir -p $HOME/jetson
sudo mount -t ext4 clone.img.raw $HOME/jetson
export TARGET_ROOTFS=$HOME/jetson
# then compile/link with:  --sysroot=$TARGET_ROOTFS
```

A `Linux_for_Tegra/rootfs` that has had `apply_binaries.sh` (plus any apt
packages you link against) also works as a sysroot.

### When to just build on-device
One-off builds, Python extensions, and anything with a deep dependency tree
(OpenCV, PyTorch) are usually less total effort on the Jetson itself — add
swap and max clocks first (see the on-device-builds entry in this domain).

## Verify
- `${CROSS_COMPILE}gcc --version` prints `aarch64-buildroot-linux-gnu-gcc (Buildroot ...) 11.3.0` (r36).
- `file yourbinary` on the host → `ELF 64-bit LSB ... ARM aarch64`; binary runs on the target.

## Gotchas
- Ubuntu's stock `aarch64-linux-gnu-gcc` cross-compiler often works for plain
  apps, but kernel/bootloader/BSP builds should use the Bootlin toolchain the
  docs name — glibc/gcc drift causes link and runtime symbol errors.
- The sysroot must match the target's JetPack: linking against a r36.3
  sysroot and deploying to r35.x fails on GLIBC version symbols.
- CUDA cross-compilation additionally needs the host `cuda-cross-aarch64`
  packages that SDK Manager installs; nvcc still needs the right
  `-gencode arch=compute_87,code=sm_87` for Orin (see the arch-flags entry).
