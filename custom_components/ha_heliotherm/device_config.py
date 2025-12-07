"""Device configuration for Heliotherm integration."""

from dataclasses import dataclass
from typing import Optional

from .const import ATTR_MANUFACTURER, DOMAIN


@dataclass
class DeviceConfig:
    """Configuration for a device."""

    identifier: str
    name: str
    model: Optional[str] = None
    sw_version: Optional[str] = None


# Device definitions
DEVICES = {
    "main": DeviceConfig(
        identifier="main",
        name="Wärmepumpe",
        model="Heliotherm Heat Pump",
    ),
    "hkr": DeviceConfig(
        identifier="hkr",
        name="HKR (Hauptheizkreis)",
        model="Main Heating Circuit",
    ),
    "mkr1": DeviceConfig(
        identifier="mkr1",
        name="MKR1 (Mischkreis 1)",
        model="Mixing Circuit 1",
    ),
    "mkr2": DeviceConfig(
        identifier="mkr2",
        name="MKR2 (Mischkreis 2)",
        model="Mixing Circuit 2",
    ),
    "ww": DeviceConfig(
        identifier="ww",
        name="Warmwasser",
        model="Domestic Hot Water",
    ),
    "pumps": DeviceConfig(
        identifier="pumps",
        name="Pumpen",
        model="Pumps & Fan",
    ),
    "buffer": DeviceConfig(
        identifier="buffer",
        name="Pufferspeicher",
        model="Buffer Storage",
    ),
    "counters": DeviceConfig(
        identifier="counters",
        name="Zähler",
        model="Energy Counters",
    ),
    "solar": DeviceConfig(
        identifier="solar",
        name="Solar",
        model="Solar System",
    ),
    "advanced": DeviceConfig(
        identifier="advanced",
        name="Erweitert",
        model="Advanced Settings",
    ),
}


def get_device_info(hub_name: str, device_key: str) -> dict:
    """Get device info dictionary for a specific device."""
    if device_key not in DEVICES:
        device_key = "main"

    device = DEVICES[device_key]

    return {
        "identifiers": {(DOMAIN, f"{hub_name}_{device.identifier}")},
        "name": f"{hub_name} {device.name}",
        "manufacturer": ATTR_MANUFACTURER,
        "model": device.model,
        "via_device": (DOMAIN, hub_name) if device_key != "main" else None,
    }
