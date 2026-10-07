"""Config flow for BWT AQA Perla."""

from __future__ import annotations

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
    CONF_POLL_INTERVAL,
    CONF_SERIAL_PORT,
    CONF_TCP_PORT,
    CONNECTION_SERIAL,
    CONNECTION_TCP,
    DEFAULT_BAUDRATE,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_TCP_PORT,
    DOMAIN,
    SUPPORTED_BAUDRATES,
)
from .protocol import QUERY_SPECS, BwtProtocolError


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

        return self.async_show_form(
            step_id="serial", data_schema=_serial_schema(), errors=errors
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


def _poll_interval_field() -> dict:
    """Return the common polling interval schema field."""

    return {
        vol.Optional(CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL): NumberSelector(
            NumberSelectorConfig(
                min=30,
                max=3600,
                step=1,
                mode=NumberSelectorMode.BOX,
                unit_of_measurement="s",
            )
        )
    }


def _serial_schema() -> vol.Schema:
    """Return the direct-serial form schema."""

    fields: dict = {
        vol.Required(CONF_SERIAL_PORT): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT)
        ),
        vol.Optional(
            CONF_BAUDRATE, default=str(DEFAULT_BAUDRATE)
        ): _baudrate_selector(),
    }
    fields.update(_poll_interval_field())
    return vol.Schema(fields)


def _baudrate_selector() -> SelectSelector:
    """Return baud rates supported by the original serial control."""

    return SelectSelector(
        SelectSelectorConfig(
            options=[str(value) for value in SUPPORTED_BAUDRATES],
            mode=SelectSelectorMode.DROPDOWN,
        )
    )


def _tcp_schema() -> vol.Schema:
    """Return the TCP form schema."""

    fields: dict = {
        vol.Required(CONF_HOST): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT)
        ),
        vol.Optional(CONF_TCP_PORT, default=DEFAULT_TCP_PORT): NumberSelector(
            NumberSelectorConfig(min=1, max=65535, step=1, mode=NumberSelectorMode.BOX)
        ),
    }
    fields.update(_poll_interval_field())
    return vol.Schema(fields)


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
        fields[
            vol.Optional(
                CONF_POLL_INTERVAL,
                default=int(effective.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)),
            )
        ] = NumberSelector(
            NumberSelectorConfig(
                min=30,
                max=3600,
                step=1,
                mode=NumberSelectorMode.BOX,
                unit_of_measurement="s",
            )
        )
        return self.async_show_form(step_id="init", data_schema=vol.Schema(fields))
