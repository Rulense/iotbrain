# Jetson Brain Index

One line per entry. Format: `- [title](domain/slug.md) — type · JP range · hook`

## ml-stack
- [ImportError: libcudnn.so after pip-installing PyTorch on Jetson](ml-stack/pytorch-wheel-libcudnn-import-error.md) — fix · JP 5.x–6.x · wheel/JetPack mismatch breaks import or CUDA
- [Known-working PyTorch wheel source for JetPack 6.x (CUDA 12.6)](ml-stack/pytorch-jetpack6-working-wheels.md) — config · JP 6.x · jp6/cu126 pip index, no source builds

## runtime
- [Default power mode silently caps Jetson performance](runtime/default-power-mode-caps-performance.md) — gotcha · JP all · nvpmodel + jetson_clocks before benchmarking

## setup
- [Jetson in forced recovery mode not detected by host lsusb (cable, port, VM passthrough)](setup/recovery-mode-device-not-detected-lsusb.md) — fix · JP all · USB-C flashing port, data cable, no VMs; expect 0955:xxxx APX
- [Flash Jetson Orin Nano devkit to NVMe SSD with l4t_initrd_flash.sh](setup/orin-nano-nvme-initrd-flash.md) — recipe · JP 6.x · exact initrd-flash command, r36 QSPI cfg path change
- [SDK Manager hangs at 'Determining the IP address of the target' — OEM configuration not completed](setup/sdk-manager-sdk-components-ip-oem-config.md) — fix · JP all · SDK components install over SSH; Pre-Config OEM setup or finish oem-config first
- [JetPack 6 SD image stuck at first boot / End-user configuration on Orin Nano — QSPI firmware too old](setup/jetpack6-first-boot-hang-qspi-firmware.md) — fix · JP 6.x · firmware <36.0 can't boot JP6; JP5.1.3 bridge + qspi-updater or full flash
- [Correct board-config names for flashing Orin devkits on L4T r36.x (stale names break boot)](setup/orin-flash-board-config-names.md) — matrix · JP 6.x · jetson-orin-nano-devkit covers Orin NX too; r35-era names flash but don't boot
- [Recover an unbootable Jetson after a failed apt/OTA upgrade (forced recovery + reflash)](setup/recover-unbootable-after-apt-ota-upgrade.md) — recipe · JP all · forced recovery always works; reflash matching BSP, apt-mark hold to prevent
