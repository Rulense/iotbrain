---
title: "Connect a Jetson to AWS IoT Core over MQTT with mutual TLS (paho-mqtt / mosquitto, port 8883 or 443 ALPN)"
type: recipe
company: nvidia
keys:
  - "AmazonRootCA1.pem"
  - "-ats.iot"
  - "tls_set"
  - "mosquitto_pub"
  - "certificate verify failed"
  - "[Errno 104] Connection reset by peer"
platform_versions: ["all"]
devices: [all]
status: unverified
sources:
  - "https://aws.amazon.com/blogs/iot/how-to-integrate-nvidia-deepstream-on-jetson-devices-with-aws-iot-core-and-aws-iot-greengrass/"
  - "https://aws.amazon.com/blogs/iot/how-to-implement-mqtt-with-tls-client-authentication-on-port-443-from-client-devices-python/"
  - "https://docs.aws.amazon.com/iot/latest/developerguide/mqtt.html"
---
## Context
You want a Jetson edge device to publish telemetry/inference results to AWS IoT
Core. AWS IoT only accepts authenticated, encrypted connections (mutual TLS with
per-device X.509 certs), so plain `mqtt://` clients fail. Everything below is
plain userspace and aarch64-clean: `paho-mqtt` is pure Python and
`mosquitto-clients` is in Ubuntu's arm64 repos — no Jetson-specific wheels needed.

## Knowledge
1. In AWS IoT Core: create a Thing, generate the device certificate + private
   key, download them along with the Amazon root CA (`AmazonRootCA1.pem`), and
   attach an IoT policy that allows `iot:Connect`/`iot:Publish` for your
   client ID and topics.
2. Get your account's **ATS data endpoint** (not the legacy VeriSign one):
   ```
   aws iot describe-endpoint --endpoint-type iot:Data-ATS
   # -> xxxxxxxx-ats.iot.<region>.amazonaws.com
   ```
3. Smoke-test from the Jetson with mosquitto:
   ```
   sudo apt install mosquitto-clients
   mosquitto_pub -d -h xxxxxxxx-ats.iot.<region>.amazonaws.com -p 8883 \
     --cafile AmazonRootCA1.pem --cert device.pem.crt --key private.pem.key \
     -t 'jetson/test' -m 'hello from jetson' --tls-version tlsv1.2
   ```
4. Python client:
   ```python
   import paho.mqtt.client as mqtt   # pip3 install paho-mqtt
   c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="my-jetson-01")
   c.tls_set(ca_certs="AmazonRootCA1.pem",
             certfile="device.pem.crt", keyfile="private.pem.key")
   c.connect("xxxxxxxx-ats.iot.<region>.amazonaws.com", 8883)
   c.publish("jetson/test", "hello")
   ```
   paho-mqtt >= 2.0 (what `pip3 install paho-mqtt` installs today) requires the
   `CallbackAPIVersion` first argument — omitting it raises `ValueError`. If
   you're pinned to paho 1.x, drop that argument
   (`mqtt.Client(client_id="my-jetson-01")`).
5. If outbound 8883 is blocked (common on guest/corporate networks), use MQTT
   over port 443 with the ALPN protocol name `x-amzn-mqtt-ca` (ssl context with
   `set_alpn_protocols(["x-amzn-mqtt-ca"])`, see the AWS port-443 blog), or
   MQTT-over-WebSocket on 443.

## Verify
`mosquitto_pub ... -d` prints `CONNACK` then `PUBACK` (QoS 1), and the message
appears in the AWS IoT console MQTT test client subscribed to `jetson/test`.

## Gotchas
- `[Errno 104] Connection reset by peer` right after the TLS handshake is
  almost always **authorization**, not TLS: the IoT policy doesn't allow this
  client ID/topic, or the cert is inactive/not attached to the policy.
- `certificate verify failed` → wrong CA file (must be the Amazon root CA that
  matches the ATS endpoint) or the device clock is wrong — Jetsons without an
  RTC battery boot in the past and fail every TLS handshake; see
  [rtc-clock-reset-breaks-tls.md](rtc-clock-reset-breaks-tls.md).
- Don't bake one identity into a fleet image: AWS IoT allows one live
  connection per MQTT **client ID**, and a new connect with the same ID bumps
  the existing session — cloned devices with the same client ID knock each
  other offline in a connect/disconnect loop. Give every unit its own client ID
  (and, for revocability, its own certificate).
