"""Button platform for LifeControl MCLH-09."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription, ButtonDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import MCLH09Coordinator

BUTTONS: tuple[ButtonEntityDescription, ...] = (
    ButtonEntityDescription(
        key="force_update",
        name="Force Update",
        icon="mdi:update",
    ),
    ButtonEntityDescription(
        key="calibrate_temp",
        name="Calibrate Temperature",
        icon="mdi:thermometer-alert",
    ),
    ButtonEntityDescription(
        key="calibrate_moisture",
        name="Calibrate Moisture/Light",
        icon="mdi:water-alert",
    ),
    ButtonEntityDescription(
        key="factory_reset",
        name="Factory Reset",
        device_class=ButtonDeviceClass.RESTART,
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the MCLH-09 buttons from a config entry."""
    coordinator: MCLH09Coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        MCLH09Button(coordinator, entry, description)
        for description in BUTTONS
    ]
    async_add_entities(entities)

class MCLH09Button(ButtonEntity):
    """Representation of an MCLH-09 button."""

    def __init__(
        self,
        coordinator: MCLH09Coordinator,
        entry: ConfigEntry,
        description: ButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        self.coordinator = coordinator
        self.entity_description = description

        address = entry.data[CONF_ADDRESS]

        self._attr_unique_id = f"{address}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            name=entry.title or f"LifeControl MCLH-09 ({address})",
            manufacturer="LifeControl",
            model="MCLH-09",
        )
        self._attr_has_entity_name = True

    async def async_press(self) -> None:
        """Handle the button press."""
        if self.entity_description.key == "force_update":
            await self.coordinator.async_request_refresh()
        elif self.entity_description.key == "calibrate_temp":
            await self.coordinator.async_send_command(b'\x01')
        elif self.entity_description.key == "calibrate_moisture":
            await self.coordinator.async_send_command(b'\x02')
        elif self.entity_description.key == "factory_reset":
            await self.coordinator.async_send_command(b'\x03')
