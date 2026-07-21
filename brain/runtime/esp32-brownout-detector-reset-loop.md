---
title: "'Brownout detector was triggered' reset loop on ESP32 — power supply and cable causes, threshold config (CONFIG_ESP_BROWNOUT_DET_LVL_SEL)"
type: fix
company: espressif
keys:
  - "Brownout detector was triggered"
  - "CONFIG_ESP_BROWNOUT_DET_LVL_SEL"
  - "RTCWDT_BROWN_OUT_RESET"
  - "esp32 keeps rebooting"
  - "reset loop when wifi starts"
platform_versions: ["ESP-IDF 5.x", "ESP-IDF 6.0"]
devices: [all]
status: verified
verified_on: "doc checked 2026-07-21"
sources:
  - "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/fatal-errors.html"
  - "https://www.esp32.com/viewtopic.php?t=16299"
---
## Context
The device prints `Brownout detector was triggered`, resets, and often loops —
classically the moment Wi-Fi TX starts (association, first HTTP request) or
when a peripheral load kicks in. The message and the `CONFIG_ESP_BROWNOUT_DET*`
options are current in the ESP-IDF `latest` fatal-errors guide, so this holds
across IDF 5.x and 6.0.

## Knowledge
### Root cause
The chip's built-in brownout detector fires when the supply voltage dips below
the configured threshold, and the chip is reset right after the message is
printed. Wi-Fi/BLE TX bursts draw current spikes of hundreds of mA; a weak USB
port, a long thin USB cable, or a marginal 3.3 V regulator (the AMS1117 on
cheap boards drops out when 5 V sags) lets the rail dip for microseconds —
enough to trip the detector even though a multimeter shows "3.3 V".

### Fix
In order of likelihood:
1. Swap the USB cable for a short, thick one and use a wall adapter or powered
   hub instead of a laptop port / unpowered hub.
2. Add bulk capacitance (hundreds of µF electrolytic + 100 nF ceramic) across
   the module's 3.3 V/GND, close to the module. This is the fix the solved
   forum threads converge on for boards that brown out only under Wi-Fi load.
3. If the board's 3.3 V regulator is hot or the brownouts persist with a good
   supply, the regulator is undersized/faulty — power 3.3 V from a proper
   buck/LDO rated ≥500 mA with headroom.
4. Battery designs: measure the rail with a scope during Wi-Fi TX; size the
   battery/DC-DC for the pulse load, not the average.

Threshold configuration (menuconfig → Component config → ESP System Settings):
`CONFIG_ESP_BROWNOUT_DET` enables the detector and
`CONFIG_ESP_BROWNOUT_DET_LVL_SEL` selects the trip voltage. Lowering the
threshold (or disabling the detector) only masks a real supply problem — the
chip will instead misbehave or corrupt flash writes when the rail collapses.
Don't ship with it disabled.

## Verify
Run the device through its worst-case load (Wi-Fi association + TX, all
peripherals on) for minutes without a reset. In firmware,
`esp_reset_reason()` no longer returns `ESP_RST_BROWNOUT` after reboots.

## Gotchas
- If the voltage drops fast the console may show only a truncated part of the
  message before reset (documented behavior) — a garbled line ending in a
  reset banner is still a brownout.
- On classic ESP32 the ROM banner after the reset shows
  `rst:0x10 (RTCWDT_BROWN_OUT_RESET)` — grep boot logs for it when the
  brownout message itself scrolled away.
- Brownouts during flashing show up as esptool sync/packet errors instead —
  see [esptool-failed-to-connect-wrong-boot-mode.md](../setup/esptool-failed-to-connect-wrong-boot-mode.md).
