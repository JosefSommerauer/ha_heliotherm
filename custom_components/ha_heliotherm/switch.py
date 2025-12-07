"""Support for Heliotherm switch entities."""
from __future__ import annotations
from . import HaHeliothermModbusHub


from homeassistant.components.switch import SwitchEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.core import callback

from .const import *
from .device_config import get_device_info


async def async_setup_entry(hass, entry, async_add_entities):
    hub_name = entry.data[CONF_NAME]
    hub = hass.data[DOMAIN][hub_name]["hub"]

    entities = []
    for switch_description in SWITCH_TYPES.values():
        device_info = get_device_info(
            hub_name,
            getattr(switch_description, 'device', 'main')
        )

        switch = HaHeliothermModbusSwitch(
            hub_name,
            hub,
            device_info,
            switch_description,
        )
        entities.append(switch)

    async_add_entities(entities)
    return True


class HaHeliothermModbusSwitch(SwitchEntity):
    """Representation of a Heliotherm Modbus switch."""

    def __init__(
        self,
        platform_name,
        hub: HaHeliothermModbusHub,
        device_info,
        description: HaHeliothermSwitchEntityDescription,
    ):
        """Initialize the switch."""
        self._platform_name = platform_name
        self._attr_device_info = device_info
        self._hub = hub
        self.entity_description: HaHeliothermSwitchEntityDescription = description

        # Set entity category if specified
        if hasattr(description, 'entity_category') and description.entity_category:
            self._attr_entity_category = description.entity_category

    async def async_added_to_hass(self):
        """Register callbacks."""
        self._hub.async_add_haheliotherm_modbus_sensor(self._modbus_data_updated)

    async def async_will_remove_from_hass(self) -> None:
        """Remove callbacks."""
        self._hub.async_remove_haheliotherm_modbus_sensor(self._modbus_data_updated)

    @callback
    def _modbus_data_updated(self):
        """Update the state."""
        self.async_write_ha_state()

    @property
    def name(self):
        """Return the name."""
        return f"{self._platform_name} {self.entity_description.name}"

    @property
    def unique_id(self):
        """Return unique id."""
        return f"{self._platform_name}_{self.entity_description.key}"

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._hub.data.get(self.entity_description.key, False)

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self._hub.setter_function_callback(self, True)

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self._hub.setter_function_callback(self, False)