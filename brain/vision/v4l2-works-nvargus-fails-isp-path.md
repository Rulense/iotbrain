---
title: "v4l2-ctl captures frames but nvarguscamerasrc/Argus fails — the ISP path needs more than a working V4L2 driver"
type: gotcha
company: nvidia
keys:
  - "SCF: Error Timeout: ISP port 0 timed out!"
  - "LSC: LSC surface is not based on full res!"
  - "v4l2-ctl --list-devices"
  - "No cameras available"
  - "nvargus-daemon"
  - "camera works only with v4l2"
  - "isp pipeline fails"
platform_versions: ["all"]
devices: [all]
status: verified
verified_on: "Jetson Nano (custom Bayer sensor driver), JetPack 4.x, 2020-06-30 (forum thread solved: missing DT properties)"
sources:
  - "https://forums.developer.nvidia.com/t/can-get-images-using-v4l2-ctl-but-not-with-nvarguscamerasrc/129291"
  - "https://docs.nvidia.com/jetson/archives/r36.4.4/DeveloperGuide/SD/CameraDevelopment/CameraSoftwareDevelopmentSolution.html"
  - "https://forums.developer.nvidia.com/t/v4l2-ctl-works-however-nvarguscamerasrc-fails/257337"
---
## Context
Bringing up a custom or third-party CSI Bayer sensor: `v4l2-ctl --list-devices`
shows it and `v4l2-ctl --stream-mmap` captures raw frames, yet
`nvarguscamerasrc` / `argus_camera` fails (`No cameras available`, timeouts, or
black frames). Applies to every JetPack because the two-path capture
architecture (V4L2 direct vs Argus/ISP) is the same across L4T releases.

## Knowledge
There are two capture paths, and passing the first proves nothing about the
second:

- **V4L2 direct** (`v4l2-ctl`, `v4l2src`): kernel driver only, raw Bayer
  straight from the sensor, **bypasses the ISP**.
- **Argus** (`nvarguscamerasrc`, libargus apps via `nvargus-daemon`): routes
  through the ISP for debayer/AE/AWB, and additionally requires:
  1. A complete device-tree camera module definition — mode tables with every
     property from the reference sensor DT (e.g. imx219), including easy-to-omit
     ones like `physical_w`/`physical_h`, pixel clock, embedded metadata config,
     and a `proc-device-tree` path that exactly matches the i2c node name.
  2. Working V4L2 control (CID) implementations — Argus AE calls
     `set_exposure`/`set_gain`/frame-rate continuously; `v4l2-ctl` does not,
     so broken CIDs only surface under Argus (per the official camera doc).
  3. A clean CSI link — frame/CRC errors that raw V4L2 capture tolerates make
     Argus fail; there is no way to disable those checks (Argus is closed
     source). NVIDIA's guidance in that case: use a V4L2 app + software debayer.

In the solved source case, copying the missing properties from the reference
imx219 device tree fixed Argus ("Everything's working fine now").

## Verify
`argus_camera` or
`gst-launch-1.0 nvarguscamerasrc num-buffers=30 ! fakesink`
produces frames without errors in `journalctl -u nvargus-daemon`.

## Gotchas
- The real error is usually only in the daemon log
  (`sudo journalctl -u nvargus-daemon -f`), not in the GStreamer output —
  e.g. `SCF: Error Timeout: ISP port 0 timed out!` or
  `LSC: LSC surface is not based on full res!` (mode size vs DT mismatch).
- YUV sensors (UYVY etc.) never use the ISP — capture them with `v4l2src` or
  `nvv4l2camerasrc`; `nvarguscamerasrc` is for Bayer sensors only.
- Black frames from Argus while v4l2 works usually mean the MIPI link is
  marginal — recheck lane config/signal before blaming the DT.
