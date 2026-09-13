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
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig

from .const import DOMAIN, CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL

_LOGGER = logging.getLogger(__name__)

class MCLH09ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LifeControl MCLH-09."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_device: BluetoothServiceInfoBleak | None = None
        self._discovered_devices: dict[str, str] = {}

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return MCLH09OptionsFlowHandler(config_entry)

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle the bluetooth discovery step."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        name = discovery_info.name
        if not name or ("mclh" not in name.lower() and "lifecontrol" not in name.lower()):
            return self.async_abort(reason="not_supported")

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
            title = self._discovery_info.name or self._discovery_info.address
            address = self._discovery_info.address.upper()
            return self.async_create_entry(
                title=f"{title} ({address})",
                data={CONF_ADDRESS: address},
                options={CONF_POLLING_INTERVAL: user_input.get(CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL)},
            )

        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={
                "name": self._discovery_info.name or self._discovery_info.address
            },
            data_schema=vol.Schema({
                vol.Required(CONF_POLLING_INTERVAL, default=DEFAULT_POLLING_INTERVAL): vol.All(vol.Coerce(int), vol.Range(min=1)),
            }),
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step to pick discovered device or enter MAC."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS].upper()
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()

            # Use the friendly name if selected from the dropdown, otherwise use MAC as title
            title = self._discovered_devices.get(address, address)
            if "(" in title and ")" in title:
                title = title.split(" (")[0]

            return self.async_create_entry(
                title=f"{title} ({address})",
                data={CONF_ADDRESS: address},
                options={CONF_POLLING_INTERVAL: user_input.get(CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL)},
            )

        # Find already discovered devices
        current_addresses = self._async_current_ids()
        for discovery_info in async_discovered_service_info(self.hass):
            address = discovery_info.address.upper()
            if address in current_addresses:
                continue
            if discovery_info.name and ("mclh" in discovery_info.name.lower() or "lifecontrol" in discovery_info.name.lower()):
                self._discovered_devices[address] = f"{discovery_info.name} ({address})"

        schema = {}
        if self._discovered_devices:
            schema[vol.Required(CONF_ADDRESS)] = SelectSelector(
                SelectSelectorConfig(
                    options=list(self._discovered_devices.keys()),
                    custom_value=True,
                )
            )
        else:
            schema[vol.Required(CONF_ADDRESS)] = cv.string

        schema[vol.Required(CONF_POLLING_INTERVAL, default=DEFAULT_POLLING_INTERVAL)] = vol.All(vol.Coerce(int), vol.Range(min=1))

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema),
            errors=errors,
        )


class MCLH09OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_POLLING_INTERVAL,
                        default=current_interval,
                    ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                }
            ),
        )
