---
title: "Jetson Orin thermal throttling under sustained load — clocks drop near 99°C, soft shutdown at 104.5°C (thermal_zone temps)"
type: gotcha
company: nvidia
keys:
  - "tj-thermal"
  - "cpu-thermal"
  - "gpu-thermal"
  - "thermal_zone"
  - "slows down when hot"
  - "thermal throttling under load"
platform_versions: ["JetPack 5.x", "JetPack 6.x", "L4T 35.x", "L4T 36.x"]
devices: [orin-nano, orin-nx, agx-orin]
status: verified
verified_on: "Trip temperatures per NVIDIA L4T r36.5 Developer Guide (Platform Power and Performance, Orin series: throttle 99.0 C, software shutdown 104.5 C, hardware shutdown 105.0 C); doc retrieved 2026-07-18"
sources:
  - "https://docs.nvidia.com/jetson/archives/r36.5/DeveloperGuide/SD/PlatformPowerAndPerformance/JetsonOrinNanoSeriesJetsonOrinNxSeriesAndJetsonAgxOrinSeries.html"
---
## Context
Throughput starts strong then sags after minutes of sustained inference/build
load — even with `nvpmodel` maxed and `jetson_clocks` applied. `tegrastats`
shows frequencies below max while utilization stays high. Common in enclosures,
fanless carriers, or with the default `quiet` fan profile on Orin Nano/NX.

## Knowledge
The Linux thermal framework throttles silently — there is **no popup** (unlike
over-current). On Orin-family modules the documented trip points are:

| Event | Temp | Effect |
|---|---|---|
| Software throttling | 99.0 °C | CPU/GPU clocks reduced by cooling devices; overrides `jetson_clocks` |
| Software (soft) shutdown | 104.5 °C | Orderly OS shutdown |
| Hardware shutdown | 105.0 °C | Immediate power-off, no OS involvement |

Zones monitored: `cpu-thermal`, `gpu-thermal`, `cv0/1/2-thermal`,
`soc0/1/2-thermal`, `tj-thermal` (highest junction). Read them:

```bash
paste <(cat /sys/devices/virtual/thermal/thermal_zone*/type) \
      <(cat /sys/devices/virtual/thermal/thermal_zone*/temp)   # millidegrees C
```

Diagnosis: log `tegrastats` during the workload — if `tj@` approaches ~99 °C
right as `GR3D_FREQ`/CPU frequencies drop, it's thermal, not a power-mode or
over-current issue.

Mitigations, in order:
1. Switch the fan profile from `quiet` to `cool`
   (see `runtime/nvfancontrol-fan-profile-change.md`), or pin the fan with
   `sudo jetson_clocks --fan` while diagnosing.
2. Fix airflow/heatsinking — enclosure venting, module thermal interface,
   ambient temperature.
3. If the thermal budget genuinely can't hold MAXN, run one nvpmodel mode
   lower for stable (unthrottled) sustained performance.

## Verify
Repeat the sustained workload while logging `tegrastats`: temps plateau below
~95 °C and clocks hold at the mode's maximum for the full run.

## Gotchas
- `jetson_clocks` cannot override thermal caps — trip points come from the
  device tree, not userspace.
- A device that "randomly powers off" under load likely hit soft/hardware
  shutdown; check temps before suspecting the PSU.
- Sudden clock dips with cool temps are over-current events instead — see
  `runtime/over-current-throttling-warning.md`.
- Benchmark honestly: a 30-second run measures burst performance; sustained
  workloads need minutes to reach thermal steady state.
