---
title: "Stream the Pi camera on Bookworm — rpicam-vid over TCP/UDP, GStreamer libcamerasrc, Picamera2 capture_array into OpenCV"
type: recipe
company: raspberry-pi
keys:
  - "rpicam-vid -t 0 --codec libav --libav-format mpegts"
  - "libcamerasrc"
  - "gst-launch-1.0 fdsrc fd=0"
  - "capture_array"
  - "pi camera frames into opencv"
  - "stream pi camera over network"
platform_versions: ["Raspberry Pi OS Bookworm+"]
devices: [pi-5, pi-4]
status: verified
verified_on: "doc checked 2026-07-21 (raspberrypi.com camera_software.html streaming; picamera2 repo)"
sources:
  - "https://www.raspberrypi.com/documentation/computers/camera_software.html"
  - "https://github.com/raspberrypi/picamera2"
  - "https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf"
---
## Context
Getting live CSI-camera video off a Pi (network stream) or into OpenCV
on-device, on the Bookworm libcamera stack. `cv2.VideoCapture(0)` does not
drive a CSI camera through the ISP on Bookworm — pick one of the routes
below instead of fighting V4L2.

## Knowledge
Network stream with rpicam-vid (simplest):

```bash
# UDP push to a client
rpicam-vid -t 0 -n --inline -o udp://<client-ip>:5000
# TCP listen, MPEG-TS container
rpicam-vid -t 0 -n --codec libav --libav-format mpegts -o "tcp://0.0.0.0:5000?listen=1"
```

Into a GStreamer pipeline — either pipe rpicam-vid in:

```bash
rpicam-vid -t 0 -n --codec libav --libav-format mpegts -o - | \
  gst-launch-1.0 fdsrc fd=0 ! udpsink host=<client-ip> port=5000
```

or use libcamera's own `libcamerasrc` element (official docs example):

```bash
# Pi 4 and earlier (hardware H.264 encoder):
gst-launch-1.0 libcamerasrc ! capsfilter caps=video/x-raw,width=640,height=360,format=NV12 ! \
  v4l2h264enc extra-controls="controls,repeat_sequence_header=1" ! \
  'video/x-h264,level=(string)4' ! h264parse ! mpegtsmux ! udpsink host=<ip> port=5000
```

Pi 5 has no hardware H.264 encoder — replace `v4l2h264enc ...` with
`x264enc speed-preset=1 threads=1` (software; budget CPU accordingly).

Into OpenCV in-process — use Picamera2 (preinstalled on Bookworm images,
else `sudo apt install python3-picamera2`):

```python
import cv2
from picamera2 import Picamera2
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(
    main={"format": "RGB888", "size": (1280, 720)}))
picam2.start()
while True:
    frame = picam2.capture_array()   # numpy array, OpenCV-ready
    cv2.imshow("cam", frame)
    if cv2.waitKey(1) == ord('q'):
        break
```

## Verify
Client side: `vlc udp://@:5000` (or a gst `udpsrc ! tsdemux ! h264parse !
avdec_h264 ! autovideosink` pipeline) shows live video with ~sub-second
latency on a LAN. The OpenCV window shows correctly-colored frames.

## Gotchas
- Picamera2 format naming is inverted vs expectation (libcamera/DRM
  little-endian naming): `"RGB888"` yields B,G,R memory order — i.e. what
  OpenCV wants; `"BGR888"` yields R,G,B. Wrong pick = swapped red/blue.
- Only one process owns the camera: rpicam-vid and a Picamera2 script can't
  run simultaneously on the same sensor.
- `--codec libav` on Pi 5 means software encode; at 1080p keep an eye on
  CPU/thermals (`vcgencmd get_throttled`).
- Legacy `raspivid | nc` recipes and `picamera` (v1) code are dead on
  Bookworm — migrate, don't patch.
