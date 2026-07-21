---
title: "JetPack 7.x support matrix — 7.0/7.1 are Thor-only (L4T 38.x), Orin joins at JetPack 7.2 (L4T 39.2)"
type: matrix
company: nvidia
keys:
  - "JetPack 7.0"
  - "Jetson Linux 38.2"
  - "JetPack 7.2"
  - "L4T r39.2"
  - "jetpack 7 on orin"
  - "which jetpack supports thor"
platform_versions: ["JetPack 6.x", "JetPack 7.x", "L4T 36.x", "L4T 38.x", "L4T 39.x"]
devices: [agx-thor, agx-orin, orin-nx, orin-nano]
status: verified
verified_on: "doc checked 2026-07-21"
sources:
  - "https://forums.developer.nvidia.com/t/jetpack-7-0-jetson-linux-38-2-for-nvidia-jetson-thor-is-now-live/343128"
  - "https://github.com/OE4T/meta-tegra/blob/master/docs/release-notes/JetPack-7.0-L4T-R38.2.x-Notes.md"
  - "https://forums.developer.nvidia.com/t/jetpack-7-2-jetson-linux-r39-2-on-jetson-agx-orin-developer-kit-getting-started-and-feedback-thread/372156"
  - "https://forums.developer.nvidia.com/t/jetpack-7-2-jetson-linux-r39-2-on-jetson-orin-nano-developer-kit-getting-started-and-feedback-thread/372151"
  - "https://developer.nvidia.com/embedded/jetpack-archive"
---
## Context
You're deciding which JetPack to flash — or wondering why JetPack 7.0/7.1 refuses
to target your Orin. The JetPack 7 line launched Thor-only and only later picked
up Orin, so "JetPack 7 supports Orin" is true or false depending on the minor
version. Getting this wrong wastes a full download + flash cycle.

## Knowledge
| JetPack | L4T (Jetson Linux) | Devices | Base OS / stack |
|---------|--------------------|---------|-----------------|
| 6.x (6.0–6.2.x) | 36.x | Orin family only (AGX Orin, Orin NX, Orin Nano) | Ubuntu 22.04, kernel 5.15, CUDA 12.x |
| 7.0 | 38.2 | **AGX Thor devkit + T5000 only** | Ubuntu 24.04, kernel 6.8, CUDA 13, cuDNN 9.12, TensorRT 10.13 |
| 7.1 | 38.4 | AGX Thor only (adds MIG) | Ubuntu 24.04, kernel 6.8, CUDA 13 |
| 7.2 | 39.2 | Thor **and** the full Orin family (AGX Orin, Orin NX, Orin Nano) | Ubuntu 24.04, kernel 6.8, CUDA 13 |

- The 7.0 release notes are explicit: the release "supports **only** AGX Thor
  targets"; L4T R38.2.x does not support Orin hardware, and NVIDIA staff confirmed
  "JetPack 7 does not support AGX Orin currently" at launch.
- JetPack 7.2 (June 2026) is the first 7.x that brings the Thor-era stack
  (Ubuntu 24.04 / kernel 6.8 / CUDA 13) to Orin devkits.
- Orin on JetPack 6.x → 7.2 is a major-version migration: full reflash, no
  apt-upgrade path across majors (see `iot/fleet-ota-apt-vs-image-based.md`).
- Xavier and earlier never appear in the 6.x/7.x lines (JetPack 5.x was their last).

## Verify
On-device: `cat /etc/os-release` (24.04 = JP7-era) and `dpkg -l nvidia-l4t-core`
shows the L4T major (36/38/39). On the download side, the JetPack archive page
lists supported hardware per release.

## Gotchas
- Board-support matters more than brand: "supports Orin" at 7.2 means the devkits
  and modules listed in the 39.2 release notes — custom carriers need their
  vendor's BSP to catch up first.
- L4T 38.x board configs for Orin exist in the BSP tree but are "not usable and
  not supported" (OE4T release notes) — flashing them is a dead end.
- Ecosystem wheels/containers key off L4T major (r36 vs r38/r39); after moving an
  Orin to 7.2 you need cu130-era builds, not your JP6 cu126 stash.
