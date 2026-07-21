---
title: "Flash Jetson Orin Nano devkit to NVMe SSD with l4t_initrd_flash.sh"
type: recipe
company: nvidia
keys:
  - "l4t_initrd_flash.sh"
  - "flash_l4t_t234_nvme.xml"
  - "--external-device nvme0n1p1"
  - "jetson-orin-nano-devkit"
  - "l4t_flash_prerequisites.sh"
platform_versions: ["JetPack 6.x", "L4T 36.x"]
devices: [orin-nano, orin-nx]
status: verified
verified_on: "Orin Nano devkit, JetPack 6.2 (L4T r36.4.3 official Quick Start), doc checked 2026-07-17"
sources:
  - "https://docs.nvidia.com/jetson/archives/r36.4.3/DeveloperGuide/IN/QuickStart.html"
  - "https://docs.nvidia.com/jetson/archives/r36.4.3/DeveloperGuide/SD/FlashingSupport.html"
---
## Context
You want to install JetPack 6 directly onto an NVMe SSD in the Orin Nano devkit
(no SD card), or the SD-card image path isn't an option (Orin NX module, custom
rootfs). The Orin Nano/NX has no eMMC, so plain `flash.sh` to "internal" storage
is not the route — external-storage flashing uses the initrd flash tools.

## Knowledge
On the x86 host (Ubuntu 20.04/22.04), from the extracted `Linux_for_Tegra/` of the
matching L4T BSP + sample rootfs:

```bash
# one-time host setup
sudo ./tools/l4t_flash_prerequisites.sh
sudo ./apply_binaries.sh
```

Put the devkit in forced recovery (jumper FC REC to GND on the button header
before powering on), connect USB-C to the host, then:

```bash
sudo ./tools/kernel_flash/l4t_initrd_flash.sh --external-device nvme0n1p1 \
  -c tools/kernel_flash/flash_l4t_t234_nvme.xml \
  -p "-c bootloader/generic/cfg/flash_t234_qspi.xml" \
  --showlogs --network usb0 jetson-orin-nano-devkit internal
```

This flashes QSPI bootloader firmware *and* the rootfs onto the NVMe over the
USB network (usb0). The same command with `--external-device sda1` targets a USB
drive, or `mmcblk0p1` an SD card. The `jetson-orin-nano-devkit` config covers
both Orin Nano and Orin NX modules on the p3768 carrier.

## Verify
Remove the jumper, reboot: device boots from NVMe into oem-config / first-boot
setup. On the device, `lsblk` shows `/` mounted from `nvme0n1p1`.

## Gotchas
- The QSPI partition layout path changed in r36: `bootloader/generic/cfg/...`
  (r35 used `bootloader/t186ref/cfg/...`) — old r35 commands fail on r36 BSPs.
- Two NVMe drives installed: slot C4 enumerates as `nvme0n1`, slot C7 as
  `nvme1n1` — point `--external-device` at the right one.
- Host must be bare-metal Ubuntu; the initrd flash's USB re-enumeration is
  unreliable through VM passthrough.
- `l4t_flash_prerequisites.sh` matters: missing host packages (e.g. sshpass,
  abootimg) produce confusing mid-flash failures.
