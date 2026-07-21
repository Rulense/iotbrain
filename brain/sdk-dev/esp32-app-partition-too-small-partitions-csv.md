---
title: "ESP-IDF build fails 'partition is too small for binary' — grow the app partition with partitions_singleapp_large or a custom partitions.csv"
type: fix
company: espressif
keys:
  - "too small for binary"
  - "(overflow 0x"
  - "CONFIG_PARTITION_TABLE_CUSTOM"
  - "partitions.csv"
  - "Single factory app (large)"
  - "app image too big"
  - "firmware does not fit in flash"
platform_versions: ["ESP-IDF 5.x", "ESP-IDF 6.0"]
devices: [all]
status: verified
verified_on: "doc checked 2026-07-21"
sources:
  - "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/partition-tables.html"
  - "https://github.com/espressif/esp-idf/blob/master/components/partition_table/check_sizes.py"
---
## Context
The build (or `idf.py flash`) fails with an error containing
`too small for binary <app>.bin size 0x...` and a per-partition
`(overflow 0x...)` line — the app image outgrew its partition. Typical the
first time a project pulls in Wi-Fi + TLS + C++ or enables debug logging.
Message format checked against `components/partition_table/check_sizes.py` on
current master; the partition-table mechanics are unchanged across IDF 5.x
and 6.0.

## Knowledge
### Root cause
The default partition table option **"Single factory app, no OTA"** gives the
factory app slot 1 MB. `check_sizes.py` compares the built `.bin` against the
slot and fails the build once the image no longer fits. Nothing is wrong with
your code — the table is just the conservative default.

### Fix
Pick one, in menuconfig → **Partition Table**:
1. **Cheapest**: switch to "Single factory app (large), no OTA" — the bundled
   `partitions_singleapp_large.csv` gives the factory slot 1500K.
2. **Custom table** (needed for OTA layouts or >4 MB flash): select
   `Custom partition table CSV` (`CONFIG_PARTITION_TABLE_CUSTOM`) and add
   `partitions.csv` next to the project's CMakeLists:
   ```
   # Name,   Type, SubType, Offset,  Size
   nvs,      data, nvs,     0x9000,  0x6000
   phy_init, data, phy,     ,        0x1000
   factory,  app,  factory, 0x10000, 2M
   ```
   Blank offsets are auto-calculated with correct alignment; app partitions
   must sit on 0x10000 (64 KB) boundaries. `otadata` needs exactly 0x2000,
   NVS at least 0x3000 (docs recommend more).
3. **Tell IDF the real flash size**: a 4/8/16 MB module configured as the
   smaller default wastes the headroom your bigger table needs — set
   `CONFIG_ESPTOOLPY_FLASHSIZE` (Serial flasher config → Flash size) to the
   module's actual size.
4. **Or shrink the app**: `idf.py size` and `idf.py size-components` show
   what's eating flash; size-optimization (`-Os`), lower default log level,
   and dropping unused components buy back hundreds of KB.

## Verify
`idf.py partition-table` prints the summary with the new sizes;
`idf.py build` completes and the size footer shows free space in the app
partition. Flash and boot — the partition table is written at its own offset
(default 0x8000, `CONFIG_PARTITION_TABLE_OFFSET`), so a plain
`idf.py flash` ships it along with the app.

## Gotchas
- Changing the partition table on **deployed** devices moves/resizes `nvs` —
  stored Wi-Fi credentials and app data are effectively lost. Plan tables
  before shipping, not after.
- For OTA layouts, *every* app slot must fit the image; growing only `ota_0`
  just defers the failure to the first update into `ota_1`.
- The `.bin` files still get produced despite the size error — don't script
  around the failure by flashing them manually; the app would overwrite the
  next partition's data.
