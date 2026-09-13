"""Coordinator for the LifeControl MCLH-09 integration."""
from __future__ import annotations

import asyncio
import logging
import struct
from datetime import timedelta

from bleak import BleakClient
from bleak.exc import BleakError

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    DATA_CHAR_UUID,
    BATTERY_CHAR_UUID,
    UPDATE_INTERVAL,
    TEMPERATURE_VALUES,
    TEMPERATURE_READINGS,
    MOISTURE_VALUES,
    MOISTURE_READINGS,
    LIGHT_VALUES,
    LIGHT_READINGS,
)

_LOGGER = logging.getLogger(__name__)

def interpolate(raw_value: float, values: list[float], raw_values: list[float]) -> float:
    """Non-linear interpolation logic to convert raw data to human-readable values."""
    index = 0
    if raw_value > raw_values[0]:
        index = 0
    elif raw_value < raw_values[-2]:
        index = len(raw_values) - 2
    else:
        while raw_value < raw_values[index + 1]:
            index += 1

    delta_value = values[index] - values[index + 1]
    delta_raw = raw_values[index] - raw_values[index + 1]

    # Avoid division by zero
    if delta_raw == 0:
        return values[index + 1]

    return ((raw_value - raw_values[index + 1]) * delta_value / delta_raw + values[index + 1])

class MCLH09Coordinator(DataUpdateCoordinator[dict[str, float]]):
    """Class to manage fetching data from the MCLH-09 BLE device."""

    def __init__(self, hass: HomeAssistant, address: str) -> None:
        """Initialize the coordinator."""
        self.address = address
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{address}",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, float]:
        """Fetch data from the BLE device."""
        ble_device = bluetooth.async_ble_device_from_address(self.hass, self.address, connectable=True)
        if not ble_device:
            raise UpdateFailed(f"Could not find BLE device with address {self.address}")

        client = BleakClient(ble_device)
        try:
            async with asyncio.timeout(30):
                await client.connect()

                # Read Data Characteristic
                data_bytes = await client.read_gatt_char(DATA_CHAR_UUID)

                # Read Battery Characteristic
                battery_bytes = await client.read_gatt_char(BATTERY_CHAR_UUID)

        except (BleakError, asyncio.TimeoutError) as err:
            raise UpdateFailed(f"Error communicating with device {self.address}: {err}") from err
        finally:
            if client.is_connected:
                await client.disconnect()

        # Parse data
        if len(data_bytes) < 8:
            raise UpdateFailed(f"Invalid data length received: {len(data_bytes)}")

        # Unpack format: <HxxHH (temp_raw, moisture_raw, illuminance_raw)
        # Note: H is 2 bytes, x is 1 byte of padding
        try:
            temp_raw, moisture_raw, illuminance_raw = struct.unpack("<HxxHH", data_bytes[:8])
        except struct.error as err:
            raise UpdateFailed(f"Failed to unpack data: {err}") from err

        # Parse battery (usually 1 byte for percentage)
        battery_level = 0
        if len(battery_bytes) >= 1:
            battery_level = int(battery_bytes[0])

        # Apply interpolation
        temperature = interpolate(temp_raw, TEMPERATURE_VALUES, TEMPERATURE_READINGS)
        moisture = interpolate(moisture_raw, MOISTURE_VALUES, MOISTURE_READINGS)
        illuminance = interpolate(illuminance_raw, LIGHT_VALUES, LIGHT_READINGS)

        data = {
            "temperature": round(temperature, 1),
            "moisture": round(moisture, 1),
            "illuminance": round(illuminance, 1),
            "battery": battery_level,
        }

        _LOGGER.debug("Parsed data for %s: %s", self.address, data)
        return data
