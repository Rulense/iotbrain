---
name: iot-connect
description: Use for edge-device connectivity and fleet work — MQTT (mosquitto, paho, AWS IoT Core, Azure IoT Hub), TLS and per-device certificates, provisioning, headless and remote access, OTA update strategy, fleet deployment with containers, and time-sync/RTC pitfalls. Applies to any connected board — NVIDIA Jetson, Raspberry Pi, ESP32, and others. Consults the iotbrain before and during the work and distills verified learnings back.
---

# IoT Connectivity & Fleet Companion

Getting edge devices talking — to brokers, clouds, and their operators — and
keeping fleets updated. The stable procedure lives here; version-specific
knowledge lives in the iotbrain at `${CLAUDE_PLUGIN_ROOT}/brain/` and the
user's overlay at `~/.iotbrain/local/`. Follow the steps in order.

## Step 1 — Device facts first

If the board, vendor, and OS/SDK version are not already established this
session, run `iot-dev` Step 1 to collect them — never guess. Then add the
connectivity facts: network path (Ethernet / Wi-Fi / cellular, NAT or not),
the broker or cloud target, and whether the board has a battery-backed RTC
and/or a secure element or TPM.

## Step 2 — Consult the brain BEFORE connecting

Grep the `iot/` domain in both stores for protocol names, ports, cloud
services, and (when debugging) VERBATIM error text:

```bash
grep -ril "mqtt\|8883\|ota\|provision\|ntp\|hwclock" \
  "${CLAUDE_PLUGIN_ROOT}/brain/iot/" ~/.iotbrain/local/ 2>/dev/null
```

Read every hit, filter by `company` + version exactly as iot-dev Step 3
describes, and surface matching `gotcha` entries BEFORE the stage that would
hit them — clock, cert, and power-save traps cost hours when discovered late.

## Step 3 — The connectivity playbook

1. **MQTT.** Local development → mosquitto. Cloud → AWS IoT Core / Azure IoT
   Hub with mutual TLS on port 8883 (443 with ALPN where 8883 is blocked).
   One identity and certificate per device — never fleet-shared. Prove the
   connection with `mosquitto_pub`/paho before wiring app code. Cloud-broker
   rejections often surface as generic socket resets: the brain's AWS IoT
   entry documents that Errno 104 there means a policy problem, not TLS. Set
   a Last-Will and sane keepalive; QoS 1 for commands and state, QoS 0 for
   high-rate telemetry.
2. **Provisioning & certs.** Pick per fleet size: individual registration
   (small), claim/fleet provisioning (devices trade a bootstrap cert for
   their own on first boot), or the cloud's device-provisioning service.
   Generate private keys on-device and never let them leave; use the secure
   element/TPM where the board has one. Track cert expiry — and remember
   validation also fails when the device clock is wrong (stage 6).
3. **Headless & remote access.** First contact without a monitor: serial
   console or USB device mode — the brain's Jetson recipe covers oem-config
   over `/dev/ttyACM0`, then ssh to `192.168.55.1`. For NAT-ed fleets, open
   no inbound ports: use an overlay/mesh VPN (WireGuard/Tailscale-class) or a
   reverse tunnel, and keep serial as the last-resort recovery path.
4. **OTA strategy.** Decide per update class. App-only → ship the app as a
   container and update only it. OS/BSP → package OTA (apt-style; not
   failsafe, limited across major releases) vs image-based A/B (atomic, with
   rollback) — the brain's OTA matrix entry covers what survives each on
   Jetson. Invariants: stage rollouts, never break the updater itself, always
   keep a rollback path, and run the full update on one real device before
   the fleet.
5. **Fleet deployment via containers.** One multi-arch image (docker buildx),
   configuration via env/mounts, restart policies for unattended recovery,
   image digests pinned for reproducibility. On GPU devices confirm the
   container runtime is wired to the accelerator — the brain's Docker-GPU fix
   (`default-runtime` nvidia) is the Jetson case.
6. **Time-sync & RTC.** A wrong clock breaks TLS, apt, and token auth. Check
   that an RTC battery exists AND that boot actually reads that RTC — the
   brain's Jetson fix exists because the battery feeds rtc0 while boot time
   comes from rtc1. Ensure NTP is reachable from the fleet network or point
   devices at an internal server. For devices that fall off Wi-Fi when idle,
   check the brain's power-save fix before blaming the AP.

## Step 4 — Defer to specific skills

When a more specific installed skill covers the doing, use it:
`jetson-headless-mode` for reclaiming GUI memory on headless Jetsons, the
`devicetree` / `hardware-io` skills for Zephyr-based connectivity firmware,
and the upstream sets catalogued in `SKILLS-CATALOG.md` — Microsoft's
azure-iot skills for Azure operations, Seeed's Jetson tools for vendor OTA.
Consult the brain first either way — Steps 2–3 tell you which knowledge
applies to this device before the specialist acts.

## Step 5 — Distill verified learnings

When something new was VERIFIED against real infrastructure — a broker
config that connected, a provisioning flow run end-to-end, an OTA that
survived a reboot, a clock/cert trap reproduced — invoke the `brain-distill`
skill. Distill working setups as `recipe`/`config` entries and traps as
`gotcha` entries, not just debug fixes.
