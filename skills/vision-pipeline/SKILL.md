---
name: vision-pipeline
description: Use for camera and vision-pipeline work on ANY edge device — sensor bring-up, capture (V4L2 / libcamera / Argus), GStreamer pipeline construction, inference integration (DeepStream, OpenCV, vendor runtimes), and RTSP/streaming out. Covers CSI and USB cameras on boards like NVIDIA Jetson (nvarguscamerasrc, nvvidconv, NVMM), Raspberry Pi (libcamera), and others. Consults the iotbrain before and during the work and distills verified learnings back.
---

# Vision Pipeline Builder

Camera → pipeline → inference → stream, on edge boards. The stable procedure
lives here; the volatile version-specific knowledge lives in the iotbrain at
`${CLAUDE_PLUGIN_ROOT}/brain/` and the user's overlay at `~/.iotbrain/local/`.
Follow the steps in order.

## Step 1 — Device facts first

If the board, vendor, and OS/SDK version are not already established this
session, run `iot-dev` Step 1 to collect them — never guess. Then add the
vision facts:
- Camera type and sensor model: CSI (IMX219, IMX477, …) or USB/UVC.
- `v4l2-ctl --list-devices` (package `v4l-utils`) — what the kernel sees now.
- If OpenCV will consume frames: does `cv2.getBuildInformation()` report
  GStreamer YES? (pip wheels usually don't.)

## Step 2 — Consult the brain BEFORE building

Grep the `vision/` and `ml-stack/` domains in both stores for the sensor
model, GStreamer element names, capture API, and (when debugging) VERBATIM
error text:

```bash
grep -ril "imx477\|nvarguscamerasrc\|libcamera\|appsink\|rtsp" \
  "${CLAUDE_PLUGIN_ROOT}/brain/vision/" "${CLAUDE_PLUGIN_ROOT}/brain/ml-stack/" \
  ~/.iotbrain/local/ 2>/dev/null
```

Read every hit, filter by `company` + version exactly as iot-dev Step 3
describes, and surface matching `gotcha` entries to the user BEFORE the stage
that would hit them — e.g. warn about ISP-path or container-socket traps up
front, not after an hour of debugging.

## Step 3 — Build the pipeline, stage by stage

Build incrementally; verify each stage produces real frames before adding the next.

1. **Sensor bring-up.** USB/UVC cameras enumerate as `/dev/video*` with no
   setup. CSI sensors need platform plumbing first: a device-tree overlay for
   the sensor (Jetson: `jetson-io`; Raspberry Pi: `dtoverlay=` in the boot
   config; other vendors: their DT mechanism). Then prove raw capture at the
   V4L2 level: `v4l2-ctl --stream-mmap --stream-count=30`. Know the trap the
   brain documents: V4L2 capturing does NOT prove the ISP path works — a
   raw-Bayer CSI sensor still needs the vendor ISP stack above the driver.
2. **Capture element per platform.** Jetson CSI → Argus (`nvarguscamerasrc`;
   the real errors are in the nvargus-daemon journal). Raspberry Pi CSI →
   libcamera (`libcamerasrc`). USB/UVC anywhere → `v4l2src`. Other vendor ISP
   stacks → their element (check the brain and vendor docs).
3. **GStreamer construction.** Grow the pipeline one element at a time with
   `gst-launch-1.0 … ! fakesink`, pinning caps (width/height/framerate/format)
   right after the source. Two conversion paths:
   - NVIDIA: keep frames in NVMM memory as long as possible; `nvvidconv`
     converts/scales and crosses the NVMM↔system boundary. The VIC cannot
     output BGR — the brain's recipe is `nvvidconv` → BGRx in system memory →
     `videoconvert` → BGR for OpenCV.
   - Generic: `videoconvert` (+ `videoscale`) in system memory — slower but
     works on every board.
4. **Inference integration.** Single stream into your own code → `appsink`
   (OpenCV `VideoCapture(pipeline, cv2.CAP_GSTREAMER)`). Multi-stream/batched
   analytics on NVIDIA → DeepStream (`nvstreammux` does the batching). Vendor
   runtime and model-format choices are version-volatile: take runtime/wheel
   pairings from the brain's `ml-stack/` `config`/`matrix` entries, never from
   memory.
5. **Streaming out.** RTSP via gst-rtsp-server (the test-launch helper wraps a
   pipeline string). Use the SoC's hardware encoder where it exists; fall back
   to `x264enc tune=zerolatency` where it doesn't — which modules lack an
   encoder is brain knowledge, not guesswork.

Verify end-to-end by consuming the output (frames counted, stream actually
played) — a pipeline that reaches PLAYING was not thereby verified.

## Step 4 — Defer to specific skills

When a more specific installed skill covers the doing, use it: the vendored
`jetson-*` skills for Jetson serving and memory work (`jetson-llm-serve`,
`jetson-inference-mem-tune`, `jetson-package`), `espdl-quantize` /
`espdl-operator` for NN models on ESP32-S3/P4, and the upstream DeepStream /
VSS / TAO skill sets catalogued in `SKILLS-CATALOG.md` for DeepStream app
development and video analytics. Consult the brain first either way — Steps
2–3 tell you which knowledge applies to this device before the specialist acts.

## Step 5 — Distill verified learnings

When something new was VERIFIED on the actual hardware — a pipeline played,
a conversion path produced correct frames, a camera fix held after reboot —
invoke the `brain-distill` skill. Distill working pipelines as `recipe`
entries and known-good element/caps combinations as `config` entries, not
just debug fixes.
