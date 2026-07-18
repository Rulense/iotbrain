# Jetson Brain Index

One line per entry. Format: `- [title](domain/slug.md) — type · JP range · hook`

## ml-stack
- [ImportError: libcudnn.so after pip-installing PyTorch on Jetson](ml-stack/pytorch-wheel-libcudnn-import-error.md) — fix · JP 5.x–6.x · wheel/JetPack mismatch breaks import or CUDA
- [Known-working PyTorch wheel source for JetPack 6.x (CUDA 12.6)](ml-stack/pytorch-jetpack6-working-wheels.md) — config · JP 6.x · jp6/cu126 pip index, no source builds
- [RuntimeError: operator torchvision::nms does not exist — torch/torchvision pairing on Jetson](ml-stack/torch-torchvision-version-pairing.md) — matrix · JP 5.x–6.x · pairing table; install both from the same Jetson index
- [TensorRT engine plan files are not portable — rebuild per device and per TensorRT version](ml-stack/tensorrt-engines-not-portable.md) — gotcha · JP all · ship ONNX, trtexec on target; JetPack upgrade invalidates cached engines
- [onnxruntime-gpu wheels for Jetson — PyPI installs are CPU-only, use Jetson AI Lab / Jetson Zoo wheels](ml-stack/onnxruntime-gpu-jetson-wheels.md) — config · JP 5.x–6.x · jp6/cu126 index or Jetson Zoo wheel per JetPack; check providers list
- [Illegal instruction (core dumped) importing numpy/torch on Jetson — OPENBLAS_CORETYPE=ARMV8](ml-stack/numpy-illegal-instruction-openblas-coretype.md) — fix · JP 4.x · numpy 1.19.5 OpenBLAS core misdetect; env var or pin 1.19.4
- [Don't apt-install Ubuntu's nvidia-cuda-toolkit on Jetson — JetPack CUDA lives in /usr/local/cuda](ml-stack/cuda-toolkit-apt-vs-jetpack-cuda.md) — gotcha · JP 5.x–6.x · nvcc is a PATH problem; upgrade CUDA via NVIDIA's Jetson repo instead
- [jetson-containers — prebuilt CUDA ML containers as the escape hatch for on-device dependency hell](ml-stack/jetson-containers-dependency-escape-hatch.md) — recipe · JP 6.x–7.x · autotag matches your L4T; run wrapper sets --runtime nvidia

## runtime
- [Default power mode silently caps Jetson performance](runtime/default-power-mode-caps-performance.md) — gotcha · JP all · nvpmodel + jetson_clocks before benchmarking

## setup
- [Jetson in forced recovery mode not detected by host lsusb (cable, port, VM passthrough)](setup/recovery-mode-device-not-detected-lsusb.md) — fix · JP all · USB-C flashing port, data cable, no VMs; expect 0955:xxxx APX
- [Flash Jetson Orin Nano devkit to NVMe SSD with l4t_initrd_flash.sh](setup/orin-nano-nvme-initrd-flash.md) — recipe · JP 6.x · exact initrd-flash command, r36 QSPI cfg path change
- [SDK Manager hangs at 'Determining the IP address of the target' — OEM configuration not completed](setup/sdk-manager-sdk-components-ip-oem-config.md) — fix · JP all · SDK components install over SSH; Pre-Config OEM setup or finish oem-config first
- [JetPack 6 SD image stuck at first boot / End-user configuration on Orin Nano — QSPI firmware too old](setup/jetpack6-first-boot-hang-qspi-firmware.md) — fix · JP 6.x · firmware <36.0 can't boot JP6; JP5.1.3 bridge + qspi-updater or full flash
- [Correct board-config names for flashing Orin devkits on L4T r36.x (stale names break boot)](setup/orin-flash-board-config-names.md) — matrix · JP 6.x · jetson-orin-nano-devkit covers Orin NX too; r35-era names flash but don't boot
- [Recover an unbootable Jetson after a failed apt/OTA upgrade (forced recovery + reflash)](setup/recover-unbootable-after-apt-ota-upgrade.md) — recipe · JP all · forced recovery always works; reflash matching BSP, apt-mark hold to prevent

## vision
- [nvarguscamerasrc 'No cameras available' with IMX219/IMX477 — apply CSI overlay with jetson-io](vision/nvarguscamerasrc-no-cameras-available-jetson-io.md) — fix · JP 5.x–6.x · JP6 needs jetson-io overlay; i2c -121 means reseat the ribbon
- [CSI camera frames into OpenCV as BGR — nvvidconv to BGRx, then videoconvert (VIC can't output BGR)](vision/csi-camera-opencv-bgr-gstreamer-pipeline.md) — recipe · JP all · canonical appsink pipeline; OpenCV must be built with GStreamer
- [v4l2-ctl captures frames but nvarguscamerasrc/Argus fails — the ISP path needs more than a working V4L2 driver](vision/v4l2-works-nvargus-fails-isp-path.md) — gotcha · JP all · Argus needs full DT + live CID controls; real errors in the daemon journal
- [nvarguscamerasrc in Docker: mount /tmp/argus_socket — and remount after any nvargus-daemon restart](vision/nvargus-docker-argus-socket-mount.md) — fix · JP all · client/daemon split; stale socket bind-mount after daemon restart
- [RTSP streaming from a Jetson camera with the hardware encoder (nvv4l2h264enc + gst-rtsp-server test-launch)](vision/rtsp-stream-nvv4l2h264enc-test-launch.md) — recipe · JP 4.x–6.x · test-launch pipeline; Orin Nano has no NVENC
- [Camera worked before, now every Argus open fails/times out — restart nvargus-daemon first](vision/restart-nvargus-daemon-first-line-recovery.md) — fix · JP all · daemon owns all Argus state; journalctl -u nvargus-daemon for the real error
