---
title: "JetPack 6 SD image stuck at first boot / End-user configuration on Orin Nano — QSPI firmware too old"
type: fix
company: nvidia
keys:
  - "A start job is running for End-user configuration after initial OEM installation"
  - "oem-config"
  - "nvidia-l4t-jetson-orin-nano-qspi-updater"
  - "nv-l4t-bootloader-config"
jetpack: ["6.x"]
l4t: ["36.x"]
devices: [orin-nano]
status: verified
verified_on: "Orin Nano devkit, JetPack 6.x update path (official NVIDIA firmware-update doc), doc checked 2026-07-17"
sources:
  - "https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/update_firmware.html"
  - "https://forums.developer.nvidia.com/t/suject-jetson-orin-nano-stuck-at-end-user-configuration-during-first-boot-jetpack-6-x-dear-support-team-i-am-experiencing-a-persistent-issue-w/361108"
---
## Context
Fresh JetPack 6.x SD card in an Orin Nano devkit: first boot hangs (sometimes for
hours) at

```
[***] (1 of 2) A start job is running for End-user configuration after initial OEM installation
```

or the oem-config wizard never appears / the device boot-loops before setup.
Common on devkits bought earlier that shipped with JetPack 5-era factory firmware.

## Knowledge
### Root cause
The SD card image only contains the OS — the bootloader lives in QSPI flash on
the module. NVIDIA's docs state some devkits "shipped with factory firmware that
cannot boot JetPack 6.x": QSPI firmware older than 36.0 cannot boot a JetPack 6
SD image.

### Fix
First check the firmware version: press Esc repeatedly at the NVIDIA splash to
enter UEFI setup; the firmware version line is near the top. If it is older than
36.0, either:

**A. SD-card-only update path (no host PC):**
1. Boot the bridge image `JP513-orin-nano-sd-card-image_b29.zip` (JetPack 5.1.3
   from its release page) and complete setup.
2. `sudo systemctl status nv-l4t-bootloader-config` (confirm a bootloader update
   is scheduled), then `sudo reboot` — firmware updates to 35.x.
3. `sudo apt update && sudo apt install nvidia-l4t-jetson-orin-nano-qspi-updater`
   then reboot again — QSPI updates to the 36.x-capable layout.
4. Power off, insert the JetPack 6 SD card, boot.

**B. Host PC path:** full flash with SDK Manager (or `l4t_initrd_flash.sh`) in
forced recovery mode — this rewrites QSPI firmware and OS together. This is also
NVIDIA support's standard answer when first boot is stuck.

## Verify
UEFI setup screen reports firmware 36.x, and the JetPack 6 SD card reaches the
oem-config screen and completes first boot.

## Gotchas
- Headless: the firmware version is also visible over the serial console on the
  button header (RXD pin 3, TXD pin 4, GND pin 7, 115200 baud).
- The same brief "End-user configuration" message on a *working* setup is normal
  for a minute or two — the problem is when it never completes.
- Re-imaging the SD card repeatedly cannot fix this; the stale firmware is on the
  module, not the card.
