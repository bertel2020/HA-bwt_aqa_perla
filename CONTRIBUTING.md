# Contributing

Thanks for helping! Bug reports and pull requests are welcome, in English or
German.

## Local development

Python 3.14 is required.

```bash
python3.13 -m venv .venv
.venv/bin/pip install -r requirements_test.txt
.venv/bin/ruff check . && .venv/bin/ruff format --check .
.venv/bin/pytest
```

The tests need no appliance: the protocol and client tests run against
scripted byte streams, and the Home Assistant tests (config flow, entities,
diagnostics) use a fake client. Please add or update tests with your change
and keep `ruff` clean.

## Protocol findings

There is no vendor documentation; the protocol was inferred from public
telegram captures and IP-Symcon scripts. If your appliance behaves
differently (other length, scale, unit or unsupported commands), please open
an issue and attach the **diagnostics download** (Settings → Devices &
services → BWT AQA Perla → ⋮ → Download diagnostics) together with the value
the appliance itself displays. The raw frame per command in the diagnostics
makes it possible to verify the decoding.

The command table lives in
[`custom_components/bwt_aqa_perla/protocol.py`](custom_components/bwt_aqa_perla/protocol.py).
Commands that are not essential must stay `optional=True` so a different
firmware cannot make the core readings unavailable.

## Translations

`strings.json` and `translations/de.json` carry the German texts,
`translations/en.json` the English ones. Enum states (device type,
regeneration step) are translated through `state` keys, so new values must be
added to all three files.

## Continuous integration

`.github/workflows/validate.yml` runs on every push and pull request:

- HACS validation of the repository.
- Hassfest validation against Home Assistant's integration requirements.
- `ruff` (lint and format check) and `pytest`.
