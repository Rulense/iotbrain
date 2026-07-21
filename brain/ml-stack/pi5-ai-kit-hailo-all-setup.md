---
title: "Set up the Raspberry Pi AI Kit / AI HAT+ (Hailo-8L/Hailo-8) on Pi 5 — hailo-all package, PCIe gen 3, hailortcli verify"
type: recipe
company: raspberry-pi
keys:
  - "sudo apt install hailo-all"
  - "hailortcli fw-control identify"
  - "hailo_yolov8_inference.json"
  - "dtparam=pciex1_gen=3"
  - "hailo device not detected"
  - "npu inference on raspberry pi"
platform_versions: ["Raspberry Pi OS Bookworm+", "kernel 6.6+"]
devices: [pi-5]
status: verified
verified_on: "doc checked 2026-07-21 (raspberrypi.com documentation/computers/ai.html)"
sources:
  - "https://www.raspberrypi.com/documentation/computers/ai.html"
  - "https://www.raspberrypi.com/documentation/accessories/ai-kit.html"
  - "https://github.com/hailo-ai/hailo-rpi5-examples"
---
## Context
Pi 5 with the AI Kit (M.2 HAT+ + Hailo-8L, 13 TOPS — since discontinued) or
an AI HAT+ (Hailo-8L 13 TOPS / Hailo-8 26 TOPS): you want the NPU visible
and running rpicam-apps/Picamera2 inference demos. Everything ships through
apt on 64-bit Raspberry Pi OS — no vendor SDK download needed.

## Knowledge
```bash
sudo apt update && sudo apt full-upgrade -y
sudo rpi-eeprom-update -a          # NPU needs a recent bootloader firmware
sudo raspi-config                  # Advanced Options → PCIe Speed → Yes (gen 3)
sudo reboot
sudo apt install hailo-all
sudo reboot
```

- `hailo-all` pulls the whole stack: Hailo kernel driver + firmware, HailoRT
  middleware, Tappas-core post-processing, and the rpicam-apps Hailo
  post-processing stages.
- PCIe gen 3 (`raspi-config`, or `dtparam=pciex1_gen=3` in
  `/boot/firmware/config.txt`) is the documented recommendation for full NPU
  throughput; the link runs gen 2 otherwise and inference fps drops.
- Demo assets install under `/usr/share/rpi-camera-assets/` — the Hailo ones
  are the `hailo_*.json` post-process files.

## Verify
```bash
hailortcli fw-control identify     # prints board: Hailo-8L / Hailo-8, fw version
rpicam-hello -t 0 --post-process-file /usr/share/rpi-camera-assets/hailo_yolov8_inference.json
```
Live camera preview with YOLOv8 boxes = driver, firmware, and camera path all
good. For Python pipelines, clone `hailo-ai/hailo-rpi5-examples`.

## Gotchas
- `hailortcli fw-control identify` failing / no `/dev/hailo0` → the PCIe link
  itself is down: reseat the FPC ribbon, check `lspci` for a Hailo device,
  and confirm firmware is current (`sudo rpi-eeprom-update`).
- The apt route is Raspberry Pi OS-only; on Ubuntu or other distros you're
  on Hailo's own installer and version matching is on you.
- Model zoo compiled artifacts (.hef) are chip-specific: Hailo-8L .hef files
  run on Hailo-8, but 26-TOPS Hailo-8 .hef files do not run on the 8L.
- The AI Kit is out of production — new purchases are AI HAT+ (13/26 TOPS);
  same software path (`hailo-all`).
