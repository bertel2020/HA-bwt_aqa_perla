"""Config flow for BWT AQA Perla."""

from __future__ import annotations

import glob
import os
from typing import Any
from urllib.parse import urlparse

import voluptuous as vol
from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
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
    DEFAULT_TITLE,
    DOMAIN,
    MAX_POLL_INTERVAL,
    MIN_FAST_POLL_INTERVAL,
    MIN_POLL_INTERVAL,
    SOCKET_PREFIX,
    SUPPORTED_BAUDRATES,
)
from .protocol import QUERY_SPECS, BwtProtocolError


def _list_serial_ports() -> list[SelectOptionDict]:
    """Return local serial ports, preferring stable /dev/serial/by-id paths."""

    try:
        from serial.tools import list_ports

        ports = list(list_ports.comports())
    except ImportError, OSError:
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


def _normalize(user_input: dict[str, Any]) -> dict[str, Any]:
    """Store whole-number selector values as integers instead of floats."""

    return {
        key: int(value) if isinstance(value, float) and value.is_integer() else value
        for key, value in user_input.items()
    }


def _query_spec(key: str):
    """Return one query definition by key."""

    return next(spec for spec in QUERY_SPECS if spec.key == key)


class BwtAqaPerlaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the appliance."""

    VERSION = 1
    MINOR_VERSION = 3

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

    async def _async_finish(
        self, data: dict[str, Any], title: str
    ) -> ConfigFlowResult | str:
        """Validate and store the connection; return an error key on failure."""

        if error := await self._async_validate(data):
            return error
        port = data[CONF_SERIAL_PORT]
        await self.async_set_unique_id(port)
        if self.source == SOURCE_RECONFIGURE:
            self._abort_if_unique_id_configured()
            return self.async_update_reload_and_abort(
                self._get_reconfigure_entry(), unique_id=port, title=title, data=data
            )
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=title, data=data)

    async def async_step_serial(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure a directly attached serial device."""

        errors: dict[str, str] = {}
        if user_input is not None:
            user_input = _normalize(user_input)
            data = {
                CONF_SERIAL_PORT: user_input[CONF_SERIAL_PORT],
                CONF_BAUDRATE: int(user_input[CONF_BAUDRATE]),
            }
            title = (
                self._get_reconfigure_entry().title
                if self.source == SOURCE_RECONFIGURE
                else DEFAULT_TITLE
            )
            result = await self._async_finish(data, title)
            if not isinstance(result, str):
                return result
            errors["base"] = result

        ports = await self.hass.async_add_executor_job(_list_serial_ports)
        return self.async_show_form(
            step_id="serial",
            data_schema=self.add_suggested_values_to_schema(
                _serial_schema(ports), user_input or self._current_values()
            ),
            errors=errors,
        )

    async def async_step_tcp(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure a raw serial-over-TCP bridge."""

        errors: dict[str, str] = {}
        if user_input is not None:
            user_input = _normalize(user_input)
            host = user_input[CONF_HOST].strip()
            port = int(user_input[CONF_TCP_PORT])
            if not host or "/" in host or ":" in host.strip("[]"):
                errors["base"] = "invalid_host"
            else:
                result = await self._async_finish(
                    {CONF_SERIAL_PORT: f"{SOCKET_PREFIX}{host}:{port}"},
                    f"{DEFAULT_TITLE} ({host})",
                )
                if not isinstance(result, str):
                    return result
                errors["base"] = result

        return self.async_show_form(
            step_id="tcp",
            data_schema=self.add_suggested_values_to_schema(
                _tcp_schema(), user_input or self._current_values()
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the connection of an existing entry."""

        port = self._get_reconfigure_entry().data[CONF_SERIAL_PORT]
        if port.startswith(SOCKET_PREFIX):
            return await self.async_step_tcp()
        return await self.async_step_serial()

    def _current_values(self) -> dict[str, Any] | None:
        """Return form values of the entry being reconfigured, if any."""

        if self.source != SOURCE_RECONFIGURE:
            return None
        data = self._get_reconfigure_entry().data
        port = data[CONF_SERIAL_PORT]
        if port.startswith(SOCKET_PREFIX):
            url = urlparse(port)
            return {CONF_HOST: url.hostname, CONF_TCP_PORT: url.port}
        return {
            CONF_SERIAL_PORT: port,
            CONF_BAUDRATE: str(data.get(CONF_BAUDRATE, DEFAULT_BAUDRATE)),
        }

    async def _async_validate(self, data: dict[str, Any]) -> str | None:
        """Connect and read one documented value before saving."""

        client = create_client(data)
        try:
            await client.async_query(_query_spec("water_consumption_24h"))
        except BwtConnectionError:
            return "cannot_connect"
        except BwtProtocolError:
            return "invalid_response"
        except Exception:  # noqa: BLE001 - serial backends may raise platform errors
            return "unknown"
        finally:
            await client.async_close()
        return None


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


def _serial_port_selector(ports: list[SelectOptionDict]) -> Any:
    """Return a port dropdown that also accepts a manually typed path."""

    if not ports:
        return TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT))
    return SelectSelector(
        SelectSelectorConfig(
            options=ports, custom_value=True, mode=SelectSelectorMode.DROPDOWN
        )
    )


def _baudrate_selector() -> SelectSelector:
    """Return baud rates supported by the original serial control."""

    return SelectSelector(
        SelectSelectorConfig(
            options=[str(value) for value in SUPPORTED_BAUDRATES],
            mode=SelectSelectorMode.DROPDOWN,
        )
    )


def _serial_schema(ports: list[SelectOptionDict]) -> vol.Schema:
    """Return the direct-serial form schema."""

    return vol.Schema(
        {
            vol.Required(CONF_SERIAL_PORT): _serial_port_selector(ports),
            vol.Optional(
                CONF_BAUDRATE, default=str(DEFAULT_BAUDRATE)
            ): _baudrate_selector(),
        }
    )


def _tcp_schema() -> vol.Schema:
    """Return the TCP form schema."""

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


class BwtAqaPerlaOptionsFlow(OptionsFlowWithReload):
    """Allow changing the polling intervals after setup."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage integration options."""

        if user_input is not None:
            return self.async_create_entry(data=_normalize(user_input))

        options = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_POLL_INTERVAL,
                        default=int(
                            options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
                        ),
                    ): _interval_selector(MIN_POLL_INTERVAL),
                    vol.Optional(
                        CONF_FAST_POLL_INTERVAL,
                        default=int(
                            options.get(
                                CONF_FAST_POLL_INTERVAL, DEFAULT_FAST_POLL_INTERVAL
                            )
                        ),
                    ): _interval_selector(MIN_FAST_POLL_INTERVAL),
                }
            ),
        )
