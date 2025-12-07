"""The HaHeliotherm integration."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
import threading
from typing import Optional

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException
import voluptuous as vol

from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    Platform,
)
from homeassistant.core import HomeAssistant, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_time_interval


from .const import DEFAULT_NAME, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

# PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SELECT]
PLATFORMS = [
    Platform.SELECT,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.BUTTON,
]


async def async_setup(hass, config):
    """Set up the HaHeliotherm modbus component."""
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up a HaHeliotherm modbus."""
    host = entry.data[CONF_HOST]
    name = entry.data[CONF_NAME]
    port = entry.data[CONF_PORT]
    scan_interval = DEFAULT_SCAN_INTERVAL

    _LOGGER.debug("Setup %s.%s", DOMAIN, name)

    hub = HaHeliothermModbusHub(hass, name, host, port, scan_interval)
    # """Register the hub."""
    hass.data[DOMAIN][name] = {"hub": hub}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass, entry):
    """Unload HaHeliotherm mobus entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if not unload_ok:
        return False

    hass.data[DOMAIN].pop(entry.data["name"])
    return True


class HaHeliothermModbusHub:
    """Thread safe wrapper class for pymodbus."""

    def __init__(
        self,
        hass: HomeAssistant,
        name,
        host,
        port,
        scan_interval,
    ):
        """Initialize the Modbus hub."""
        self._hass = hass
        self._client = ModbusTcpClient(host=host, port=port, timeout=3, retries=3)
        self._lock = threading.Lock()
        self._name = name
        self._scan_interval = timedelta(seconds=scan_interval)
        self._unsub_interval_method = None
        self._sensors = []
        self.data = {}

    @callback
    def async_add_haheliotherm_modbus_sensor(self, update_callback):
        """Listen for data updates."""
        # This is the first sensor, set up interval.
        if not self._sensors:
            self.connect()
            self._unsub_interval_method = async_track_time_interval(
                self._hass, self.async_refresh_modbus_data, self._scan_interval
            )

        self._sensors.append(update_callback)

    @callback
    def async_remove_haheliotherm_modbus_sensor(self, update_callback):
        """Remove data update."""
        self._sensors.remove(update_callback)

        if not self._sensors:
            # """stop the interval timer upon removal of last sensor"""
            self._unsub_interval_method()
            self._unsub_interval_method = None
            self.close()

    async def async_refresh_modbus_data(self, _now: Optional[int] = None) -> None:
        """Time to update."""
        if not self._sensors:
            return

        update_result = self.read_modbus_registers()

        if update_result:
            for update_callback in self._sensors:
                update_callback()

    @property
    def name(self):
        """Return the name of this hub."""
        return self._name

    def close(self):
        """Disconnect client."""
        with self._lock:
            self._client.close()

    def connect(self):
        """Connect client."""
        with self._lock:
            self._client.connect()

    def read_input_registers(self, slave, address, count):
        """Read holding registers."""
        with self._lock:
            return self._client.read_input_registers(address, count=count, device_id=slave)

    def getsignednumber(self, number, bitlength=16):
        mask = (2**bitlength) - 1
        if number & (1 << (bitlength - 1)):
            return number | ~mask
        else:
            return number & mask

    def checkval(self, value, scale, bitlength=16):
        """Check value for missing item"""
        if value is None:
            return None
        value = self.getsignednumber(value, bitlength)
        value = round(value * scale, 1)
        if value == -50.0:
            value = None
        return value

    def getbetriebsart(self, bietriebsart_nr: int):
        return (
            "Aus"
            if bietriebsart_nr == 0
            else "Auto"
            if bietriebsart_nr == 1
            else "Kühlen"
            if bietriebsart_nr == 2
            else "Sommer"
            if bietriebsart_nr == 3
            else "Dauerbetrieb"
            if bietriebsart_nr == 4
            else "Absenken"
            if bietriebsart_nr == 5
            else "Urlaub"
            if bietriebsart_nr == 6
            else "Party"
            if bietriebsart_nr == 7
            else None
        )

    def getbetriebsartnr(self, bietriebsart_str: str):
        return (
            0
            if bietriebsart_str == "Aus"
            else 1
            if bietriebsart_str == "Auto"
            else 2
            if bietriebsart_str == "Kühlen"
            else 3
            if bietriebsart_str == "Sommer"
            else 4
            if bietriebsart_str == "Dauerbetrieb"
            else 5
            if bietriebsart_str == "Absenken"
            else 6
            if bietriebsart_str == "Urlaub"
            else 7
            if bietriebsart_str == "Party"
            else None
        )

    async def setter_function_callback(self, entity: Entity, option):
        # Handle Select entities
        if entity.entity_description.key == "select_betriebsart":
            await self.set_betriebsart(option)
            return
        if entity.entity_description.key == "select_mkr1_betriebsart":
            await self.set_mkr1_betriebsart(option)
            return
        if entity.entity_description.key == "select_mkr2_betriebsart":
            await self.set_mkr2_betriebsart(option)
            return

        # Handle Climate entities
        if entity.entity_description.key == "climate_hkr_raum_soll":
            temp = float(option["temperature"])
            await self.set_raumtemperatur(temp)
            return

        if entity.entity_description.key == "climate_rlt_kuehlen":
            temp = float(option["temperature"])
            await self.set_rltkuehlen(temp)
            return

        if entity.entity_description.key == "climate_ww_bereitung":
            tmin = float(option["target_temp_low"])
            tmax = float(option["target_temp_high"])
            await self.set_ww_bereitung(tmin, tmax)
            return

        if entity.entity_description.key == "climate_rl_soll":
            temp = float(option["temperature"])
            await self.set_rl_soll(temp)
            return

        # Handle Switch entities
        if entity.entity_description.key == "climate_rl_soll_ovr":
            await self.set_rl_soll_ovr(option)
            return

        # Handle Number entities (Heizkurven)
        if entity.entity_description.key == "hkr_heizgrenze":
            await self.set_hkr_heizgrenze(option)
            return
        if entity.entity_description.key == "hkr_rlt_soll_ohg":
            await self.set_hkr_rlt_soll_ohg(option)
            return
        if entity.entity_description.key == "hkr_rlt_soll_0":
            await self.set_hkr_rlt_soll_0(option)
            return
        if entity.entity_description.key == "hkr_rlt_soll_uhg":
            await self.set_hkr_rlt_soll_uhg(option)
            return

        # Phase 2: WW Minimaltemp
        if entity.entity_description.key == "ww_minimaltemp":
            await self.set_ww_minimaltemp(option)
            return

        # Phase 2: Override Values
        if entity.entity_description.key == "aussentemp_override_wert":
            await self.set_aussentemp_override_wert(option)
            return
        if entity.entity_description.key == "puffer_override_wert":
            await self.set_puffer_override_wert(option)
            return
        if entity.entity_description.key == "brauchwasser_override_wert":
            await self.set_brauchwasser_override_wert(option)
            return

        # Phase 2: Override Switches
        if entity.entity_description.key == "aussentemp_override":
            await self.set_aussentemp_override(option)
            return
        if entity.entity_description.key == "puffer_override":
            await self.set_puffer_override(option)
            return
        if entity.entity_description.key == "brauchwasser_override":
            await self.set_brauchwasser_override(option)
            return

        # Phase 2: MKR Climate Entities
        if entity.entity_description.key == "climate_mkr1_raum_soll":
            temp = float(option["temperature"])
            await self.set_mkr1_raumtemperatur(temp)
            return
        if entity.entity_description.key == "climate_mkr1_rlt_kuehlen":
            temp = float(option["temperature"])
            await self.set_mkr1_rlt_kuehlen(temp)
            return
        if entity.entity_description.key == "climate_mkr2_raum_soll":
            temp = float(option["temperature"])
            await self.set_mkr2_raumtemperatur(temp)
            return
        if entity.entity_description.key == "climate_mkr2_rlt_kuehlen":
            temp = float(option["temperature"])
            await self.set_mkr2_rlt_kuehlen(temp)
            return

        # Phase 3: MKR1 Heizkurven
        if entity.entity_description.key == "mkr1_heizgrenze":
            await self.set_mkr1_heizgrenze(option)
            return
        if entity.entity_description.key == "mkr1_rlt_soll_ohg":
            await self.set_mkr1_rlt_soll_ohg(option)
            return
        if entity.entity_description.key == "mkr1_rlt_soll_0":
            await self.set_mkr1_rlt_soll_0(option)
            return
        if entity.entity_description.key == "mkr1_rlt_soll_uhg":
            await self.set_mkr1_rlt_soll_uhg(option)
            return

        # Phase 3: MKR2 Heizkurven
        if entity.entity_description.key == "mkr2_heizgrenze":
            await self.set_mkr2_heizgrenze(option)
            return
        if entity.entity_description.key == "mkr2_rlt_soll_ohg":
            await self.set_mkr2_rlt_soll_ohg(option)
            return
        if entity.entity_description.key == "mkr2_rlt_soll_0":
            await self.set_mkr2_rlt_soll_0(option)
            return
        if entity.entity_description.key == "mkr2_rlt_soll_uhg":
            await self.set_mkr2_rlt_soll_uhg(option)
            return

        # Phase 3: PV/SG Parameter
        if entity.entity_description.key == "pv_energie":
            await self.set_pv_energie(option)
            return
        if entity.entity_description.key == "ueberheizen_pv_sg":
            await self.set_ueberheizen_pv_sg(option)
            return
        if entity.entity_description.key == "unterkuehlen_pv_sg":
            await self.set_unterkuehlen_pv_sg(option)
            return

    async def set_betriebsart(self, betriebsart: str):
        betriebsart_nr = self.getbetriebsartnr(betriebsart)
        if betriebsart_nr is None:
            return
        self._client.write_register(address=100, value=betriebsart_nr, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_mkr1_betriebsart(self, betriebsart: str):
        betriebsart_nr = self.getbetriebsartnr(betriebsart)
        if betriebsart_nr is None:
            return
        self._client.write_register(address=107, value=betriebsart_nr, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_mkr2_betriebsart(self, betriebsart: str):
        betriebsart_nr = self.getbetriebsartnr(betriebsart)
        if betriebsart_nr is None:
            return
        self._client.write_register(address=112, value=betriebsart_nr, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_raumtemperatur(self, temperature: float):
        if temperature is None:
            return
        temp_int = int(temperature * 10)
        self._client.write_register(address=101, value=temp_int, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_rltkuehlen(self, temperature: float):
        if temperature is None:
            return
        temp_int = int(temperature * 10)
        self._client.write_register(address=104, value=temp_int, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_ww_bereitung(self, temp_min: float, temp_max: float):
        if temp_min is None or temp_max is None:
            return
        temp_max_int = int(temp_max * 10)
        temp_min_int = int(temp_min * 10)
        self._client.write_register(address=105, value=temp_max_int, device_id=1)
        self._client.write_register(address=106, value=temp_min_int, device_id=1)
        await self.async_refresh_modbus_data()

#---------------------eingefügt-------------------------------------------------
    async def set_rl_soll(self, temperature: float):
        """Set return temperature setpoint - only works if override is active."""
        if temperature is None:
            return

        # Check if override is active
        if not self.data.get("climate_rl_soll_ovr", False):
            error_msg = (
                "⚠️ Rücklauf-Sollwert kann nicht geändert werden!\n\n"
                "Der 'Rücklauf-Sollwert Override' Switch ist nicht aktiv. "
                "Bitte aktivieren Sie zuerst den Switch, um die manuelle Steuerung zu ermöglichen.\n\n"
                "**ACHTUNG:** Die manuelle Steuerung deaktiviert die automatische Regelung der Wärmepumpe!"
            )

            _LOGGER.warning(
                "Versuch die Rücklauf-Solltemperatur auf %.1f°C zu ändern, aber Override ist nicht aktiv.",
                temperature
            )

            # Create persistent notification
            await self._hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "⚠️ Rücklauf-Sollwert Override erforderlich",
                    "message": error_msg,
                    "notification_id": f"{DOMAIN}_rl_soll_override_warning",
                },
            )

            # Still raise error to prevent the write
            from homeassistant.exceptions import HomeAssistantError
            raise HomeAssistantError(
                "Rücklauf-Sollwert Override ist nicht aktiv. Bitte zuerst den Override-Switch aktivieren."
            )

        temp_int = int(temperature * 10)
        with self._lock:
            self._client.write_register(address=102, value=temp_int, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_rl_soll_ovr(self, active: bool):
        """Enable or disable manual override of return temperature setpoint."""
        value = 1 if active else 0
        with self._lock:
            self._client.write_register(address=103, value=value, device_id=1)

        # Clear warning notification when override is activated
        if active:
            try:
                await self._hass.services.async_call(
                    "persistent_notification",
                    "dismiss",
                    {"notification_id": f"{DOMAIN}_rl_soll_override_warning"},
                )
            except Exception:
                # Notification might not exist, ignore
                pass

        await self.async_refresh_modbus_data()

#---------------------eingefügt-------------------------------------------------

    # Phase 1: Button callbacks
    async def button_press_callback(self, entity: Entity):
        """Handle button press events."""
        if entity.entity_description.key == "button_entstoerung":
            await self.press_entstoerung()
            return

    async def press_entstoerung(self):
        """Press Entstörung button (fault reset)."""
        _LOGGER.info("Entstörung button pressed - resetting fault")
        with self._lock:
            # Write 1 to HR 128 to reset fault
            self._client.write_register(address=128, value=1, device_id=1)
        await self.async_refresh_modbus_data()

    # Phase 1: Setter für Heizkurven-Parameter
    async def set_hkr_heizgrenze(self, value: float):
        """Set HKR Heizgrenze (heating limit)."""
        if value is None:
            return
        value_int = int(value * 10)
        with self._lock:
            self._client.write_register(address=135, value=value_int, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_hkr_rlt_soll_ohg(self, value: float):
        """Set HKR RLT Soll oberhalb Heizgrenze."""
        if value is None:
            return
        value_int = int(value * 10)
        with self._lock:
            self._client.write_register(address=136, value=value_int, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_hkr_rlt_soll_0(self, value: float):
        """Set HKR RLT Soll bei 0°C."""
        if value is None:
            return
        value_int = int(value * 10)
        with self._lock:
            self._client.write_register(address=137, value=value_int, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_hkr_rlt_soll_uhg(self, value: float):
        """Set HKR RLT Soll unterhalb Heizgrenze."""
        if value is None:
            return
        value_int = int(value * 10)
        with self._lock:
            self._client.write_register(address=138, value=value_int, device_id=1)
        await self.async_refresh_modbus_data()

    # Phase 2: WW Minimaltemp
    async def set_ww_minimaltemp(self, value: float):
        """Set WW Minimaltemperatur."""
        if value is None:
            return
        value_int = int(value * 10)
        with self._lock:
            self._client.write_register(address=106, value=value_int, device_id=1)
        await self.async_refresh_modbus_data()

    # Phase 2: MKR Climate Setters
    async def set_mkr1_raumtemperatur(self, temperature: float):
        """Set MKR1 Raum Solltemperatur."""
        if temperature is None:
            return
        temp_int = int(temperature * 10)
        with self._lock:
            self._client.write_register(address=108, value=temp_int, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_mkr1_rlt_kuehlen(self, temperature: float):
        """Set MKR1 Kühlen RLT min."""
        if temperature is None:
            return
        temp_int = int(temperature * 10)
        with self._lock:
            self._client.write_register(address=111, value=temp_int, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_mkr2_raumtemperatur(self, temperature: float):
        """Set MKR2 Raum Solltemperatur."""
        if temperature is None:
            return
        temp_int = int(temperature * 10)
        with self._lock:
            self._client.write_register(address=113, value=temp_int, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_mkr2_rlt_kuehlen(self, temperature: float):
        """Set MKR2 Kühlen RLT min."""
        if temperature is None:
            return
        temp_int = int(temperature * 10)
        with self._lock:
            self._client.write_register(address=116, value=temp_int, device_id=1)
        await self.async_refresh_modbus_data()

    # Phase 2: Override Setters
    async def set_aussentemp_override_wert(self, value: float):
        """Set Außentemperatur Override Value."""
        if value is None:
            return
        value_int = int(value * 10)
        with self._lock:
            self._client.write_register(address=129, value=value_int, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_aussentemp_override(self, active: bool):
        """Enable or disable Außentemperatur Override."""
        value = 1 if active else 0
        with self._lock:
            self._client.write_register(address=130, value=value, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_puffer_override_wert(self, value: float):
        """Set Pufferspeicher Override Value."""
        if value is None:
            return
        value_int = int(value * 10)
        with self._lock:
            self._client.write_register(address=131, value=value_int, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_puffer_override(self, active: bool):
        """Enable or disable Pufferspeicher Override."""
        value = 1 if active else 0
        with self._lock:
            self._client.write_register(address=132, value=value, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_brauchwasser_override_wert(self, value: float):
        """Set Brauchwasser Override Value."""
        if value is None:
            return
        value_int = int(value * 10)
        with self._lock:
            self._client.write_register(address=133, value=value_int, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_brauchwasser_override(self, active: bool):
        """Enable or disable Brauchwasser Override."""
        value = 1 if active else 0
        with self._lock:
            self._client.write_register(address=134, value=value, device_id=1)
        await self.async_refresh_modbus_data()

    # Phase 3: MKR1 Heizkurven Setter
    async def set_mkr1_heizgrenze(self, value: float):
        """Set MKR1 Heizgrenze."""
        if value is None:
            return
        value_int = int(value * 10)
        with self._lock:
            self._client.write_register(address=139, value=value_int, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_mkr1_rlt_soll_ohg(self, value: float):
        """Set MKR1 RLT Soll oberhalb Heizgrenze."""
        if value is None:
            return
        value_int = int(value * 10)
        with self._lock:
            self._client.write_register(address=140, value=value_int, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_mkr1_rlt_soll_0(self, value: float):
        """Set MKR1 RLT Soll bei 0°C."""
        if value is None:
            return
        value_int = int(value * 10)
        with self._lock:
            self._client.write_register(address=141, value=value_int, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_mkr1_rlt_soll_uhg(self, value: float):
        """Set MKR1 RLT Soll unterhalb Heizgrenze."""
        if value is None:
            return
        value_int = int(value * 10)
        with self._lock:
            self._client.write_register(address=142, value=value_int, device_id=1)
        await self.async_refresh_modbus_data()

    # Phase 3: MKR2 Heizkurven Setter
    async def set_mkr2_heizgrenze(self, value: float):
        """Set MKR2 Heizgrenze."""
        if value is None:
            return
        value_int = int(value * 10)
        with self._lock:
            self._client.write_register(address=143, value=value_int, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_mkr2_rlt_soll_ohg(self, value: float):
        """Set MKR2 RLT Soll oberhalb Heizgrenze."""
        if value is None:
            return
        value_int = int(value * 10)
        with self._lock:
            self._client.write_register(address=144, value=value_int, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_mkr2_rlt_soll_0(self, value: float):
        """Set MKR2 RLT Soll bei 0°C."""
        if value is None:
            return
        value_int = int(value * 10)
        with self._lock:
            self._client.write_register(address=145, value=value_int, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_mkr2_rlt_soll_uhg(self, value: float):
        """Set MKR2 RLT Soll unterhalb Heizgrenze."""
        if value is None:
            return
        value_int = int(value * 10)
        with self._lock:
            self._client.write_register(address=146, value=value_int, device_id=1)
        await self.async_refresh_modbus_data()

    # Phase 3: PV/SG Parameter Setter
    async def set_pv_energie(self, value: float):
        """Set PV Energie (32-bit value)."""
        if value is None:
            return
        value_int = int(value)
        # Split into upper and lower 16-bit values
        value_upper = (value_int >> 16) & 0xFFFF
        value_lower = value_int & 0xFFFF
        with self._lock:
            self._client.write_register(address=117, value=value_upper, device_id=1)
            self._client.write_register(address=118, value=value_lower, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_ueberheizen_pv_sg(self, value: float):
        """Set Überhitzen bei PV/SG."""
        if value is None:
            return
        value_int = int(value * 10)
        with self._lock:
            self._client.write_register(address=122, value=value_int, device_id=1)
        await self.async_refresh_modbus_data()

    async def set_unterkuehlen_pv_sg(self, value: float):
        """Set Unterkühlen bei PV/SG."""
        if value is None:
            return
        value_int = int(value * 10)
        with self._lock:
            self._client.write_register(address=123, value=value_int, device_id=1)
        await self.async_refresh_modbus_data()

#---------------------eingefügt-------------------------------------------------

    def read_modbus_registers(self):
        """Read from modbus registers"""
        modbusdata = self.read_input_registers(slave=1, address=10, count=43)  # IR 10-52
        modbusdata2 = self.read_input_registers(slave=1, address=60, count=16)
        modbusdata3 = self._client.read_holding_registers(
            address=100, count=51, device_id=1  # HR 100-150
        )

        # if modbusdata.isError():
        #    return False

        temp_aussen = modbusdata.registers[0]
        self.data["temp_aussen"] = self.checkval(temp_aussen, 0.1)

        temp_brauchwasser = modbusdata.registers[1]
        self.data["temp_brauchwasser"] = self.checkval(temp_brauchwasser, 0.1)

        temp_vorlauf = modbusdata.registers[2]
        self.data["temp_vorlauf"] = self.checkval(temp_vorlauf, 0.1)

        temp_ruecklauf = modbusdata.registers[3]
        self.data["temp_ruecklauf"] = self.checkval(temp_ruecklauf, 0.1)

        temp_pufferspeicher = modbusdata.registers[4]
        self.data["temp_pufferspeicher"] = self.checkval(temp_pufferspeicher, 0.1)

        temp_eq_eintritt = modbusdata.registers[5]
        self.data["temp_eq_eintritt"] = self.checkval(temp_eq_eintritt, 0.1)

        temp_eq_austritt = modbusdata.registers[6]
        self.data["temp_eq_austritt"] = self.checkval(temp_eq_austritt, 0.1)

        temp_sauggas = modbusdata.registers[7]
        self.data["temp_sauggas"] = self.checkval(temp_sauggas, 0.1)

        temp_verdampfung = modbusdata.registers[8]
        self.data["temp_verdampfung"] = self.checkval(temp_verdampfung, 0.1)

        temp_kodensation = modbusdata.registers[9]
        self.data["temp_kodensation"] = self.checkval(temp_kodensation, 0.1)

        temp_heissgas = modbusdata.registers[10]
        self.data["temp_heissgas"] = self.checkval(temp_heissgas, 0.1)

        bar_niederdruck = modbusdata.registers[11]
        self.data["bar_niederdruck"] = self.checkval(bar_niederdruck, 0.1)

        bar_hochdruck = modbusdata.registers[12]
        self.data["bar_hochdruck"] = self.checkval(bar_hochdruck, 0.1)

        on_off_heizkreispumpe = modbusdata.registers[13]
        self.data["on_off_heizkreispumpe"] = (
            "off" if (on_off_heizkreispumpe == 0) else "on"
        )

        on_off_pufferladepumpe = modbusdata.registers[14]
        self.data["on_off_pufferladepumpe"] = (
            "off" if (on_off_pufferladepumpe == 0) else "on"
        )

        on_off_verdichter = modbusdata.registers[15]
        self.data["on_off_verdichter"] = "off" if (on_off_verdichter == 0) else "on"

        on_off_stoerung = modbusdata.registers[16]
        self.data["on_off_stoerung"] = "off" if (on_off_stoerung == 0) else "on"

        vierwegeventil_luft = modbusdata.registers[17]
        self.data["vierwegeventil_luft"] = (
            "Abtaubetrieb" if (vierwegeventil_luft != 0) else "Aus"
        )

        wmz_durchfluss = modbusdata.registers[18]
        self.data["wmz_durchfluss"] = self.checkval(wmz_durchfluss, 0.1)

        n_soll_verdichter = modbusdata.registers[19]
        self.data["n_soll_verdichter"] = self.checkval(n_soll_verdichter, 1)

        cop = modbusdata.registers[20]
        self.data["cop"] = self.checkval(cop, 0.1)

        temp_frischwasser = modbusdata.registers[21]
        self.data["temp_frischwasser"] = self.checkval(temp_frischwasser, 0.1)

        on_off_evu_sperre = modbusdata.registers[22]
        self.data["on_off_evu_sperre"] = "on" if (on_off_evu_sperre == 0) else "off"

        temp_aussen_verzoegert = modbusdata.registers[23]
        self.data["temp_aussen_verzoegert"] = self.checkval(temp_aussen_verzoegert, 0.1)

        hkr_solltemperatur = modbusdata.registers[24]
        self.data["hkr_solltemperatur"] = self.checkval(hkr_solltemperatur, 0.1)

        mkr1_solltemperatur = modbusdata.registers[25]
        self.data["mkr1_solltemperatur"] = self.checkval(mkr1_solltemperatur, 0.1)

        mkr2_solltemperatur = modbusdata.registers[26]
        self.data["mkr2_solltemperatur"] = self.checkval(mkr2_solltemperatur, 0.1)

        on_off_eq_ventilator = modbusdata.registers[27]
        self.data["on_off_eq_ventilator"] = (
            "off" if (on_off_eq_ventilator == 0) else "on"
        )

        ww_vorrang = modbusdata.registers[28]
        self.data["ww_vorrang"] = "off" if (ww_vorrang == 0) else "on"

        kuehlen_umv_passiv = modbusdata.registers[29]
        self.data["kuehlen_umv_passiv"] = "off" if (kuehlen_umv_passiv == 0) else "on"

        expansionsventil = modbusdata.registers[30]
        self.data["expansionsventil"] = self.checkval(expansionsventil, 0.1)

#---------------------geändert-------------------------------------------------
        verdichteranforderung = modbusdata.registers[31]
        self.data["verdichteranforderung"] = (
            "Kühlen"
            if (verdichteranforderung == 10)
            else "Heizen"
            if (verdichteranforderung == 20)
            else "Warmwasser"
            if (verdichteranforderung == 30)
            else "Externe Anforderung"
            if (verdichteranforderung == 40)
            else "Keine"
        )
#---------------------geändert-------------------------------------------------

        # Phase 1: Neue Input Register (IR 32-42)
        # IR 37: Energiequellen Pumpe
        on_off_eq_pumpe = modbusdata.registers[27]  # IR 37 = Index 27
        self.data["on_off_eq_pumpe"] = "off" if (on_off_eq_pumpe == 0) else "on"

        # IR 42-45: Betriebsstundenzähler (32-bit values)
        # IR 42-43: BSZ Verdichter WW
        bsz_ww_upper = modbusdata.registers[32]  # IR 42 = Index 32
        bsz_ww_lower = modbusdata.registers[33]  # IR 43 = Index 33
        bsz_verdichter_ww = (bsz_ww_upper << 16) | bsz_ww_lower
        self.data["bsz_verdichter_ww"] = bsz_verdichter_ww

        # IR 44-45: BSZ Verdichter HKR
        bsz_hkr_upper = modbusdata.registers[34]  # IR 44 = Index 34
        bsz_hkr_lower = modbusdata.registers[35]  # IR 45 = Index 35
        bsz_verdichter_hkr = (bsz_hkr_upper << 16) | bsz_hkr_lower
        self.data["bsz_verdichter_hkr"] = bsz_verdichter_hkr

        # IR 46-49: MKR1/MKR2 Vor-/Rücklauftemperaturen
        mkr1_temp_vorlauf = modbusdata.registers[36]  # IR 46 = Index 36
        self.data["mkr1_temp_vorlauf"] = self.checkval(mkr1_temp_vorlauf, 0.1)

        mkr1_temp_ruecklauf = modbusdata.registers[37]  # IR 47 = Index 37
        self.data["mkr1_temp_ruecklauf"] = self.checkval(mkr1_temp_ruecklauf, 0.1)

        mkr2_temp_vorlauf = modbusdata.registers[38]  # IR 48 = Index 38
        self.data["mkr2_temp_vorlauf"] = self.checkval(mkr2_temp_vorlauf, 0.1)

        mkr2_temp_ruecklauf = modbusdata.registers[39]  # IR 49 = Index 39
        self.data["mkr2_temp_ruecklauf"] = self.checkval(mkr2_temp_ruecklauf, 0.1)

        # IR 50: Raum 1 Temperatur
        temp_raum1 = modbusdata.registers[40]  # IR 50 = Index 40
        self.data["temp_raum1"] = self.checkval(temp_raum1, 0.1)

        # -----------------------------------------------------------------------------------
        # decoder = BinaryPayloadDecoder.fromRegisters(
        #    modbusdata2.registers, byteorder=ENDIAN.BIG
        # )
        decoder = self._client.convert_from_registers(
            modbusdata2.registers,
            data_type=self._client.DATATYPE.UINT32,
        )

        wmz_heizung = decoder[0]
        self.data["wmz_heizung"] = wmz_heizung

        stromz_heizung = decoder[1]
        self.data["stromz_heizung"] = stromz_heizung

        wmz_brauchwasser = decoder[2]
        self.data["wmz_brauchwasser"] = wmz_brauchwasser

        stromz_brauchwasser = decoder[3]
        self.data["stromz_brauchwasser"] = stromz_brauchwasser

        stromz_gesamt = decoder[4]
        self.data["stromz_gesamt"] = stromz_gesamt

        stromz_leistung = decoder[5]
        self.data["stromz_leistung"] = stromz_leistung

        wmz_gesamt = decoder[6]
        self.data["wmz_gesamt"] = wmz_gesamt

        wmz_leistung = decoder[7] * 0.1
        self.data["wmz_leistung"] = wmz_leistung

        # -----------------------------------------------------------------------------------

        select_betriebsart = modbusdata3.registers[0]
        self.data["select_betriebsart"] = self.getbetriebsart(select_betriebsart)

        select_mkr1_betriebsart = modbusdata3.registers[7]
        self.data["select_mkr1_betriebsart"] = self.getbetriebsart(
            select_mkr1_betriebsart
        )

        select_mkr2_betriebsart = modbusdata3.registers[12]
        self.data["select_mkr2_betriebsart"] = self.getbetriebsart(
            select_mkr2_betriebsart
        )

        climate_hkr_raum_soll = modbusdata3.registers[1]
        self.data["climate_hkr_raum_soll"] = {
            "temperature": self.checkval(climate_hkr_raum_soll, 0.1)
        }

        climate_rlt_kuehlen = modbusdata3.registers[4]
        self.data["climate_rlt_kuehlen"] = {
            "temperature": self.checkval(climate_rlt_kuehlen, 0.1)
        }

        climate_ww_bereitung_max = modbusdata3.registers[5]
        climate_ww_bereitung_min = modbusdata3.registers[6]
        self.data["climate_ww_bereitung"] = {
            "target_temp_low": self.checkval(climate_ww_bereitung_min, 0.1),
            "target_temp_high": self.checkval(climate_ww_bereitung_max, 0.1),
            "temperature": self.checkval(temp_brauchwasser, 0.1),
        }

        # manual overwrite of flow return temp. is only possible if overwrite flag is set
        # caution: overwritting the flow return temperure disables the automatic controle loop

        climate_rl_soll = modbusdata3.registers[2]
        self.data["climate_rl_soll"] = {
            "temperature": self.checkval(climate_rl_soll, 0.1)
        }

        climate_rl_soll_ovr = modbusdata3.registers[3]
        self.data["climate_rl_soll_ovr"] = bool(climate_rl_soll_ovr)

        # Phase 1: Neue Holding Register
        # HR 135-138: HKR Heizkurven (HR 100 + offset)
        hkr_heizgrenze = modbusdata3.registers[35]  # HR 135 = Index 35
        self.data["hkr_heizgrenze"] = self.checkval(hkr_heizgrenze, 0.1)

        hkr_rlt_soll_ohg = modbusdata3.registers[36]  # HR 136 = Index 36
        self.data["hkr_rlt_soll_ohg"] = self.checkval(hkr_rlt_soll_ohg, 0.1)

        hkr_rlt_soll_0 = modbusdata3.registers[37]  # HR 137 = Index 37
        self.data["hkr_rlt_soll_0"] = self.checkval(hkr_rlt_soll_0, 0.1)

        hkr_rlt_soll_uhg = modbusdata3.registers[38]  # HR 138 = Index 38
        self.data["hkr_rlt_soll_uhg"] = self.checkval(hkr_rlt_soll_uhg, 0.1)

        # Phase 2: WW Minimaltemp, MKR Climate, Override
        # Note: HR 106 is already read above as climate_ww_bereitung_min
        # We use it for ww_minimaltemp
        self.data["ww_minimaltemp"] = self.checkval(climate_ww_bereitung_min, 0.1)

        # HR 108: MKR1 Raum Soll
        climate_mkr1_raum_soll = modbusdata3.registers[8]  # HR 108 = Index 8
        self.data["climate_mkr1_raum_soll"] = {
            "temperature": self.checkval(climate_mkr1_raum_soll, 0.1)
        }

        # HR 111: MKR1 Kühlen RLT min
        climate_mkr1_rlt_kuehlen = modbusdata3.registers[11]  # HR 111 = Index 11
        self.data["climate_mkr1_rlt_kuehlen"] = {
            "temperature": self.checkval(climate_mkr1_rlt_kuehlen, 0.1)
        }

        # HR 113: MKR2 Raum Soll
        climate_mkr2_raum_soll = modbusdata3.registers[13]  # HR 113 = Index 13
        self.data["climate_mkr2_raum_soll"] = {
            "temperature": self.checkval(climate_mkr2_raum_soll, 0.1)
        }

        # HR 116: MKR2 Kühlen RLT min
        climate_mkr2_rlt_kuehlen = modbusdata3.registers[16]  # HR 116 = Index 16
        self.data["climate_mkr2_rlt_kuehlen"] = {
            "temperature": self.checkval(climate_mkr2_rlt_kuehlen, 0.1)
        }

        # HR 129-134: Override Values and Flags
        # HR 129-130: Außentemperatur Override
        aussentemp_override_wert = modbusdata3.registers[29]  # HR 129 = Index 29
        self.data["aussentemp_override_wert"] = self.checkval(aussentemp_override_wert, 0.1)

        aussentemp_override = modbusdata3.registers[30]  # HR 130 = Index 30
        self.data["aussentemp_override"] = bool(aussentemp_override)

        # HR 131-132: Pufferspeicher Override
        puffer_override_wert = modbusdata3.registers[31]  # HR 131 = Index 31
        self.data["puffer_override_wert"] = self.checkval(puffer_override_wert, 0.1)

        puffer_override = modbusdata3.registers[32]  # HR 132 = Index 32
        self.data["puffer_override"] = bool(puffer_override)

        # HR 133-134: Brauchwasser Override
        brauchwasser_override_wert = modbusdata3.registers[33]  # HR 133 = Index 33
        self.data["brauchwasser_override_wert"] = self.checkval(brauchwasser_override_wert, 0.1)

        brauchwasser_override = modbusdata3.registers[34]  # HR 134 = Index 34
        self.data["brauchwasser_override"] = bool(brauchwasser_override)

        # Phase 3: Solar & Durchfluss (IR 51-52)
        # IR 51: Solar KT1
        solar_kt1 = modbusdata.registers[41]  # IR 51 = Index 41
        self.data["solar_kt1"] = self.checkval(solar_kt1, 0.1)

        # IR 52: Durchfluss primär
        durchfluss_primaer = modbusdata.registers[42]  # IR 52 = Index 42
        self.data["durchfluss_primaer"] = self.checkval(durchfluss_primaer, 0.1)

        # Phase 3: PV/SG Parameter (HR 117-123)
        # HR 117-118: PV Energie (32-bit)
        pv_energie_upper = modbusdata3.registers[17]  # HR 117 = Index 17
        pv_energie_lower = modbusdata3.registers[18]  # HR 118 = Index 18
        pv_energie = (pv_energie_upper << 16) | pv_energie_lower
        self.data["pv_energie"] = pv_energie

        # HR 122: Überhitzen bei PV/SG
        ueberheizen_pv_sg = modbusdata3.registers[22]  # HR 122 = Index 22
        self.data["ueberheizen_pv_sg"] = self.checkval(ueberheizen_pv_sg, 0.1)

        # HR 123: Unterkühlen bei PV/SG
        unterkuehlen_pv_sg = modbusdata3.registers[23]  # HR 123 = Index 23
        self.data["unterkuehlen_pv_sg"] = self.checkval(unterkuehlen_pv_sg, 0.1)

        # Phase 3: MKR1/MKR2 Heizkurven (HR 139-146)
        # MKR1: HR 139-142
        mkr1_heizgrenze = modbusdata3.registers[39]  # HR 139 = Index 39
        self.data["mkr1_heizgrenze"] = self.checkval(mkr1_heizgrenze, 0.1)

        mkr1_rlt_soll_ohg = modbusdata3.registers[40]  # HR 140 = Index 40
        self.data["mkr1_rlt_soll_ohg"] = self.checkval(mkr1_rlt_soll_ohg, 0.1)

        mkr1_rlt_soll_0 = modbusdata3.registers[41]  # HR 141 = Index 41
        self.data["mkr1_rlt_soll_0"] = self.checkval(mkr1_rlt_soll_0, 0.1)

        mkr1_rlt_soll_uhg = modbusdata3.registers[42]  # HR 142 = Index 42
        self.data["mkr1_rlt_soll_uhg"] = self.checkval(mkr1_rlt_soll_uhg, 0.1)

        # MKR2: HR 143-146
        mkr2_heizgrenze = modbusdata3.registers[43]  # HR 143 = Index 43
        self.data["mkr2_heizgrenze"] = self.checkval(mkr2_heizgrenze, 0.1)

        mkr2_rlt_soll_ohg = modbusdata3.registers[44]  # HR 144 = Index 44
        self.data["mkr2_rlt_soll_ohg"] = self.checkval(mkr2_rlt_soll_ohg, 0.1)

        mkr2_rlt_soll_0 = modbusdata3.registers[45]  # HR 145 = Index 45
        self.data["mkr2_rlt_soll_0"] = self.checkval(mkr2_rlt_soll_0, 0.1)

        mkr2_rlt_soll_uhg = modbusdata3.registers[46]  # HR 146 = Index 46
        self.data["mkr2_rlt_soll_uhg"] = self.checkval(mkr2_rlt_soll_uhg, 0.1)

        return True
