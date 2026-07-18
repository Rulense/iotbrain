---
title: "RTSP streaming from a Jetson camera with the hardware encoder (nvv4l2h264enc + gst-rtsp-server test-launch)"
type: recipe
company: nvidia
keys:
  - "nvv4l2h264enc"
  - "test-launch"
  - "rtph264pay name=pay0 pt=96"
  - "rtsp://127.0.0.1:8554/test"
  - "gst-rtsp-server"
jetpack: ["4.x", "5.x", "6.x"]
l4t: ["32.x", "35.x", "36.x"]
devices: [nano, xavier-nx, agx-xavier, orin-nx, agx-orin]
status: verified
verified_on: "Jetson Nano, JetPack 4.2.x, 2019-10-21 (poster confirmed 'it is streaming')"
sources:
  - "https://forums.developer.nvidia.com/t/live-streaming-on-the-nano-via-rtsp-test-launch-server/83505"
  - "https://developer.ridgerun.com/wiki/index.php/Jetson_Nano/Gstreamer/Example_Pipelines/Streaming"
---
## Context
You want to serve the CSI camera as a low-latency RTSP stream, encoding on the
Jetson's NVENC hardware block instead of the CPU. The stock tool for this is
the `test-launch` example from gst-rtsp-server.

## Knowledge
1. Build `test-launch` (once):
   ```
   sudo apt install libgstrtspserver-1.0-dev
   # grab test-launch.c from the gst-rtsp-server examples matching
   # your GStreamer version (gst-launch-1.0 --version)
   gcc test-launch.c -o test-launch \
       $(pkg-config --cflags --libs gstreamer-1.0 gstreamer-rtsp-server-1.0)
   ```
2. Serve the camera:
   ```
   ./test-launch "nvarguscamerasrc ! video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1,format=NV12 ! nvv4l2h264enc insert-sps-pps=true idrinterval=15 ! video/x-h264,profile=baseline,stream-format=byte-stream ! h264parse ! rtph264pay name=pay0 pt=96 config-interval=1"
   ```
   It prints `stream ready at rtsp://127.0.0.1:8554/test`.
3. Play from another machine:
   `vlc rtsp://<jetson-ip>:8554/test` or
   `gst-launch-1.0 uridecodebin uri=rtsp://<jetson-ip>:8554/test ! autovideosink`.

Notes: the pipeline string is a *launch description*, ending in a payloader
named `pay0`; `insert-sps-pps=true`/`config-interval=1` let late-joining
clients sync. Add `nvvidconv` before the encoder to crop/scale (the source
thread's confirmed pipeline cropped via `nvvidconv left=... right=...`).

## Verify
`stream ready at rtsp://127.0.0.1:8554/test` is printed, and a remote VLC /
gst client shows live video. `tegrastats` shows NVENC active while CPU stays low.

## Gotchas
- **Orin Nano has no NVENC** — `nvv4l2h264enc` does not exist there; use
  CPU `x264enc` (e.g. `x264enc tune=zerolatency bitrate=4000 speed-preset=ultrafast`)
  or a device with an encoder. That's why `devices` excludes orin-nano.
- There is no `rtspsink` element in GStreamer — that's the classic first
  attempt; RTSP serving needs gst-rtsp-server (test-launch).
- Don't put `gst-launch-1.0` inside the quoted test-launch string — it's a
  pipeline description, not a shell command (second classic mistake from the
  source thread).
- `omxh264enc` examples on old wikis are deprecated (JP4) and removed in
  JP5+; use the `nvv4l2*enc` elements.
- For H.265 swap in `nvv4l2h265enc ! h265parse ! rtph265pay name=pay0 pt=96`
  (client must support HEVC).
