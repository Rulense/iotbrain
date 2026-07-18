---
title: "CSI camera frames into OpenCV as BGR — nvvidconv to BGRx, then videoconvert (VIC can't output BGR)"
type: recipe
company: nvidia
keys:
  - "nvvidconv"
  - "video/x-raw(memory:NVMM)"
  - "format=BGRx ! videoconvert"
  - "appsink"
  - "cv2.CAP_GSTREAMER"
jetpack: ["all"]
l4t: ["all"]
devices: [all]
status: verified
verified_on: "AGX Orin, JetPack 5.x, 2023-02-09 (forum thread: BGRx→videoconvert→BGR pipeline working on hardware, constraint confirmed by NVIDIA)"
sources:
  - "https://forums.developer.nvidia.com/t/nvvidconv-and-videoconvert/242205"
  - "https://docs.nvidia.com/jetson/archives/r35.3.1/DeveloperGuide/text/SD/Multimedia/AcceleratedGstreamer.html"
  - "https://github.com/JetsonHacksNano/buildOpenCV/blob/master/Examples/gstreamer_view.cpp"
---
## Context
You want CSI (or YUV) camera frames as BGR `numpy` arrays in OpenCV via
`cv2.VideoCapture`. Applies to every Jetson because the constraint comes from
the VIC hardware converter behind `nvvidconv`, present on all Jetson SoCs.

## Knowledge
The canonical pipeline:

```python
import cv2
pipeline = (
    "nvarguscamerasrc sensor-id=0 ! "
    "video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1,format=NV12 ! "
    "nvvidconv ! video/x-raw,format=BGRx ! "
    "videoconvert ! video/x-raw,format=BGR ! "
    "appsink drop=1 max-buffers=1"
)
cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
```

Why each stage exists:
- `nvarguscamerasrc` outputs NV12 in NVMM (DMA) memory.
- `nvvidconv` runs on the VIC (hardware, not GPU/CPU): converts NV12→BGRx AND
  copies NVMM→system memory. The VIC does **not** support 24-bit BGR output —
  only 32-bit BGRx/RGBA — so you cannot ask nvvidconv for BGR directly
  (NVIDIA: "hardware converter does not support 24-bit BGR format").
- `videoconvert` (CPU) does the cheap BGRx→BGR channel drop that OpenCV needs.
- `drop=1 max-buffers=1` on appsink prevents latency build-up when your
  processing loop is slower than the camera.

For USB/YUV cameras swap the source:
`v4l2src device=/dev/video1 ! video/x-raw,format=UYVY ! nvvidconv ! video/x-raw,format=BGRx ! videoconvert ! video/x-raw,format=BGR ! appsink`
(this UYVY variant is the one confirmed working in the source thread).

## Verify
- `python3 -c "import cv2; print(cv2.getBuildInformation())" | grep -i gstreamer`
  must show `GStreamer: YES`.
- `cap.isOpened()` is True and `cap.read()` returns a frame with shape
  `(1080, 1920, 3)`.

## Gotchas
- `pip install opencv-python` wheels are built WITHOUT GStreamer —
  `VideoCapture(pipeline, CAP_GSTREAMER)` just returns not-opened. Use
  Ubuntu's `python3-opencv`, a Jetson build, or jetson-containers.
- Requesting `format=BGR` straight from nvvidconv fails caps negotiation
  (pipeline won't link) — the extra `videoconvert` is mandatory.
- Low GPU usage is expected: nvvidconv runs on VIC, videoconvert on CPU.
- Keep `(memory:NVMM)` caps between NVIDIA elements; drop NVMM only at the
  last hardware stage before appsink, or you pay extra copies.
