---
title: "esptool 'Failed to connect: Wrong boot mode detected' / 'Timed out waiting for packet header' — strapping pins, BOOT button, cable and driver causes"
type: fix
company: espressif
keys:
  - "Wrong boot mode detected"
  - "Failed to connect to ESP32"
  - "Timed out waiting for packet header"
  - "No serial data received."
  - "Invalid head of packet"
  - "esp32 not detected when flashing"
  - "cannot flash esp32 board"
platform_versions: ["all"]
devices: [all]
status: verified
verified_on: "doc checked 2026-07-21"
sources:
  - "https://docs.espressif.com/projects/esptool/en/latest/esp32/troubleshooting.html"
  - "https://docs.espressif.com/projects/esptool/en/latest/esp32/advanced-topics/boot-mode-selection.html"
  - "https://github.com/espressif/esptool/blob/master/esptool/loader.py"
---
## Context
`esptool.py write_flash` / `idf.py flash` fails before writing anything, with one
of: `Failed to connect to ESP32: Wrong boot mode detected (0xXX)! The chip needs
to be in download mode.`, `No serial data received.`, or (esptool v4-era wording
of the same no-reply failure) `Timed out waiting for packet header`. Scoped
`all`: this is ROM serial-bootloader behavior, independent of ESP-IDF /
Arduino / MicroPython version. Verbatim messages checked against current
esptool `loader.py` and the official troubleshooting page.

## Knowledge
### Root cause
The chip is not in ROM download mode, or the serial path between host and chip
is broken. Download mode on classic ESP32 requires **GPIO0 held low on reset**
("The ESP32 will enter the serial bootloader when GPIO0 is held low on reset"),
and "GPIO2 must also be either left unconnected/floating, or driven Low".
Devkits automate this by wiring EN→RTS and GPIO0→DTR so esptool can pulse them;
when that auto-reset circuit is missing or flaky you get exactly
`Wrong boot mode detected` — serial works, but the reset-into-download failed.

### Fix
Work down this list:
1. **Manual download mode**: hold the BOOT (GPIO0/IO0) button, tap RESET/EN,
   release BOOT — do it while esptool prints `Connecting....`. Boards without
   the DTR/RTS auto-reset circuit *always* need this.
2. **Cable and driver**: charge-only USB cables are the classic cause of
   "connects but no data". Use a known data cable, install the CP210x/CH34x
   driver, and on Linux add yourself to `dialout`/`uucp`. Make sure no serial
   monitor holds the port open.
3. **Power**: the 3.3 V rail needs ~200–300 mA peaks during flashing. Bare
   FTDI adapters and Arduino 3.3 V pins can't supply that — the docs say to
   avoid them and add bulk capacitance.
4. **Strapping pins loaded by your circuit**: measure GPIO0/GPIO2 with a
   multimeter at reset (high ≈3.3 V, low ≈0 V) and disconnect peripherals from
   strapping pins. On classic ESP32, GPIO12/MTDI pulled high switches
   VDD_SDIO to 1.8 V and "may prevent flashing and/or booting if 3.3V flash
   is used ... causing the flash to brownout".
5. **Noise/corruption**: `Invalid head of packet (0xXX)` = serial noise — bad
   cable, breadboard wiring, or sagging supply. Drop the baud rate
   (`-b 9600`) to rule out speed, and pass `--chip esp32` to skip
   autodetection.
6. On chips with native **USB-Serial/JTAG** (S3/C3/C6/P4) pick the right one
   of the two ports, and use `--after watchdog-reset` if the chip doesn't
   come back after flashing over USB-Serial/JTAG.

## Verify
`esptool.py -p <port> flash_id` connects, prints the chip type, MAC, and flash
manufacturer ID. After that, `write_flash` at the same baud works.

## Gotchas
- esptool v5 reworded several of these errors (e.g. `No serial data
  received.` replaced the old `Timed out waiting for packet header`) — same
  root causes, so match on either wording.
- After manually entering download mode, some boards stay parked in the
  bootloader after flashing — press RESET once to boot the new app.
- `Download mode successfully detected, but getting no sync reply` means the
  chip's TX line is down — check the RX/TX crossover, not the buttons.
