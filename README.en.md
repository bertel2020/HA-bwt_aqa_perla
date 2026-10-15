<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/bertel2020/HA-bwt_aqa_perla/main/custom_components/bwt_aqa_perla/brand/dark_logo.png">
    <img src="https://raw.githubusercontent.com/bertel2020/HA-bwt_aqa_perla/main/custom_components/bwt_aqa_perla/brand/logo.png" alt="BWT AQA Perla" width="320">
  </picture>
</p>

<h1 align="center">BWT AQA Perla</h1>

<p align="center">
  Home Assistant integration for the BWT AQA Perla – local via USB/serial or serial over TCP, set up entirely through the UI.
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom"></a>
  <a href="https://www.home-assistant.io/"><img src="https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-18BCF2.svg?logo=home-assistant&logoColor=white" alt="Home Assistant"></a>
  <a href="https://github.com/bertel2020/HA-bwt_aqa_perla/releases"><img src="https://img.shields.io/github/v/release/bertel2020/HA-bwt_aqa_perla?sort=semver&include_prereleases" alt="Release"></a>
  <a href="https://github.com/bertel2020/HA-bwt_aqa_perla/actions/workflows/validate.yml"><img src="https://github.com/bertel2020/HA-bwt_aqa_perla/actions/workflows/validate.yml/badge.svg" alt="Validate"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/bertel2020/HA-bwt_aqa_perla" alt="LICENSE"></a>
</p>

<p align="center">
  <a href="https://buymeacoffee.com/bertel2020"><img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-FFDD00?logo=buy-me-a-coffee&logoColor=black" alt="Buy Me a Coffee"></a>
  <a href="https://ko-fi.com/bertel2020"><img src="https://img.shields.io/badge/Ko--fi-support-FF5E5B?logo=ko-fi&logoColor=white" alt="Ko-fi"></a>
  <a href="https://paypal.me/RobertoMartins"><img src="https://img.shields.io/badge/PayPal-donate-00457C?logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

<p align="center"><em><a href="README.md">🇩🇪 Deutsche Version</a></em></p>

A UI-configurable Home Assistant custom integration for the older **BWT AQA Perla** (twin-column water softener). It reads water, salt and regeneration data through the appliance's serial interface and exposes them as sensors. There is no cloud communication, and the appliance is only ever read from.

## Features

- Water, salt and regeneration data as sensors, suitable for the water dashboard and long-term statistics
- Remaining capacity per column in liters and percent
- Current regeneration step as text (German/English) and a “Regeneration active” binary sensor
- The regeneration step is polled faster than the other values
- Direct serial connection (with port picker) or serial over TCP (e.g. ser2net)
- Resilient to partial failures: one missing value does not make every sensor unavailable
- Setup, options and reconfiguration entirely through the UI
- Diagnostics download for troubleshooting

## Requirements

- Home Assistant **2026.2** or newer (tested against this version; older versions are not verified).
- A BWT AQA Perla with a serial interface, connected through a USB serial/UART adapter on the Home Assistant host **or** a transparent raw TCP bridge (ser2net, RS232-Ethernet gateway, etc.).
- Access to the interface by **exactly one** client at a time (see [Troubleshooting](#troubleshooting)).

## Installation

### Via HACS (recommended)

[![Open the HACS repository in My Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=bertel2020&repository=HA-bwt_aqa_perla&category=integration)
[![Add BWT AQA Perla to My Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=bwt_aqa_perla)

1. Use the first button to open the repository in HACS.
2. Download **BWT AQA Perla** and restart Home Assistant.
3. Use the second button to add the integration. Alternatively open **Settings → Devices & services → Add integration → BWT AQA Perla**.

If the first button does not work, add `https://github.com/bertel2020/HA-bwt_aqa_perla` in HACS under **Integrations → Custom repositories** with the category **Integration**.

### Manual

Copy the `custom_components/bwt_aqa_perla` directory to `/config/custom_components/bwt_aqa_perla` and restart Home Assistant.

## Setup

Settings → Devices & services → Add integration → **BWT AQA Perla**. Before saving, the wizard test-reads the 24 h consumption.

1. Choose **USB / serial** or **Serial over TCP**.
   - USB / serial: port, baud rate (default `9600`).
   - Serial over TCP: host/IP and raw TCP port (default `8899`).
2. Set the polling intervals (default 60 s, and 15 s for the regeneration step).

### USB / serial

The wizard offers detected serial ports as a dropdown (stable `/dev/serial/by-id/...` paths first); a custom path can still be typed in. Prefer a stable path over `/dev/ttyUSB0`. With Home Assistant Container the USB device must be passed through to the container.

The appliance usually uses `9600 baud, 8 data bits, no parity, 1 stop bit` (`9600 8N1`); this is the integration's default. Other units may use 19200 baud – the actual setting of your appliance is what counts.

### Serial over TCP (ser2net)

This option expects a **transparent raw TCP connection**. The bridge must set baud rate, 8 data bits, no parity and 1 stop bit on its serial port itself. Telnet, RFC2217, HTTP and Modbus TCP gateways are not supported.

On a machine with the adapter attached (e.g. a Raspberry Pi), [ser2net](https://github.com/cminyard/ser2net) exposes the serial port as raw TCP. Example for `/etc/ser2net.yaml` (ser2net 4.x):

```yaml
%YAML 1.1
---
connection: &bwt-aqa-perla
  accepter: tcp,8899
  enable: on
  connector: serialdev,/dev/serial/by-id/usb-XXXX,9600n81,local
```

For ser2net 3.x the corresponding line in `/etc/ser2net.conf` is:

```
8899:raw:0:/dev/serial/by-id/usb-XXXX:9600 8DATABITS NONE 1STOPBIT
```

In the integration choose **Serial over TCP**, enter the machine's host and port `8899`. The baud rate (`9600n81`) is set only in ser2net. The `tcp` accepter is raw; **do not** use `telnet(rfc2217)` or `telnet`.

## Configuration (options)

Via the integration's **Configure** button:

| Option | Default | Range | Meaning |
|---|---:|---|---|
| Polling interval | 60 s | 30–3600 s | Interval for all values except the regeneration step |
| Regeneration polling interval | 15 s | 5–3600 s | Interval for the regeneration step |
| Baud rate | 9600 | 1200–56000 | direct serial connection only |

With serial over TCP the baud rate must be set on the bridge itself. Change the serial port, or host and TCP port, through the integration's menu (⋮) under **Reconfigure** without re-adding the integration. Changes reload the integration automatically.

## Entities

One device **“BWT AQA Perla”** is created (with the host in the title for serial over TCP). Optional values are only created when the appliance answers them; older firmware versions do not support every command.

The entity ID is built from device name + entity name (Home Assistant's default scheme with `has_entity_name`). Home Assistant assigns it **once at first setup**, based on the **UI language active at that moment**; the table shows the English names. With another language or device name your actual IDs differ – what counts is what **Settings → Devices & services → BWT AQA Perla** shows.

| Friendly name | Entity ID | Command | Description |
|---|---|---|---|
| Water consumption 24 h | `sensor.bwt_aqa_perla_water_consumption_24_h` | `0x08` | Water consumption over the last 24 hours (rolling value) |
| Total water consumption | `sensor.bwt_aqa_perla_total_water_consumption` | `0x10` | Increasing total counter, suitable for the water dashboard |
| Total salt consumption | `sensor.bwt_aqa_perla_total_salt_consumption` | `0x13` | Increasing total counter in kg (raw value divided by 1000) |
| Peak flow today | `sensor.bwt_aqa_perla_peak_flow_today` | `0x05` | Peak flow today; optional |
| Peak flow 24 h | `sensor.bwt_aqa_perla_peak_flow_24_h` | `0x06` | Peak flow over the last 24 hours; optional |
| Peak flow since commissioning | `sensor.bwt_aqa_perla_peak_flow_since_commissioning` | `0x07` | Peak flow since commissioning; optional |
| Nominal capacity column 1 | `sensor.bwt_aqa_perla_nominal_capacity_column_1` | `0x25` | Nominal capacity of column 1 in liters |
| Nominal capacity column 2 | `sensor.bwt_aqa_perla_nominal_capacity_column_2` | `0x26` | Nominal capacity of column 2 in liters |
| Remaining capacity column 1 | `sensor.bwt_aqa_perla_remaining_capacity_column_1` | `0x02` | Remaining capacity of column 1 in liters |
| Remaining capacity column 2 | `sensor.bwt_aqa_perla_remaining_capacity_column_2` | `0x03` | Remaining capacity of column 2 in liters |
| Remaining capacity column 1 (percent) | `sensor.bwt_aqa_perla_remaining_capacity_column_1_percent` | derived | Remaining divided by nominal capacity; only for a used column |
| Remaining capacity column 2 (percent) | `sensor.bwt_aqa_perla_remaining_capacity_column_2_percent` | derived | Remaining divided by nominal capacity; only for a used column |
| Regenerations | `sensor.bwt_aqa_perla_regenerations` | `0x11` | Increasing counter of regenerations |
| Regenerations since service | `sensor.bwt_aqa_perla_regenerations_since_service` | `0x12` | Regenerations since the last service; optional |
| Regeneration step | `sensor.bwt_aqa_perla_regeneration_step` | `0x04` | Current step as text; attributes `raw_value`, `normalized_step`, `flag_bit_7`, `short_code` |
| Regenerant saving | `sensor.bwt_aqa_perla_regenerant_saving` | `0x14` | Raw value, unit not conclusively determined; optional |
| Regeneration active | `binary_sensor.bwt_aqa_perla_regeneration_active` | derived | On while the step is not “columns in operation” |
| Device type | `sensor.bwt_aqa_perla_device_type` | `0x01` | Device type, e.g. “Aqua Perla”; diagnostic, optional |
| Commissioning date | `sensor.bwt_aqa_perla_commissioning_date` | `0x15` | Commissioning date; diagnostic, optional |
| Power electronics software version | `sensor.bwt_aqa_perla_power_electronics_software_version` | `0x19` | Power electronics version, e.g. `3.94`; diagnostic |
| Control panel software version | `sensor.bwt_aqa_perla_control_panel_software_version` | `0x19` | Control panel version, e.g. `155`; diagnostic |
| Combined software version | `sensor.bwt_aqa_perla_combined_software_version` | `0x19` | Combined response, e.g. `3.94#155`; diagnostic, disabled by default |

The states of **Device type** and **Regeneration step** are keys (`type_12`, `step_0`); the UI shows the translated label. Automations should therefore compare against these keys or use the “Regeneration active” binary sensor.

Liter values are displayed without decimals by default, salt consumption with two. This can be changed per entity under **Display precision**.

## Examples

Notification when a regeneration starts (adjust the entity ID if necessary):

```yaml
automation:
  - alias: BWT regeneration started
    triggers:
      - trigger: state
        entity_id: binary_sensor.bwt_aqa_perla_regeneration_active
        from: "off"
        to: "on"
    actions:
      - action: notify.notify
        data:
          message: "The water softener is regenerating."
```

Warning on low remaining capacity:

```yaml
automation:
  - alias: BWT remaining capacity low
    triggers:
      - trigger: numeric_state
        entity_id: sensor.bwt_aqa_perla_remaining_capacity_column_1_percent
        below: 10
    actions:
      - action: notify.notify
        data:
          message: "Remaining capacity of column 1 is below 10 %."
```

## Troubleshooting

**All sensors are briefly unavailable, or `Expected command` errors appear in the log.** If a second system (such as IP-Symcon or SoftControl) accesses the same serial line or bridge at the same time, the replies get mixed up. The integration skips foreign replies, but only a single active client is clean. The integration opens a new connection per poll; with bridges that allow only one connection this can displace another client.

**Connection fails.** Check host, port and baud rate. With ser2net the accepter must be `tcp` (raw), not `telnet`. For USB check that the device reaches the container and Home Assistant can access the port.

**Individual sensors are missing.** Optional values are only created when the appliance answers them.

**Debug logging.** Enable in `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.bwt_aqa_perla: debug
```

**Download diagnostics.** Under **Settings → Devices & services → BWT AQA Perla → ⋮ → Download diagnostics** you find the (redacted) configuration, the decoded values and the most recently received raw frame per command. Please attach it to bug reports.

Please report bugs and requests as an [issue](https://github.com/bertel2020/HA-bwt_aqa_perla/issues).

## How it works

The appliance is polled with a simple telegram protocol:

```
0x0D | command | length | payload | checksum | 0x0A
```

The checksum is the sum of all preceding bytes modulo 256; multi-byte values are little-endian. The implementation reads length-framed frames completely, validates boundaries, command and checksum, and runs all queries sequentially. Replies to a different command (echo, late or foreign replies) are skipped. The protocol was inferred from publicly available telegram captures and IP-Symcon scripts; there is no vendor documentation.

If a single query fails, the other sensors keep their value; a missing value is retained and only becomes unavailable after three missed polls. The connection is closed cleanly after every poll and reopened on the next, which reduces the risk of stuck USB or serial-over-TCP sessions.

Bit 7 of the regeneration step is masked (`raw & 0x7F`); it stays visible as an attribute together with the original byte. A software version such as `Version: 3.94#155` is split into power electronics (`3.94`) and control panel (`155`).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Changelog

See [CHANGELOG.en.md](CHANGELOG.en.md).

## Disclaimer

This is an independent, community-developed integration. It is not affiliated with BWT and is neither supported nor endorsed by BWT. The protocol was inferred from publicly available sources without vendor documentation.

The integration only reads from the appliance and sends no write commands. It is provided **“as is”, without warranty of any kind** (see [LICENSE](LICENSE)) – use at your own risk.

## Trademarks

The logo and icon of this integration are original designs (`custom_components/bwt_aqa_perla/brand/`, source in `assets/`) and are covered by this project's license. “BWT”, “BWT Holding GmbH”, “BWT Wassertechnik GmbH” and “AQA Perla” are trademarks of their respective owners; they are mentioned solely to describe which hardware the integration works with.

## Copyright & license

Copyright © 2026 bertel2020. Licensed under the [MIT License](LICENSE).
