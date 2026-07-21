---
title: "RP2350-E9 erratum on Pico 2 — GPIO inputs latch near 2.2 V and internal pull-downs can't pull low (fixed in A3/A4 stepping)"
type: gotcha
company: raspberry-pi
keys:
  - "RP2350-E9"
  - "RP2350 A2 stepping"
  - "pico-sdk 2.1.0"
  - "gpio input stuck at 2.2V"
  - "internal pull-down not working"
platform_versions: ["RP2350 A2 stepping", "pico-sdk 2.x"]
devices: [pico-2]
status: verified
verified_on: "doc checked 2026-07-21 (RP2350 datasheet errata RP2350-E9; A4 stepping PCN + raspberrypi.com news)"
sources:
  - "https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf"
  - "https://www.raspberrypi.com/news/rp2350-a4-rp2354-and-a-new-hacking-challenge/"
  - "https://forums.raspberrypi.com/viewtopic.php?t=375631"
  - "https://github.com/earlephilhower/arduino-pico/issues/2380"
---
## Context
Buttons, rotary encoders, or any active-high input on a Pico 2 / RP2350
board read as pressed forever, ADC pins sit at a mystery ~2 V, or a pin
"works once" then sticks. This is silicon, not your firmware: erratum
RP2350-E9 in the launch (A2) stepping.

## Knowledge
On A2-stepping RP2350 (all original Pico 2 boards), a Bank 0 GPIO configured
as an input (output driver disabled, input buffer enabled) can latch at
roughly 2.1–2.2 V after the pad has been driven high, instead of being
pulled to ground — the internal pull-down is too weak to win, and the pad
leaks (~120 µA). In practice it's broader than the original erratum text:
any high-impedance input that has seen a high level can stick near 2.2 V
even with the pull-down disabled.

Workarounds on A2 silicon:
- Hardware: external pull-down of ≤ ~8.2 kΩ on affected inputs, or design
  inputs active-low with pull-ups (pull-ups are unaffected).
- Software: don't leave pads floating as inputs — between reads, disable the
  pad's input enable (IE) or briefly drive the pin low, then sample.

Fixed silicon: the A3/A4 steppings (announced July 2025, PCN covers both;
markings `RP2350A0A4` / `RP2350B0A4`, plus the new RP2354 2 MB-flash
variants) fix E9 in hardware. A4 parts require pico-sdk ≥ 2.1.0 (bootrom
changes) — older SDK binaries may not boot on new-stepping chips.

## Verify
Testbench: configure a suspect pin `gpio_set_dir(pin, GPIO_IN);
gpio_pull_down(pin);` drive it high externally once, release, and measure —
A2 sticks near 2.2 V, A3/A4 falls to 0 V. Stepping is readable in the
bootrom/OTP chip info (`picotool info -a` reports the package/revision).

## Gotchas
- Symptom masquerades as software: "works with pull-up logic, broken with
  pull-down" is the classic E9 signature.
- Mixed-stepping production runs: same firmware, different behavior per unit
  — check chip markings before debugging boards individually.
- The 9 kΩ figure is the boundary: 10 kΩ external pull-downs are NOT
  reliably strong enough; use 8.2 kΩ or lower.
