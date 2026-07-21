---
title: "Jetson boots with clock in the past after power-off (TLS/apt breaks) — RTC battery is on rtc0, but boot time comes from rtc1"
type: fix
company: nvidia
keys:
  - "hwclock -f /dev/rtc0"
  - "rtc1"
  - "hctosys"
  - "certificate is not yet valid"
  - "is not valid yet (invalid for another"
platform_versions: ["JetPack 5.x", "JetPack 6.x", "L4T 35.x", "L4T 36.x"]
devices: [agx-orin, orin-nx, orin-nano]
status: verified
verified_on: "AGX Orin devkit, JetPack 5.1.1 (L4T 35.3.1), 2023 (forum thread self-answered: hwclock -s systemd service held across reboots and power cycles)"
sources:
  - "https://forums.developer.nvidia.com/t/rtc-time-date-are-correct-but-system-time-date-are-reset-after-reboot/256963"
  - "https://forums.developer.nvidia.com/t/about-setting-the-rtc-time/279625"
---
## Context
A deployed Jetson that sat powered off (hours to weeks) boots with its clock in
the past — 1970, or a fixed date like the kernel build epoch — even though you
installed an RTC coin cell. Until NTP kicks in, everything TLS breaks: MQTT/HTTPS
fail with `certificate is not yet valid`, and `apt update` refuses with
`Release file for ... is not valid yet (invalid for another ...)`. Offline
devices never recover on their own.

## Knowledge
### Root cause
Orin-family Jetsons have **two** RTCs: `rtc0` on the PMIC — the one the coin
cell actually backs — and `rtc1` inside the Tegra SoC, which loses time when
power is cut. L4T configures `rtc1` as the boot time source (kernel `hctosys`,
chosen for accuracy), so the battery-backed time in `rtc0` is never read at
boot: system time resets even with a healthy battery.

### Fix
1. Fit the coin cell to the carrier's RTC backup connector and set `rtc0` once
   the system clock is correct (e.g. after NTP sync):
   ```
   sudo hwclock -f /dev/rtc0 -w      # write system time -> PMIC RTC
   ```
2. Read `rtc0` into the system clock at every boot with a oneshot unit,
   `/etc/systemd/system/rtc0-hctosys.service`:
   ```
   [Unit]
   Description=Set system time from battery-backed rtc0
   DefaultDependencies=no
   Before=sysinit.target
   After=systemd-modules-load.service

   [Service]
   Type=oneshot
   ExecStart=/sbin/hwclock -f /dev/rtc0 -s

   [Install]
   WantedBy=sysinit.target
   ```
   `sudo systemctl daemon-reload && sudo systemctl enable rtc0-hctosys.service`
3. Keep NTP for drift correction when online (default `systemd-timesyncd`, or
   chrony — its default `makestep 1 3` jumps large offsets at startup). Write
   the corrected time back to `rtc0` periodically or on shutdown.

The kernel-level fix — `CONFIG_RTC_HCTOSYS_DEVICE="rtc0"` — works (confirmed in
source thread 279625) but requires rebuilding and reflashing the kernel;
the systemd unit gets the same result without touching the BSP.

## Verify
`sudo hwclock -f /dev/rtc0 -r` shows the right time. Then: power the device off
(unplugged) for several minutes, boot it **without network**, and `date` is
still correct. `dmesg | grep rtc` shows which RTC provided `hctosys`.

## Gotchas
- Setting the date with `date -s`/NTP alone fixes only the running system —
  nothing persists to `rtc0` unless something runs `hwclock -w` against it.
- `timedatectl` and plain `hwclock` may show the wrong RTC: plain `hwclock`
  follows `/dev/rtc`, which L4T points at `rtc1`. Always pass `-f /dev/rtc0`.
- Devkit RTC connectors are for a **3V coin cell**; on Orin Nano/NX carriers,
  check the carrier spec for the 2-pin connector polarity.
- Boot-time services that need TLS (fleet agents, MQTT) race NTP on first
  boot after power loss — the rtc0 unit above closes that window.
