---
title: "ESP32 OTA anti-brick — app rollback with CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE, otadata states, and interrupted-OTA recovery"
type: recipe
company: espressif
keys:
  - "CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE"
  - "esp_ota_mark_app_valid_cancel_rollback"
  - "esp_ota_mark_app_invalid_rollback_and_reboot"
  - "ESP_OTA_IMG_PENDING_VERIFY"
  - "otadata"
  - "device bricked after ota"
  - "esp32 rolls back after update"
platform_versions: ["ESP-IDF 5.x", "ESP-IDF 6.0"]
devices: [all]
status: verified
verified_on: "doc checked 2026-07-21"
sources:
  - "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/ota.html"
---
## Context
You push OTA firmware to a fleet of ESP32 devices you can't physically reach.
A bad image that boots-then-crashes must never strand the device: the
bootloader has to fall back to the previous app on its own. ESP-IDF's app
rollback does exactly that; the states and APIs below are current in the
`latest` OTA docs (IDF 5.x and 6.0).

## Knowledge
1. **Partition layout**: use an OTA table (`ota_0` + `ota_1` app slots plus an
   `otadata` partition). `otadata` is two mirrored 0x2000-byte sectors, so a
   power cut mid-write cannot lose the boot selection.
2. **Enable rollback**: set `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE=y`. Now a
   freshly written app is marked `ESP_OTA_IMG_NEW` in otadata; the bootloader
   boots it **once**, flipping it to `ESP_OTA_IMG_PENDING_VERIFY`.
3. **Self-test and confirm**: the new app must prove it works (network up,
   MQTT connected, whatever your health check is) and then call
   `esp_ota_mark_app_valid_cancel_rollback()` — state becomes
   `ESP_OTA_IMG_VALID` and the update is final.
4. **Automatic rollback**: if the app crashes, watchdogs, or reboots before
   confirming, the bootloader sees `ESP_OTA_IMG_PENDING_VERIFY` on the next
   boot, marks the slot `ESP_OTA_IMG_ABORTED`, and boots the previous valid
   app. No user action, no brick.
5. **Deliberate rollback**: if the app decides it's unhealthy, call
   `esp_ota_mark_app_invalid_rollback_and_reboot()` to mark itself invalid
   and reboot into the previous version.
6. **Interrupted download ≠ interrupted device**: an OTA transfer that dies
   mid-download never touches the running app — the boot partition only
   switches after `esp_ota_end()` validates the image. The partially written
   slot is simply overwritten on the next attempt (`esp_ota_resume()` in
   `esp_ota_ops.h` can continue a partial write from an offset instead of
   restarting).

## Verify
Bench-test the failure path before trusting it in the field:
- Flash an OTA build that intentionally `abort()`s before the confirm call —
  after one boot the device must come back up in the previous firmware.
- Pull power mid-download and mid-first-boot; the device must still boot.
- `esp_ota_get_state_partition()` on the running slot reports
  `ESP_OTA_IMG_VALID` after a confirmed update.

## Gotchas
- Call `esp_ota_mark_app_valid_cancel_rollback()` only **after** your real
  health checks pass. Confirming first thing in `app_main()` gives you
  rollback in name only.
- `CONFIG_BOOTLOADER_APP_ANTI_ROLLBACK` (refusing images with a lower
  `secure_version`) burns monotonic counters into eFuse — the field is
  limited to 32 bits, i.e. at most 32 security-version bumps per device, and
  it's one-way hardware. Don't enable it casually; see
  [esp32-secure-boot-flash-encryption-irreversible.md](../setup/esp32-secure-boot-flash-encryption-irreversible.md).
- Rollback protects the **app**, not the bootloader or partition table —
  those aren't updatable via plain OTA, so never ship an OTA that assumes a
  different partition layout.
