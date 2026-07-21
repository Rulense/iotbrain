---
title: "SDK Manager hangs at 'Determining the IP address of the target' — OEM configuration not completed"
type: fix
company: nvidia
keys:
  - "Determining the IP address of the target"
  - "Default ip is not avaliable. Please make sure the default ip is shown in ip addr, or use a customer ip instead"
  - "192.168.55.1"
  - "Install SDK components"
  - "OEM Configuration"
platform_versions: ["all"]
devices: [all]
status: verified
verified_on: "AGX Xavier devkit, JetPack 5.0.2, 2022-08 (forum thread: install completed via device IP after first-boot setup)"
sources:
  - "https://forums.developer.nvidia.com/t/default-ip-not-available-error-while-trying-to-install-jetson-sdk-components/223582"
  - "https://forums.developer.nvidia.com/t/error-default-ip-is-not-avaliable-please-make-sure-the-default-ip-is-shown-in-ip-addr-or-use-a-customer-ip-instead-occurs-during-recovery-mode/233224"
---
## Context
SDK Manager flashes Jetson Linux successfully, but the "Install SDK components"
phase hangs at "Determining the IP address of the target..." or errors with the
(verbatim, typos included) "Default ip is not avaliable. Please make sure the
default ip is shown in ip addr, or use a customer ip instead".

## Knowledge
### Root cause
Flashing happens over the recovery-mode USB protocol, but SDK components
(CUDA, cuDNN, TensorRT, ...) are installed afterwards **over SSH to the booted
device**. If the first-boot OEM configuration wizard was never completed — you
chose "Runtime" OEM configuration and the device is sitting at the setup screen
with no user account yet — there is nothing to SSH into, and the USB device-mode
network (host sees the Jetson at 192.168.55.1) never comes up.

### Fix
1. Preferred: in SDK Manager's flash settings choose **Pre-Config** OEM
   configuration and fill in username/password. The device then boots fully
   configured and SDK Manager can SSH in at 192.168.55.1 unattended.
2. If already flashed with "Runtime": complete the setup wizard on the device
   (monitor+keyboard, or headless via the serial console on the USB debug port),
   keep the USB cable connected, then let SDK Manager retry with 192.168.55.1
   and the credentials you just created.
3. If the USB network still doesn't appear (`ip addr` on the host shows no
   l4tbr0/usb interface with 192.168.55.x), connect the Jetson to the same LAN
   by Ethernet, get its address with `ifconfig`/`ip addr` on the device, and
   enter that IP in SDK Manager instead of the default.

## Verify
From the host: `ping 192.168.55.1` (or the LAN IP) answers, and
`ssh <user>@192.168.55.1` logs in. SDK Manager's component install proceeds
past the IP prompt.

## Gotchas
- This is not a flashing failure — the OS flash already succeeded. Re-flashing
  in a loop doesn't help.
- Host firewalls/VPNs can block the 192.168.55.0/24 USB subnet.
- `ssh-askpass` missing on the host can stall the credentials prompt during
  component installation.
