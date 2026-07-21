---
title: "Update or recover the Raspberry Pi 4/5 bootloader EEPROM — rpi-eeprom-update, and the Imager bootloader-recovery SD card"
type: recipe
company: raspberry-pi
keys:
  - "rpi-eeprom-update -a"
  - "rpi-eeprom-config --edit"
  - "Misc utility images"
  - "no hdmi output green led never blinks"
  - "corrupted bootloader recovery"
platform_versions: ["all"]
devices: [pi-5, pi-4]
status: verified
verified_on: "doc checked 2026-07-21 (raspberrypi.com raspberry-pi.html boot EEPROM; rpi-eeprom README)"
sources:
  - "https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#raspberry-pi-boot-eeprom"
  - "https://github.com/raspberrypi/rpi-eeprom/blob/master/README.md"
---
## Context
Pi 4/400/5/CM4/CM5 boot from an on-board SPI EEPROM bootloader (no more
bootcode.bin on the SD card). You need to update it (new features like NVMe
boot, PSU handling fixes) or recover a Pi that powers on with no HDMI output
and a green LED that never blinks. Recovery works regardless of the
installed OS (hence `all`); the update tooling ships in Raspberry Pi OS.

## Knowledge
Routine update from a running Pi OS:

```bash
sudo rpi-eeprom-update        # shows current vs latest available
sudo rpi-eeprom-update -a     # stages the update; applied on reboot
sudo reboot
```

Updates arrive through the apt `rpi-eeprom` package; which release channel
you track is `FIRMWARE_RELEASE_STATUS` in `/etc/default/rpi-eeprom-update`
(`default` vs `latest`; also switchable via `raspi-config` → Advanced →
Bootloader Version). Settings (BOOT_ORDER, PCIE_PROBE, POWER_OFF_ON_HALT…)
are edited with `sudo rpi-eeprom-config --edit` and survive updates.

Recovery when the EEPROM is corrupt (black screen, no LED activity):

1. On another computer, Raspberry Pi Imager → Choose OS →
   **Misc utility images** → Bootloader (Pi 4 / Pi 5 family) →
   **SD Card Boot** (or your preferred default boot mode).
2. Write it to any SD card, insert into the dead Pi, power on.
3. Success within ~10 s: the green activity LED blinks rapidly and
   continuously, and an attached HDMI display turns solid green.
4. Power off, remove the recovery card, boot normally.

## Verify
`sudo rpi-eeprom-update` reports `BOOTLOADER: up to date` with the new
timestamp; `vcgencmd bootloader_version` matches. After a recovery flash,
the Pi boots your OS storage again with default EEPROM settings.

## Gotchas
- Recovery resets EEPROM configuration — re-apply custom BOOT_ORDER /
  PCIE_PROBE afterwards (`rpi-eeprom-config --edit`).
- The green LED blink patterns are diagnostic (documented "LED warning
  flash codes" table) — e.g. repeating long/short patterns point at EEPROM
  or start-file errors; count them before assuming dead hardware.
- Use a known-good SD card and full power cycle for recovery; a marginal
  card can make recovery look like failure.
- CM4/CM5: EEPROM write-protect or `SELF_UPDATE` restrictions apply on some
  carrier boards — recovery there goes through `usbboot`/`rpiboot` instead.
