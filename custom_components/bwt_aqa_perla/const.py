"""Constants for the BWT AQA Perla integration."""

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "bwt_aqa_perla"
PLATFORMS: Final = [Platform.SENSOR]

CONF_CONNECTION_TYPE: Final = "connection_type"
CONF_SERIAL_PORT: Final = "serial_port"
CONF_BAUDRATE: Final = "baudrate"
CONF_TCP_PORT: Final = "tcp_port"
CONF_POLL_INTERVAL: Final = "poll_interval"

CONNECTION_SERIAL: Final = "serial"
CONNECTION_TCP: Final = "tcp"

DEFAULT_BAUDRATE: Final = 9600
SUPPORTED_BAUDRATES: Final = (1200, 2400, 4800, 9600, 19200, 38400, 56000)
DEFAULT_TCP_PORT: Final = 8899
DEFAULT_POLL_INTERVAL: Final = 60

MANUFACTURER: Final = "BWT"
MODEL: Final = "AQA Perla"
