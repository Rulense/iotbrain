---
title: "Flash the Jetson AGX Thor devkit — unified initrd flashing only (l4t_initrd_flash.sh + apply_binaries.sh --openrm)"
type: recipe
company: nvidia
keys:
  - "l4t_initrd_flash.sh jetson-agx-thor-devkit internal"
  - "apply_binaries.sh --openrm"
  - "flash_l4t_t264_nvme.xml"
  - "SKIP_EEPROM_CHECK=1"
  - "thor flashing fails"
  - "flash agx thor devkit"
platform_versions: ["JetPack 7.x", "L4T 38.x"]
devices: [agx-thor]
status: verified
verified_on: "doc checked 2026-07-21"
sources:
  - "https://docs.nvidia.com/jetson/archives/r38.4/DeveloperGuide/SD/FlashingSupportJetsonThor.html"
  - "https://docs.nvidia.com/jetson/archives/r38.2/DeveloperGuide/IN/QuickStart.html"
  - "https://forums.developer.nvidia.com/t/unable-to-flash-thor-devkit/375392"
---
## Context
You're flashing an AGX Thor devkit from the command line (L4T r38.x). Thor uses
SBSA-aligned "unified" flashing: the Orin-era habit of calling `flash.sh`
directly does not apply — everything goes through the initrd flashing scripts,
and the rootfs prep step has a Thor-specific flag that's easy to miss.

## Knowledge
1. Download from the Jetson Linux page (developer.nvidia.com/linux-tegra):
   `Jetson_Linux_<ver>_aarch64.tbz2` + `Tegra_Linux_Sample-Root-Filesystem_<ver>_aarch64.tbz2`,
   extract, and populate `Linux_for_Tegra/rootfs/`.
2. Apply NVIDIA binaries — Thor requires the open/SBSA GPU driver flavor:
   `sudo ./apply_binaries.sh --openrm`
   (the Quick Start calls this out specifically "For Jetson Thor devices").
3. Host prerequisites: `sudo tools/l4t_flash_prerequisites.sh`
4. Recovery mode: power the carrier, hold RECOVERY, press RESET; connect the
   USB-C recovery port to the host.
5. Flash internal storage:
   `sudo ./l4t_initrd_flash.sh jetson-agx-thor-devkit internal`
   Variants:
   - rootfs A/B: `sudo ROOTFS_AB=1 ./l4t_initrd_flash.sh jetson-agx-thor-devkit internal`
   - external NVMe: `sudo ./l4t_initrd_flash.sh -c tools/kernel_flash/flash_l4t_t264_nvme.xml --external-device nvme0n1p1 jetson-agx-thor-devkit internal`
   - storage auto-detect wrapper: `sudo ./nvsdkmanager_flash.sh [--storage <dev>]`

## Verify
Flashing ends without errors; after a reset the board boots into Ubuntu 24.04
and `nvidia-smi` lists the Thor GPU (SBSA driver stack).

## Gotchas
- After flashing, the device sits at the initrd prompt by design — reset it
  (RESET button or `boardctl`) to boot Linux; that's not a hang.
- The docs warn a low-quality USB-C cable "might make the flashing process
  fail" — swap the cable before debugging anything else.
- EEPROM CRC-8 read failures abort the flash; `SKIP_EEPROM_CHECK=1` is the
  documented escape hatch.
- After a botched or interrupted flash, NVIDIA support's standard recovery is a
  clean full wipe: `sudo ./l4t_initrd_flash.sh --erase-all jetson-agx-thor-devkit internal`.
- Default external-device configs assume a ≥64 GB drive; smaller disks need
  `ROOTFSSIZE` adjusted.
- Production images should disable the initrd bash shell
  (`/etc/nv-update-initrd/list.d/disable_initrd_bash`) — the docs "strongly
  recommend" it.
- Skipping `--openrm` in step 2 produces a system that boots but has no GPU —
  see `runtime/thor-nvidia-smi-no-devices-gsp-openrm.md`.
