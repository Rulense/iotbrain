---
title: "Jetson in forced recovery mode not detected by host lsusb (cable, port, VM passthrough)"
type: fix
company: nvidia
keys:
  - "0955:7523"
  - "0955:7023"
  - "0955:7e19"
  - "NVIDIA Corp. APX"
  - "device is not in recovery mode"
  - "lsusb"
platform_versions: ["all"]
devices: [all]
status: verified
verified_on: "Orin Nano devkit, host Ubuntu 22.04, 2024-03 (forum thread confirmed detection after fix)"
sources:
  - "https://forums.developer.nvidia.com/t/jetson-orin-nano-not-detected-by-ubuntu-22-via-usb-in-recovery-mode/286259"
  - "https://forums.developer.nvidia.com/t/recovery-mode-for-jetson-orin-nano-0955-7523-p3767-0003-with-8gb/318754"
  - "https://docs.nvidia.com/jetson/archives/r36.4.3/DeveloperGuide/IN/QuickStart.html"
---
## Context
You put the Jetson into forced recovery mode to flash it, but `lsusb` on the host
shows no NVIDIA device and SDK Manager reports no board / "device is not in
recovery mode". Nothing on the Jetson's screen — that is expected: a device truly
in recovery mode shows no display output.

## Knowledge
### Root cause
Almost always one of: wrong USB port on the devkit, a charge-only/bad USB cable,
flaky VM USB passthrough, or the recovery jumper on the wrong pins / not held
through a power cycle.

### Fix
Work through in order, re-checking `lsusb` after each step:
1. **Use the flashing port.** On the Orin Nano/Orin NX devkit only the USB-C port
   goes to the flashing interface — none of the four USB-A ports work for flashing.
   (AGX devkits: the USB-C port next to the 40-pin header.)
2. **Use a known-good data cable** (many USB-C cables are charge-only). USB-C to
   USB-A 2.0 data cables are a reliable choice.
3. **Recovery jumper/button:** short FC REC to GND on the button header (Orin Nano
   devkit: J14) *before* applying power, or hold it while power-cycling. Entering
   recovery from a running system requires the pins held during reset.
4. **Avoid VMs.** VirtualBox/VMware USB passthrough drops the device when it
   re-enumerates during flashing. Use a native Ubuntu host; if a VM is unavoidable,
   add a USB filter for vendor ID 0955 and use a USB 2.0 controller, expecting
   retries.

Expected `lsusb` output when it works — vendor ID 0955, product name APX:
- Orin Nano: `ID 0955:7523 NVIDIA Corp. APX`
- AGX Orin: `ID 0955:7023 NVIDIA Corp. APX`
- Xavier NX: `ID 0955:7e19 NVIDIA Corp. APX`

## Verify
`lsusb | grep 0955` on the host shows an `0955:xxxx NVIDIA Corp.` entry, and SDK
Manager's device dropdown lists the board.

## Gotchas
- No display output in recovery mode is normal, not a sign of a dead board.
- USB hubs between host and Jetson can break detection — connect directly.
- If the device appears in `lsusb` but flashing still fails mid-way on a VM, that
  is the passthrough dropping re-enumeration, not a board fault.
