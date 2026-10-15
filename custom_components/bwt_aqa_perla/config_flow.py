"""Config flow for BWT AQA Perla."""

from __future__ import annotations

import glob
import os
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_HOST
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from . import create_client
from .client import BwtConnectionError
from .const import (
    CONF_BAUDRATE,
    CONF_CONNECTION_TYPE,
    CONF_FAST_POLL_INTERVAL,
    CONF_POLL_INTERVAL,
    CONF_SERIAL_PORT,
    CONF_TCP_PORT,
    CONNECTION_SERIAL,
    CONNECTION_TCP,
    DEFAULT_BAUDRATE,
    DEFAULT_FAST_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_TCP_PORT,
    DOMAIN,
    MAX_POLL_INTERVAL,
    MIN_FAST_POLL_INTERVAL,
    MIN_POLL_INTERVAL,
    SUPPORTED_BAUDRATES,
)
from .protocol import QUERY_SPECS, BwtProtocolError


def _list_serial_ports() -> list[SelectOptionDict]:
    """Return local serial ports, preferring stable /dev/serial/by-id paths."""

    try:
        from serial.tools import list_ports

        ports = list(list_ports.comports())
    except (ImportError, OSError):
        return []

    stable_paths = {
        os.path.realpath(path): path for path in glob.glob("/dev/serial/by-id/*")
    }
    options: list[SelectOptionDict] = []
    for port in sorted(ports, key=lambda item: item.device):
        value = stable_paths.get(os.path.realpath(port.device), port.device)
        description = port.description if port.description != "n/a" else ""
        label = f"{value} ({description})" if description else value
        options.append(SelectOptionDict(value=value, label=label))
    return options


def _query_spec(key: str):
    """Return one query definition by key."""

    return next(spec for spec in QUERY_SPECS if spec.key == key)


class BwtAqaPerlaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the appliance."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow state."""

        self._connection_type = CONNECTION_SERIAL

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlowWithReload:
        """Create the options flow."""

        return BwtAqaPerlaOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose the transport."""

        if user_input is not None:
            self._connection_type = user_input[CONF_CONNECTION_TYPE]
            if self._connection_type == CONNECTION_SERIAL:
                return await self.async_step_serial()
            return await self.async_step_tcp()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CONNECTION_TYPE, default=CONNECTION_SERIAL
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=[CONNECTION_SERIAL, CONNECTION_TCP],
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key="connection_type",
                        )
                    )
                }
            ),
        )

    async def async_step_serial(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure a directly attached serial device."""

        errors: dict[str, str] = {}
        if user_input is not None:
            data = {CONF_CONNECTION_TYPE: CONNECTION_SERIAL, **user_input}
            errors = await self._async_validate(data)
            if not errors:
                unique_id = f"serial:{user_input[CONF_SERIAL_PORT]}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="BWT AQA Perla", data=data)

        ports = await self.hass.async_add_executor_job(_list_serial_ports)
        return self.async_show_form(
            step_id="serial", data_schema=_serial_schema(ports), errors=errors
        )

    async def async_step_tcp(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure a raw serial-over-TCP bridge."""

        errors: dict[str, str] = {}
        if user_input is not None:
            data = {CONF_CONNECTION_TYPE: CONNECTION_TCP, **user_input}
            errors = await self._async_validate(data)
            if not errors:
                unique_id = f"tcp:{user_input[CONF_HOST]}:{user_input[CONF_TCP_PORT]}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"BWT AQA Perla ({user_input[CONF_HOST]})", data=data
                )

        return self.async_show_form(
            step_id="tcp", data_schema=_tcp_schema(), errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the serial port or the TCP host and port of an entry."""

        entry = self._get_reconfigure_entry()
        effective = {**entry.data, **entry.options}
        is_serial = entry.data[CONF_CONNECTION_TYPE] == CONNECTION_SERIAL
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = await self._async_validate({**effective, **user_input})
            if not errors:
                if is_serial:
                    unique_id = f"serial:{user_input[CONF_SERIAL_PORT]}"
                    title = entry.title
                else:
                    unique_id = (
                        f"tcp:{user_input[CONF_HOST]}:{user_input[CONF_TCP_PORT]}"
                    )
                    title = f"BWT AQA Perla ({user_input[CONF_HOST]})"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_update_reload_and_abort(
                    entry, unique_id=unique_id, title=title, data_updates=user_input
                )

        if is_serial:
            ports = await self.hass.async_add_executor_job(_list_serial_ports)
            schema = vol.Schema(
                {vol.Required(CONF_SERIAL_PORT): _serial_port_selector(ports)}
            )
        else:
            schema = _tcp_connection_schema()
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                schema, user_input or effective
            ),
            errors=errors,
        )

    async def _async_validate(self, data: dict[str, Any]) -> dict[str, str]:
        """Connect and read one documented value before saving."""

        client = create_client(data)
        try:
            await client.async_query(_query_spec("water_consumption_24h"))
        except BwtConnectionError:
            return {"base": "cannot_connect"}
        except BwtProtocolError:
            return {"base": "invalid_response"}
        except Exception:  # noqa: BLE001 - serial backends may raise platform errors
            return {"base": "unknown"}
        finally:
            await client.async_close()
        return {}


def _interval_selector(minimum: int) -> NumberSelector:
    """Return a seconds selector with the given minimum."""

    return NumberSelector(
        NumberSelectorConfig(
            min=minimum,
            max=MAX_POLL_INTERVAL,
            step=1,
            mode=NumberSelectorMode.BOX,
            unit_of_measurement="s",
        )
    )


def _poll_interval_fields(
    poll_interval: int = DEFAULT_POLL_INTERVAL,
    fast_poll_interval: int = DEFAULT_FAST_POLL_INTERVAL,
) -> dict:
    """Return the common polling interval schema fields."""

    return {
        vol.Optional(CONF_POLL_INTERVAL, default=poll_interval): _interval_selector(
            MIN_POLL_INTERVAL
        ),
        vol.Optional(
            CONF_FAST_POLL_INTERVAL, default=fast_poll_interval
        ): _interval_selector(MIN_FAST_POLL_INTERVAL),
    }


def _serial_port_selector(ports: list[SelectOptionDict]) -> Any:
    """Return a port dropdown that also accepts a manually typed path."""

    if not ports:
        return TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT))
    return SelectSelector(
        SelectSelectorConfig(
            options=ports, custom_value=True, mode=SelectSelectorMode.DROPDOWN
        )
    )


def _serial_schema(ports: list[SelectOptionDict]) -> vol.Schema:
    """Return the direct-serial form schema."""

    fields: dict = {
        vol.Required(CONF_SERIAL_PORT): _serial_port_selector(ports),
        vol.Optional(
            CONF_BAUDRATE, default=str(DEFAULT_BAUDRATE)
        ): _baudrate_selector(),
    }
    fields.update(_poll_interval_fields())
    return vol.Schema(fields)


def _baudrate_selector() -> SelectSelector:
    """Return baud rates supported by the original serial control."""

    return SelectSelector(
        SelectSelectorConfig(
            options=[str(value) for value in SUPPORTED_BAUDRATES],
            mode=SelectSelectorMode.DROPDOWN,
        )
    )


def _tcp_connection_schema() -> vol.Schema:
    """Return the host and port fields of the TCP form."""

    return vol.Schema(
        {
            vol.Required(CONF_HOST): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Optional(CONF_TCP_PORT, default=DEFAULT_TCP_PORT): NumberSelector(
                NumberSelectorConfig(
                    min=1, max=65535, step=1, mode=NumberSelectorMode.BOX
                )
            ),
        }
    )


def _tcp_schema() -> vol.Schema:
    """Return the TCP form schema."""

    return _tcp_connection_schema().extend(_poll_interval_fields())


class BwtAqaPerlaOptionsFlow(OptionsFlowWithReload):
    """Allow changing communication and polling options after setup."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage integration options."""

        if user_input is not None:
            return self.async_create_entry(data=user_input)

        effective = {**self.config_entry.data, **self.config_entry.options}
        fields: dict = {}
        if effective[CONF_CONNECTION_TYPE] == CONNECTION_SERIAL:
            fields[
                vol.Optional(
                    CONF_BAUDRATE,
                    default=str(effective.get(CONF_BAUDRATE, DEFAULT_BAUDRATE)),
                )
            ] = _baudrate_selector()
        fields.update(
            _poll_interval_fields(
                int(effective.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)),
                int(effective.get(CONF_FAST_POLL_INTERVAL, DEFAULT_FAST_POLL_INTERVAL)),
            )
        )
        return self.async_show_form(step_id="init", data_schema=vol.Schema(fields))
