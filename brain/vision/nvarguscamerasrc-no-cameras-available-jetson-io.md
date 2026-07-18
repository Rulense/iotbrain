---
title: "nvarguscamerasrc 'No cameras available' with IMX219/IMX477 — apply CSI overlay with jetson-io"
type: fix
company: nvidia
keys:
  - "No cameras available"
  - "Error generated. /dvs/git/dirty/git-master_linux/multimedia/nvgstreamer/gst-nvarguscamera/gstnvarguscamerasrc.cpp, execute:751 No cameras available"
  - "imx219_board_setup: error during i2c read probe (-121)"
  - "jetson-io.py"
  - "nvarguscamerasrc"
jetpack: ["5.x", "6.x"]
l4t: ["35.x", "36.x"]
devices: [orin-nano, orin-nx, xavier-nx]
status: verified
verified_on: "Orin Nano devkit, JetPack 6 (L4T r36.4.4), 2025-09-19 (forum-confirmed solve)"
sources:
  - "https://forums.developer.nvidia.com/t/jetson-orin-nano-l4t-r36-4-4-nvarguscamerasrc-fails-with-no-cameras-available-for-waveshare-imx219-160-stereo-camera/345146"
  - "https://forums.developer.nvidia.com/t/orin-jetpack-6-0-no-config-for-imx-219-camera/286616"
  - "https://forums.developer.nvidia.com/t/jetson-orin-nano-imx219-not-detected-on-jetpack-6-error-121/333576"
  - "https://docs.nvidia.com/jetson/archives/r36.4.4/DeveloperGuide/HR/ConfiguringTheJetsonExpansionHeaders.html"
---
## Context
A Raspberry Pi camera (IMX219 / v2, IMX477 / HQ) or compatible module (Waveshare,
Arducam) is plugged into the devkit CSI connector, but any `nvarguscamerasrc`
pipeline fails immediately with `No cameras available` (the line number in the
error varies by release: `execute:521` / `execute:557` / `execute:751`).

## Knowledge
### Root cause
Two distinct failure classes:

1. **Overlay not applied (the JetPack 6 change).** On JetPack 6 / L4T r36.x the
   devkit device tree no longer enables camera sensor modules by default — the
   sensor's device-tree overlay must be applied manually with jetson-io. On
   JetPack 5 the RPi v2 cam was auto-detected, so people upgrading hit this cold.
   Symptom: no `/dev/video0`, no `imx219`/`imx477` lines in `dmesg`.
2. **I2C probe failure (physical).** `dmesg` shows
   `imx219_board_setup: error during i2c read probe (-121)` /
   `probe of 9-0010 failed with error -121` — the sensor is not answering on
   I2C: ribbon not seated, inserted backwards, wrong 15↔22-pin adapter cable,
   or a damaged connector clip.

### Fix
1. Check the kernel side first:
   `sudo dmesg | grep -iE "imx219|imx477|i2c"` — if you see `-121` probe
   errors, power off and reseat the ribbon (contacts facing the correct side,
   clip fully closed) or replace the cable. No software will fix `-121`.
2. Apply the overlay:
   `sudo /opt/nvidia/jetson-io/jetson-io.py`
   → *Configure Jetson 24pin CSI Connector* → *Configure for compatible
   hardware* → pick your module (e.g. **Camera IMX219 Dual**, **Camera IMX477
   Dual**, or a vendor entry like the IMX219 stereo modules) → *Save pin
   changes* → *Save and reboot to reconfigure pins*.
   The tool writes a `.dtbo` into `/boot/` and updates
   `/boot/extlinux/extlinux.conf`.
3. After reboot confirm the node exists: `ls /dev/video*` and
   `v4l2-ctl --list-devices`.

## Verify
```
gst-launch-1.0 nvarguscamerasrc num-buffers=60 ! "video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1,format=NV12" ! fakesink
```
runs to EOS with no `No cameras available` error. Or use `nvgstcapture-1.0`.

## Gotchas
- Re-flashing or a JetPack upgrade replaces the DTB in `/boot` — re-run
  jetson-io after every flash.
- `v4l2-ctl` listing the sensor does NOT mean Argus will work; see the
  companion entry on the V4L2-vs-Argus/ISP split.
- Grep for the stable substring `No cameras available` — the
  `gstnvarguscamerasrc.cpp` line number differs across L4T releases.
- If jetson-io has no entry for your module, the vendor must ship a `.dtbo`
  for your L4T version (drop it in `/boot`, jetson-io picks it up).
