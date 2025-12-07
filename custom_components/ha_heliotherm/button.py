"""Button platform for Heliotherm integration."""

import logging
from typing import Optional

from homeassistant.components.button import ButtonEntity
from homeassistant.const import CONF_NAME
from homeassistant.core import callback

from .const import (
    DOMAIN,
    BUTTON_TYPES,
    HaHeliothermButtonEntityDescription,
)
from .device_config import get_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Heliotherm button entities."""
    hub_name = entry.data[CONF_NAME]
    hub = hass.data[DOMAIN][hub_name]["hub"]

    entities = []
    for button_description in BUTTON_TYPES.values():
        device_info = get_device_info(
            hub_name,
            getattr(button_description, 'device', 'main')
        )

        button = HaHeliothermModbusButton(
            hub_name,
            hub,
            device_info,
            button_description,
        )
        entities.append(button)

    async_add_entities(entities)
    return True


class HaHeliothermModbusButton(ButtonEntity):
    """Representation of a Heliotherm Modbus button entity."""

    def __init__(
        self,
        platform_name,
        hub,
        device_info,
        description: HaHeliothermButtonEntityDescription,
    ):
        """Initialize the button entity."""
        self._platform_name = platform_name
        self._attr_device_info = device_info
        self._hub = hub
        self.entity_description: HaHeliothermButtonEntityDescription = description

        # Set entity category if specified
        if hasattr(description, 'entity_category') and description.entity_category:
            self._attr_entity_category = description.entity_category

    @property
    def name(self):
        """Return the name."""
        return f"{self._platform_name} {self.entity_description.name}"

    @property
    def unique_id(self) -> Optional[str]:
        """Return unique ID."""
        return f"{self._platform_name}_{self.entity_description.key}"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._hub.button_press_callback(self)
