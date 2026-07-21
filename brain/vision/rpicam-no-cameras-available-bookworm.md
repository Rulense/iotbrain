---
title: "rpicam-hello 'ERROR: *** no cameras available ***' on Bookworm — dtoverlay in /boot/firmware/config.txt, and raspistill is gone"
type: fix
company: raspberry-pi
keys:
  - "ERROR: *** no cameras available ***"
  - "rpicam-hello --list-cameras"
  - "camera_auto_detect=0"
  - "dtoverlay=imx708"
  - "raspistill: command not found"
  - "camera not detected"
platform_versions: ["Raspberry Pi OS Bookworm+", "kernel 6.6"]
devices: [pi-5, pi-4, pi-zero-2w]
status: verified
verified_on: "doc checked 2026-07-21 (raspberrypi.com camera_software.html)"
sources:
  - "https://www.raspberrypi.com/documentation/computers/camera_software.html"
  - "https://forums.raspberrypi.com/viewtopic.php?t=362707"
  - "https://forums.raspberrypi.com/viewtopic.php?t=375197"
---
## Context
A CSI camera on Raspberry Pi OS Bookworm or later: `rpicam-hello` prints
`ERROR: *** no cameras available ***`, or an old guide tells you to run
`raspistill` and the command doesn't exist. Bookworm renamed the apps
(`libcamera-hello` → `rpicam-hello`) and removed the legacy stack entirely —
`raspistill`/`raspivid` are gone and will never support current modules.

## Root cause
Official modules (v1 OV5647, v2 IMX219, v3 IMX708, HQ IMX477, GS IMX296) are
auto-detected by default (`camera_auto_detect=1`). The error means either the
sensor never enumerated (cable/connector), the sensor needs an explicit
overlay (third-party or clone sensors), or the overlay was written to the
wrong config.txt — on Bookworm the live file is `/boot/firmware/config.txt`,
not `/boot/config.txt`.

## Fix
1. Cable first: contacts seated, right orientation, camera end too. Pi 5 uses
   the smaller 22-pin FPC connector — v1/v2/HQ cameras need the 22-to-15-pin
   cable. Check enumeration: `dmesg | grep -iE 'imx|ov5647'`.
2. For a sensor that isn't auto-detected, in `/boot/firmware/config.txt`:
   ```
   camera_auto_detect=0
   dtoverlay=imx219        # or ov5647 / imx477 / imx708 / imx296 / ov9281
   ```
   Pi 5 / CM: two connectors — append `,cam0` for CAM/DISP 0
   (`dtoverlay=imx219,cam0`); default is cam1.
3. Reboot, then:
   ```bash
   rpicam-hello --list-cameras
   ```

## Verify
`rpicam-hello --list-cameras` lists the sensor with its modes;
`rpicam-hello -t 5000` shows a preview. In Python use Picamera2 (the legacy
`picamera` module is equally dead on Bookworm).

## Gotchas
- Editing `/boot/config.txt` on Bookworm creates an ignored orphan file — the
  boot partition is mounted at `/boot/firmware/` (see the setup entry on the
  Bookworm /boot move).
- IMX290/IMX327 need the clock parameter:
  `dtoverlay=imx290,clock-frequency=74250000` (or 37125000).
- `libcamera-hello` still exists on early Bookworm as a transition alias;
  scripts should use the `rpicam-*` names.
