---
title: "System throttled due to Over-current on Jetson Orin — read the OC event counters, size the supply, expect it under MAXN stress"
type: fix
company: nvidia
keys:
  - "System throttled due to Over-current"
  - "System throttled due to over-current"
  - "oc1_event_cnt"
  - "/sys/class/hwmon/hwmon*/oc*_event_cnt"
jetpack: ["5.x", "6.x"]
l4t: ["35.x", "36.x"]
devices: [orin-nano, orin-nx, agx-orin]
status: unverified
sources:
  - "https://forums.developer.nvidia.com/t/about-system-throttled-due-to-over-current/292659"
  - "https://forums.developer.nvidia.com/t/jetson-orin-nano-super-system-throttled-due-to-over-current-lowcurrent-problem/368504"
  - "https://forums.developer.nvidia.com/t/system-throttled-due-to-over-current-on-orin-nx/247300"
---
## Context
A desktop popup (or log message) `System throttled due to Over-current` appears
during GPU-heavy work — TensorRT/CUDA benchmarks, LLM inference, multiple
containers — most often in MAXN / MAXN SUPER mode. Performance dips while the
warning is active.

## Knowledge
### Root cause
The onboard INA3221 rail monitors detect current above a rail's limit and the
system briefly caps clocks to protect the board. It is a protection mechanism,
not a fault: NVIDIA staff state clock specs are "designed for common usecase
and not for stress test", and that hitting OC events in MAXN under sustained
stress "is totally expected" — throttling won't hurt the board, only your
application's performance.

Two distinct situations produce it:
1. **Undersized power supply.** Example from the source thread: an Orin Nano
   Super devkit on the 19V/2.37A barrel adapter threw OC warnings in MAXN
   SUPER; NVIDIA recommended a 19V/4–4.2A supply (the devkit carrier's DC jack
   is specced up to 4.2A; 19V/5A is also fine).
2. **Genuine workload spikes** above the rail budget of the current nvpmodel
   mode — expected in MAXN-class modes.

### Fix
1. Confirm OC events are actually firing and which alarm it is (counters
   increment while throttling):
   ```bash
   grep "" /sys/class/hwmon/hwmon*/oc*_event_cnt
   ```
2. If on a marginal adapter, move to one with the same voltage and more
   current headroom (Orin Nano devkit: 19V, 4A+).
3. If the supply is adequate, drop one nvpmodel mode (e.g. 25W instead of
   MAXN) or accept occasional throttling under stress workloads.
4. Do **not** raise the current limits by writing to the INA3221 sysfs nodes
   (`curr*_max`): NVIDIA's response to that attempt was "It will damage the
   board... please do not do that".

## Verify
Re-run the same workload and watch `grep "" /sys/class/hwmon/hwmon*/oc*_event_cnt`
— counters stay flat and the popup no longer appears.

## Gotchas
- Headless devices never show the popup; the event counters (and reduced
  clocks in `tegrastats`) are the only signal.
- Distinct from thermal throttling — see
  `runtime/thermal-throttling-trip-points.md`; check temps to tell them apart.
- The exemplar gotcha applies in reverse: raising nvpmodel mode for
  performance (see `runtime/default-power-mode-caps-performance.md`) is what
  usually surfaces this warning for the first time.
