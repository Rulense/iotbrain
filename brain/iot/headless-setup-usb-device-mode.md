---
title: "Headless Jetson setup with no monitor — USB device mode serial oem-config, then ssh to 192.168.55.1"
type: recipe
company: nvidia
keys:
  - "192.168.55.1"
  - "l4tbr0"
  - "/dev/ttyACM0"
  - "nv-l4t-usb-device-mode"
jetpack: ["all"]
l4t: ["all"]
devices: [all]
status: verified
verified_on: "AGX Orin devkit, JetPack 5.x-6.x (official devkit user guide documents 192.168.55.1 virtual ethernet + headless oem-config UART), doc checked 2026-07-17"
sources:
  - "https://docs.nvidia.com/jetson/agx-orin-devkit/user-guide/latest/howto.html"
  - "https://forums.developer.nvidia.com/t/jp6-has-no-ip-over-usb-192-168-55-1-anymore/296062"
  - "https://www.jetson-ai-lab.com/tutorials/getting-started-with-jetson/"
---
## Context
Fresh-flashed Jetson, no monitor/keyboard attached (typical IoT bench or rack
setup). You need to finish first-boot configuration (oem-config: EULA, user
account, locale) and get an ssh session — using only a USB cable to a host PC.

## Knowledge
Jetson devkits run USB *device mode* on their flashing port (USB-C next to the
40-pin header on Orin devkits; micro-USB on Nano/Xavier NX). One cable gives you:

1. **Virtual UART for headless oem-config.** After the Jetson boots, the host
   sees a CDC-ACM serial device. On the host:
   ```
   ls /dev/ttyACM*          # usually /dev/ttyACM0
   sudo screen /dev/ttyACM0 115200
   ```
   (Windows: a COM port in Device Manager; use PuTTY at 115200.) The
   text-mode oem-config wizard runs in this terminal — create your user here.
2. **Virtual ethernet.** The Jetson-side service (`nv-l4t-usb-device-mode`)
   creates a bridge `l4tbr0` with the fixed address **192.168.55.1** and runs a
   DHCP server, so the host's new USB network interface gets a 192.168.55.x
   address automatically. Once oem-config is done:
   ```
   ssh <user>@192.168.55.1
   ```

Order of use: serial console first (account creation), then ssh over
192.168.55.1 for real work; from there configure Wi-Fi/ethernet
(`sudo nmcli device wifi connect <SSID> password <pw>`) and drop the USB tether.

## Verify
- Host sees the serial device (`/dev/ttyACM0`) and a new network interface with
  a 192.168.55.x address.
- `ping 192.168.55.1` answers; `ssh <user>@192.168.55.1` logs in.
- On the Jetson: `ip addr show l4tbr0` shows `192.168.55.1/24`.

## Gotchas
- Use the *device-mode* port — a USB Type-A host port on the carrier will never
  enumerate as a device. Use a real data cable, not a charge-only one.
- JetPack 6 is stricter about USB device-tree config: on custom carrier boards
  the `l4tbr0`/192.168.55.1 interface can disappear after a JP5→JP6 move until
  the board's USB (UFP/ID pin) is described correctly in the device tree
  (see source thread 296062). Devkits are unaffected.
- If ssh times out but serial works, oem-config probably isn't finished — the
  network side comes up fully only after first-boot setup completes.
- Corporate hosts sometimes block the RNDIS/ECM gadget interface; check the
  host's firewall/driver before blaming the Jetson.
