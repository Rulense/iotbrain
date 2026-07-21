---
title: "Recover an unbootable Jetson after a failed apt/OTA upgrade (forced recovery + reflash)"
type: recipe
company: nvidia
keys:
  - "EFI stub: ERROR: Invalid header detected on UEFI supplied FDT, ignoring"
  - "EFI stub: Generating empty DTB"
  - "sudo apt upgrade"
  - "0955:7e19"
  - "APX"
platform_versions: ["all"]
devices: [all]
status: verified
verified_on: "Xavier NX devkit, JetPack 5.0 DP, 2022-07-20 (forum thread marked solved via SDK Manager manual reflash)"
sources:
  - "https://forums.developer.nvidia.com/t/jetson-xavier-nx-unbootable-after-sudo-apt-update-sudo-apt-upgrade/221144"
  - "https://forums.developer.nvidia.com/t/ota-update-causing-unbootable-state/329253"
  - "https://docs.nvidia.com/jetson/l4t/Tegra%20Linux%20Driver%20Package%20Development%20Guide/updating_jetson_and_host.html"
---
## Context
After `sudo apt upgrade` pulled bootloader/kernel packages, or after an
image-based OTA (especially across major versions, e.g. L4T 35.x → 36.x), the
Jetson no longer boots: black screen, peripherals unpowered, or UEFI errors on
serial console such as `EFI stub: ERROR: Invalid header detected on UEFI
supplied FDT, ignoring` followed by `EFI stub: Generating empty DTB`
(bootloader/firmware left older than the new rootfs).

## Knowledge
A Jetson that fails to boot is almost never hard-bricked: forced recovery mode
lives in boot ROM and always works.

1. **Confirm it's recoverable.** Put the device in forced recovery (FC REC
   jumper/button held through a power cycle), connect USB to a host, check
   `lsusb` for `0955:xxxx NVIDIA Corp. APX` (e.g. `0955:7e19` = Xavier NX).
2. **Save data first if needed.** Rootfs contents will be erased by a reflash —
   from recovery you can back up with
   `sudo ./tools/backup_restore/l4t_backup_restore.sh -b <board>` (e.g.
   `jetson-orin-nano-devkit`; restore later with `-r`), or pull the SD/NVMe
   and mount it on another machine.
3. **Reflash with a matching release.** Easiest: SDK Manager, choosing
   **Manual** setup mode (device already in recovery, no auto-reset), and the
   JetPack version you want to land on. Equivalent CLI: matching L4T BSP +
   `flash.sh <board> mmcblk0p1` (eMMC devices) or the initrd-flash NVMe/SD
   command for Orin Nano/NX. This rewrites bootloader firmware *and* rootfs
   consistently — which is exactly what the half-done upgrade broke.

## Verify
Device boots to oem-config / login. `cat /etc/nv_tegra_release` shows the L4T
release you flashed, consistent across bootloader and rootfs.

## Gotchas
- Image-based OTA across major versions can update the rootfs but leave old UEFI
  firmware — that firmware/DTB mismatch is what the `EFI stub` errors indicate.
  Cross-major OTA needs the bootloader update path from the OTA docs, not just a
  rootfs image.
- On apt-managed devices, holding `nvidia-l4t-*` packages
  (`sudo apt-mark hold 'nvidia-l4t-*'`) prevents surprise bootloader updates on
  fleet machines until you can update deliberately.
- If even forced recovery does not enumerate, re-check cable/port/VM issues
  before declaring the board dead (see the recovery-mode detection entry).
