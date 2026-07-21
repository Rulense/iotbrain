---
title: "Decode vcgencmd get_throttled on Raspberry Pi — under-voltage bits, 0x50005, and the Pi 5 5A PSU / USB current limit"
type: matrix
company: raspberry-pi
keys:
  - "vcgencmd get_throttled"
  - "throttled=0x50005"
  - "Undervoltage detected!"
  - "This power supply is not capable of supplying 5A"
  - "usb_max_current_enable=1"
  - "low voltage warning keeps appearing"
  - "random reboots under load"
platform_versions: ["all"]
devices: [pi-5, pi-4, pi-zero-2w]
status: verified
verified_on: "doc checked 2026-07-21 (raspberrypi.com os.html vcgencmd + raspberry-pi.html power supply)"
sources:
  - "https://www.raspberrypi.com/documentation/computers/os.html#get_throttled"
  - "https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#power-supply"
  - "https://forums.raspberrypi.com/viewtopic.php?t=363783"
---
## Context
The Pi is slow, shows the lightning-bolt / "low voltage" desktop warning, or
reboots randomly under load, and you need to tell power trouble from thermal
trouble. `vcgencmd get_throttled` is the firmware's own verdict. The bit
layout has been stable across Pi OS releases for years (hence `all`); the
5 A PSU behavior is Pi 5-specific.

## Knowledge
```bash
vcgencmd get_throttled     # e.g. throttled=0x50005
```

| Bit | Mask     | Meaning (bits 0-3 = right now, 16-19 = since boot) |
|-----|----------|-----------------------------------------------------|
| 0   | 0x1      | Under-voltage detected                               |
| 1   | 0x2      | Arm frequency capped                                 |
| 2   | 0x4      | Currently throttled                                  |
| 3   | 0x8      | Soft temperature limit active                        |
| 16  | 0x10000  | Under-voltage has occurred                           |
| 17  | 0x20000  | Arm frequency capping has occurred                   |
| 18  | 0x40000  | Throttling has occurred                              |
| 19  | 0x80000  | Soft temperature limit has occurred                  |

- `throttled=0x0` — healthy. `0x50000` — under-voltage + throttling happened
  earlier (bits 16+18), fine now. `0x50005` — happening *right now*.
- Under-voltage events also land in the kernel log:
  `dmesg | grep -i voltage` → `hwmon hwmon1: Undervoltage detected!`
- Only 0x2/0x8 set with 0x1 clear → it's thermal, not the supply (see the
  temperature with `vcgencmd measure_temp`).

Pi 5 specifics: the recommended supply is USB-C PD 5 V / 5 A (25 W). On a
5 V / 3 A supply the Pi 5 boots but warns
"This power supply is not capable of supplying 5A. Power to peripherals will
be restricted." and caps total USB current at 600 mA (vs 1.6 A with a 5 A
PD supply). If you trust your supply, override with
`usb_max_current_enable=1` in `/boot/firmware/config.txt`.

## Verify
Fix the supply/cable, reboot (sticky bits clear only at boot), rerun
`vcgencmd get_throttled` under the same load — expect `throttled=0x0`.

## Gotchas
- Bits 16-19 are sticky since boot: `0x50000` on a long-running box may be
  one brownout weeks ago, not a live problem.
- The cable matters as much as the brick — thin USB cables drop enough volts
  to trip bit 0 on current spikes.
- `usb_max_current_enable=1` doesn't make a weak supply stronger; brownouts
  move from "USB devices misbehave" to "whole board resets".
