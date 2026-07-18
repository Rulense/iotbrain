---
title: "Correct board-config names for flashing Orin devkits on L4T r36.x (stale names break boot)"
type: matrix
company: nvidia
keys:
  - "jetson-orin-nano-devkit"
  - "jetson-orin-nano-devkit-super"
  - "jetson-agx-orin-devkit"
  - "jetson-orin-nano-devkit-nvme"
  - "flash.sh"
jetpack: ["6.x"]
l4t: ["36.x"]
devices: [orin-nano, orin-nx, agx-orin]
status: verified
verified_on: "Orin Nano/NX/AGX Orin devkits, JetPack 6.2 (L4T r36.4.3 official Quick Start table), doc checked 2026-07-17"
sources:
  - "https://docs.nvidia.com/jetson/archives/r36.4.3/DeveloperGuide/IN/QuickStart.html"
  - "https://github.com/orgs/OE4T/discussions/1304"
---
## Context
`flash.sh` / `l4t_initrd_flash.sh` take a `<board>` config argument. Passing a
config name copied from an old tutorial or a different L4T release can either
fail immediately or — worse — appear to flash successfully and then not boot.

## Knowledge
Board-config matrix for L4T r36.x (JetPack 6), from the official Quick Start:

| Module | Carrier | Config name |
|---|---|---|
| Orin Nano 8GB / 4GB (production) | P3768-0000 (Orin Nano devkit carrier) | `jetson-orin-nano-devkit` (or `jetson-orin-nano-devkit-super` for Super/MAXN modes) |
| Orin NX 16GB / 8GB | P3768-0000 (same carrier) | `jetson-orin-nano-devkit` (or `-super`) |
| AGX Orin 32GB / 64GB devkit | P3737-0000 | `jetson-agx-orin-devkit` |

Key points:
- Orin NX modules on the Orin Nano devkit carrier use the **Orin Nano** devkit
  config — there is no separate `jetson-orin-nx-devkit` config for that carrier.
- The config resolves the module SKU at flash time via EEPROM, which is why one
  name covers several modules.
- Config names are release-specific. r35-era names/variants (e.g. the
  `jetson-orin-nano-devkit-nvme` machine used by some r35 guides and Yocto
  layers) are stale on r36: a real-world report shows an image built with the
  r35-era nvme variant flashing fine but failing to boot the kernel after moving
  to 36.3, fixed by switching to the correct r36 config.
- Ground truth for your BSP: the `*.conf` files at the top of `Linux_for_Tegra/`
  — every valid `<board>` argument is one of those filenames minus `.conf`.

## Verify
`ls Linux_for_Tegra/jetson*.conf` lists the name you are about to pass; the
flash log identifies the right module (e.g. p3767) from EEPROM; the device boots
to oem-config after flashing.

## Gotchas
- Orin Nano/NX have no eMMC: with these configs the rootfs target must be an
  external device (`l4t_initrd_flash.sh --external-device nvme0n1p1 ... internal`)
  or SD — a plain `flash.sh jetson-orin-nano-devkit mmcblk0p1` internal-eMMC
  invocation has nothing to flash to.
- A "successful" flash with a wrong config is still wrong — boot failure shows up
  only afterwards, often as a kernel that never starts (nothing after UEFI).
