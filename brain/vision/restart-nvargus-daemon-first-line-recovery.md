---
title: "Camera worked before, now every Argus open fails/times out — restart nvargus-daemon first"
type: fix
company: nvidia
keys:
  - "sudo systemctl restart nvargus-daemon"
  - "Connecting to nvargus-daemon failed: No such file or directory"
  - "(Argus) Error InvalidState: CaptureProvider destroyed"
  - "(Argus) Error Timeout: (propagating from src/rpc/socket/client/ClientSocketManager.cpp, function send(), line 137)"
  - "enableCamInfiniteTimeout"
  - "camera stopped working"
  - "camera open times out"
platform_versions: ["all"]
devices: [all]
status: verified
verified_on: "Orin Nano Super devkit, JetPack 6.2.1 (L4T 36.4.4), 2025-12-04 (forum-confirmed: daemon restart restored capture)"
sources:
  - "https://forums.developer.nvidia.com/t/imx219-csi-camera-not-working-on-jetson-orin-nano-super-kit/353583"
  - "https://docs.nvidia.com/jetson/archives/r36.4.4/DeveloperGuide/SD/CameraDevelopment/CameraSoftwareDevelopmentSolution.html"
  - "https://forums.developer.nvidia.com/t/argus-invalidstate-captureprovider-destroyed-camera-cannot-be-reopened-without-restarting-nvargus-daemon-orin-nano-jetpack-6-2/375325"
  - "https://forums.developer.nvidia.com/t/nvarguscamerasrc-timeout-error/241339"
---
## Context
A camera that previously worked suddenly fails on every open — Argus timeout,
`InvalidState`, or `Connecting to nvargus-daemon failed` — typically after an
app crashed / was Ctrl+C'd mid-capture, after long continuous streaming, or
after a boot where the daemon came up wrong. The V4L2 path (`v4l2-ctl`) still
works. Applies to all JetPacks: the daemon architecture is identical across
releases.

## Knowledge
### Root cause
All Argus capture state lives inside the `nvargus-daemon` system service, not
in your process. A client that dies without teardown, a daemon-internal error
after prolonged streaming, or a failed daemon start leaves that state stuck —
and then *every* new client fails until the daemon is restarted. In the
verified case (Orin Nano Super, JP 6.2.1) the sensor probed fine and v4l2
streamed at full rate, but Argus reported
`Connecting to nvargus-daemon failed: No such file or directory` until the
service was restarted.

### Fix
```
sudo systemctl restart nvargus-daemon
```
then retry the pipeline. To see what actually went wrong, watch the daemon
log while reproducing:
```
sudo journalctl -u nvargus-daemon -f
```
For sensors that legitimately stop streaming for long periods (triggered
sensors etc.), run the daemon with timeouts disabled (official option):
```
sudo service nvargus-daemon stop
sudo enableCamInfiniteTimeout=1 nvargus-daemon
```

## Verify
`gst-launch-1.0 nvarguscamerasrc num-buffers=30 ! fakesink` (or
`nvgstcapture-1.0`) captures without Argus errors right after the restart.

## Gotchas
- Restart is first aid, not a root-cause fix. If the error returns
  immediately with a freshly restarted daemon, the problem is the driver /
  device tree / cabling — see the "No cameras available" and V4L2-vs-Argus
  entries.
- JetPack 6.0–6.2 has a known long-run stability bug
  (`(Argus) Error InvalidState: CaptureProvider destroyed` after prolonged
  streaming, camera unrecoverable until daemon restart); NVIDIA states it is
  fixed in JetPack 6.2.2 / r36.5 — upgrade instead of scripting restarts.
- Restarting the daemon replaces `/tmp/argus_socket` — containers that
  bind-mounted the old socket file must be restarted too (see the Docker
  argus_socket entry).
- On multi-camera rigs the daemon has been seen to need a restart after boot
  before all sensors open reliably (AGX Xavier, JP 4.6.1 report).
