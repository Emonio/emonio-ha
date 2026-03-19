import ipaddress
import logging

import voluptuous as vol
from homeassistant import config_entries
from pymodbus.client import ModbusTcpClient

from .const import DOMAIN
from .helpers import get_mac_address

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host"): str,
        vol.Required("port", default=502): int,
    }
)


class EmonioModbusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Emonio Modbus."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                ipaddress.ip_address(user_input["host"])
            except ValueError:
                errors["host"] = "invalid_ip"
            else:
                return await self._async_test_connection(user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def _async_test_connection(self, user_input):
        """Test the connection to the Modbus device."""
        errors = {}
        host = user_input["host"]
        port = user_input["port"]

        def connect_client():
            client = ModbusTcpClient(host=host, port=port)
            connected = client.connect()
            client.close()
            return connected

        connected = await self.hass.async_add_executor_job(connect_client)
        if connected:
            mac_address = await self.hass.async_add_executor_job(get_mac_address, host)
            if mac_address:
                mac_suffix = mac_address.replace(":", "")[-6:].upper()
                await self.async_set_unique_id(mac_suffix)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Emonio P3 {mac_suffix}", data=user_input
                )
            errors["base"] = "cannot_get_mac"
        else:
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )
