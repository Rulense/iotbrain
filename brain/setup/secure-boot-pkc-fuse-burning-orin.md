---
title: "Enable secure boot on Jetson Orin — PKC/SBK fuse burning with odmfuse.sh: dry-run first, fuses are write-once"
type: recipe
company: nvidia
keys:
  - "odmfuse.sh"
  - "tegrasign_v3.py --pubkeyhash"
  - "PublicKeyHash"
  - "SecurityMode"
  - "BootSecurityInfo"
  - "enable secure boot on jetson"
  - "fuse burning is permanent"
platform_versions: ["JetPack 6.x", "L4T 36.x"]
devices: [agx-orin, orin-nx, orin-nano]
status: verified
verified_on: "doc checked 2026-07-21"
sources:
  - "https://docs.nvidia.com/jetson/archives/r36.4.3/DeveloperGuide/SD/Security/SecureBoot.html"
---
## Context
You're locking a production Orin so BootROM only runs images signed with your
key (PKC), optionally encrypted with your SBK. This is the one Jetson workflow
with no undo: fuses are hardware write-once, and a wrong or out-of-order burn
can permanently brick the board. Everything below is the official r36.4 flow.

## Knowledge
1. **Generate the PKC keypair** (Orin dropped RSA-2K — "The 2048-bit RSA key
   option is no longer supported on Jetson Orin series"). One of:
   - `openssl genrsa -out rsa_priv.pem 3072`
   - `openssl ecparam -name prime256v1 -genkey -noout -out ecp256.pem`
   - `openssl ecparam -name secp521r1 -genkey -noout -out ecp521.pem`
2. **Compute the fuse hash**:
   `./tegrasign_v3.py --pubkeyhash <pkc.pubkey> <pkc.hash> --key <pkc.pem>`
   and take the value printed after "tegra-fuse format (big-endian):".
3. **(Optional) SBK** for bootloader encryption: eight 32-bit words (32 bytes),
   big-endian hex.
4. **Write the fuse config XML** (Orin chip id is 0x23):
   ```xml
   <genericfuse MagicId="0x45535546" version="1.0.0">
     <fuse name="PublicKeyHash" size="64" value="0x..."/>
     <fuse name="BootSecurityInfo" size="4" value="0x1"/>
     <fuse name="SecurityMode" size="4" value="0x1"/>
   </genericfuse>
   ```
   `BootSecurityInfo` encodes the auth scheme (value differs for RSA-3K vs
   ECDSA vs SBK-enabled variants — take it from the doc's table, don't guess).
5. **Dry-run first** (device in recovery mode):
   `sudo ./odmfuse.sh -X <fuse_config> -i 0x23 --test <target_config>`
   The docs explicitly recommend `--test` before every real burn.
6. **Burn**: same command without `--test`. On a board whose PKC is already
   fused, subsequent odmfuse runs need `-k <pkc.pem>` to authenticate.
7. **From now on flash signed**: `sudo ./flash.sh -u <pkc_keyfile> [-v <sbk_keyfile>] <target_config> internal`
   (`-v` requires `-u`).

## Verify
`--test` output matches intent before burning. After burning, an unsigned image
no longer boots, and `flash.sh -u/-v` flashed images do. Fuse state can be read
back via the fuse tooling from recovery mode.

## Gotchas
- "Once a fuse bit is set to 1, you cannot change its value back to 0." There
  is no RMA-reset — a wrong PublicKeyHash means the board only trusts a key you
  don't have.
- `SecurityMode` (odm_production_mode) is the point of no return: after it's
  1, "all additional fuse write requests will be blocked." Burn every key fuse
  you'll ever need (PKC hash, SBK, KEKs, ODM fuses) in the same config or
  before it — never SecurityMode first.
- Order/dependency mistakes "might render the target device inoperable" (doc's
  wording) — keep dependent fuses in one XML so the tool sequences them.
- `odmfuse.sh` is deprecated in favor of Factory Secure Key Provisioning
  (FSKP) for production lines; same fuse-config and key formats, so the XML
  above carries over.
- Guard rails belong in tooling: treat any `odmfuse.sh` invocation without
  `--test` as a reviewed, two-person action (this repo's safety gate flags it).
