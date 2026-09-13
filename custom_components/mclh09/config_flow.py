"""Config flow for LifeControl MCLH-09 integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class MCLH09ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LifeControl MCLH-09."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_device: BluetoothServiceInfoBleak | None = None
        self._discovered_devices: dict[str, str] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle the bluetooth discovery step."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        name = discovery_info.name
        if not name or ("mclh" not in name.lower() and "lifecontrol" not in name.lower()):
            # Fallback filter just in case it doesn't broadcast this exactly,
            # or you can restrict based on specific prefixes
            pass

        self._discovery_info = discovery_info

        self.context["title_placeholders"] = {
            "name": discovery_info.name or discovery_info.address,
        }

        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._discovery_info.name or self._discovery_info.address,
                data={CONF_ADDRESS: self._discovery_info.address},
            )

        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={
                "name": self._discovery_info.name or self._discovery_info.address
            },
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step to pick discovered device or enter MAC."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input.get("name", address),
                data={CONF_ADDRESS: address},
            )

        # Find already discovered devices
        current_addresses = self._async_current_ids()
        for discovery_info in async_discovered_service_info(self.hass):
            address = discovery_info.address
            if address in current_addresses:
                continue
            if discovery_info.name and ("mclh" in discovery_info.name.lower() or "lifecontrol" in discovery_info.name.lower()):
                self._discovered_devices[address] = f"{discovery_info.name} ({address})"
            elif discovery_info.name:
                self._discovered_devices[address] = f"{discovery_info.name} ({address})"

        if not self._discovered_devices:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_ADDRESS): cv.string,
                    }
                ),
                errors=errors,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(self._discovered_devices),
                }
            ),
            errors=errors,
        )
