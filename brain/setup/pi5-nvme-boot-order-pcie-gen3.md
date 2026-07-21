---
title: "Boot a Raspberry Pi 5 from NVMe — BOOT_ORDER=0xf416, PCIE_PROBE=1 for non-HAT+ adapters, PCIe gen 3 at your own risk"
type: recipe
company: raspberry-pi
keys:
  - "BOOT_ORDER=0xf416"
  - "rpi-eeprom-config --edit"
  - "PCIE_PROBE=1"
  - "dtparam=pciex1_gen=3"
  - "nvme drive not detected"
  - "boot from nvme ssd"
platform_versions: ["Raspberry Pi OS Bookworm+"]
devices: [pi-5]
status: verified
verified_on: "doc checked 2026-07-21 (raspberrypi.com raspberry-pi.html BOOT_ORDER + PCIe; rpi-eeprom README)"
sources:
  - "https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#BOOT_ORDER"
  - "https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#pcie-gen-3-0"
  - "https://github.com/raspberrypi/rpi-eeprom/blob/master/README.md"
  - "https://www.jeffgeerling.com/blog/2023/nvme-ssd-boot-raspberry-pi-5/"
---
## Context
Pi 5 with an M.2 HAT (official M.2 HAT+ or third-party) and an NVMe SSD:
you want to boot from the SSD, or the drive doesn't even show up in `lsblk`.
Boot order lives in the bootloader EEPROM, not in config.txt.

## Knowledge
```bash
sudo apt update && sudo apt full-upgrade -y
sudo rpi-eeprom-update -a        # recent bootloader first, then reboot
sudo rpi-eeprom-config --edit
```

Set (digits are tried right to left):

```
BOOT_ORDER=0xf416    # NVMe (6) → SD (1) → USB (4), f = retry/restart
PCIE_PROBE=1         # only needed for non-HAT+ M.2 adapters
```

- Pi 5 default is `BOOT_ORDER=0xf461` — NVMe is already in the list after
  SD, so with no SD card inserted an NVMe install boots without any edit;
  `0xf416` makes NVMe win even with a card present.
- `PCIE_PROBE=1`: HAT+ boards identify themselves over the HAT EEPROM and
  the port powers up automatically; non-HAT+ adapters need this to force
  PCIe enumeration (some also need `dtparam=pciex1` in
  `/boot/firmware/config.txt` on older firmware).
- Put the OS on the SSD with Raspberry Pi Imager (SSD in a USB enclosure or
  via rpi-imager on the running Pi), or clone the running SD with the
  SD Card Copier / `rpi-clone`.

PCIe speed: the connector is certified for gen 2 (5 GT/s). Gen 3 usually
works and roughly doubles NVMe throughput — enable via
`sudo raspi-config` → Advanced Options → PCIe Speed, or
`dtparam=pciex1_gen=3` in `/boot/firmware/config.txt` — but it is
explicitly not certified; drop back to gen 2 if you see I/O errors.

## Verify
`lsblk` shows `nvme0n1` with `/` mounted from `nvme0n1p2`. Power off, remove
the SD card, boot — the Pi comes up from NVMe. `sudo rpi-eeprom-config`
prints the saved BOOT_ORDER.

## Gotchas
- Drive present but never enumerated (nothing in `lsblk`, nothing in
  `dmesg | grep nvme`) on a third-party board → it's almost always the
  missing `PCIE_PROBE=1`.
- A minority of NVMe drives/controllers misbehave on the Pi 5 (especially
  forced to gen 3); check vendor compatibility lists before buying in bulk.
- M.2 SATA (B-key NGFF) drives don't work on NVMe M.2 HATs.
- FPC ribbon orientation/seating causes intermittent `nvme` timeouts —
  reseat before blaming the drive.
