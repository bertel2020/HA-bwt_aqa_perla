# Changelog

*[🇩🇪 Deutsche Version](CHANGELOG.md)*

All notable changes to this project are documented here. Versions follow the
`version` field in `custom_components/bwt_aqa_perla/manifest.json`.

## Unreleased

### Breaking changes

- **Home Assistant 2026.10 or newer** is required (Home Assistant's serial port picker).
- The connection is now stored as a single value (`serial_port`, for TCP as `socket://host:port`); the unique ID is the connection itself. Existing entries are migrated automatically. The baud rate is now part of the connection and changed via **Reconfigure**; the options only contain the polling intervals.
- The integration depends on `usb` (loaded automatically).

### New

- Setup and reconfiguration start with a menu **USB / serial** or **Network (ser2net / TCP)**; the connection type can be switched later.
- Serial port selection through Home Assistant's port picker.
- Diagnostic sensors “Last successful poll” and “Failed polls”.
- Repair issue when no poll has succeeded for over 10 minutes.
- The device can be removed from the UI.

### Internal

- Tests and CI run on Python 3.14 and Home Assistant 2026.10.

## 1.0.0 – 2026-10-15

### Breaking changes

- **Device type** and **regeneration step** are now enum sensors. The state is a key (`type_12`, `step_0`), the UI shows the translated label. Automations or templates that compare against the previous German texts must be adjusted. Unknown values no longer produce a state.
- The **sensor classes** changed: 24 h water consumption and nominal/remaining capacity are plain measurements without the water device class. Peak flow uses the volume flow rate device class.
- TCP entries are migrated automatically (unique ID without `.0` on the port).
- Liter values are displayed without decimals for **new** entities, salt consumption with two. Existing entities keep their display until the display precision is changed in the entity settings.

### New

- “Remaining capacity column 1/2 (percent)” sensors and a “Regeneration active” binary sensor.
- The regeneration step is polled faster (default 15 s) than the other values (default 60 s); both intervals are configurable.
- Detected serial ports are offered in the wizard; documentation and texts for ser2net.
- The connection (port, host, TCP port) can be reconfigured.
- Diagnostics download with redacted configuration, values and raw frames.
- Sensors are only created for values the appliance actually reports.
- The device is named after the config entry.
- Icons for the sensors and an own logo for the README.

### Fixed

- Replies to a different command (echo, late or foreign replies with a second client) no longer abort the poll.
- A single failing command no longer makes every sensor unavailable; values expire only after three consecutive misses.
- Scaled values (salt consumption) without floating-point noise.
- The TCP port was stored as a float (`8899.0`) and ended up in the unique ID.

### Internal

- CI with pytest and ruff, Dependabot, Home Assistant integration tests.

## 0.3.0

Previous version (state of the first publication in the repository).
