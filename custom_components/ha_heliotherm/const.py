"""Constants for the HaHeliotherm integration."""

from dataclasses import dataclass
from homeassistant.components.climate import (
    ClimateEntityDescription,
    ClimateEntityFeature,
)

from homeassistant.components.sensor import *

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberDeviceClass,
)
from homeassistant.const import UnitOfPressure, UnitOfTemperature, CONF_NAME

# from homeassistant.const import *

DOMAIN = "ha_heliotherm"
DEFAULT_NAME = "Heliotherm Heatpump"
DEFAULT_SCAN_INTERVAL = 15
DEFAULT_PORT = 502
CONF_HALEIOTHERM_HUB = "haheliotherm_hub"
ATTR_MANUFACTURER = "Heliotherm"


@dataclass
class HaHeliothermNumberEntityDescription(NumberEntityDescription):
    """A class that describes HaHeliotherm Modbus number entities."""

    mode: str = "slider"
    initial: float = None
    editable: bool = True
    device: str = "main"


@dataclass
class HaHeliothermSensorEntityDescription(SensorEntityDescription):
    """A class that describes HaHeliotherm Modbus sensor entities."""

    device: str = "main"


@dataclass
class HaHeliothermBinarySensorEntityDescription(BinarySensorEntityDescription):
    """A class that describes HaHeliotherm Modbus binarysensor entities."""

    device: str = "main"


@dataclass
class HaHeliothermSelectEntityDescription(SensorEntityDescription):
    """A class that describes HaHeliotherm Modbus select entities."""

    select_options: list[str] = None
    default_select_option: str = None
    setter_function = None
    device: str = "main"


@dataclass
class HaHeliothermClimateEntityDescription(ClimateEntityDescription):
    """A class that describes HaHeliotherm Modbus climate entities."""

    min_value: float = None
    max_value: float = None
    step: float = None
    hvac_modes: list[str] = None
    temperature_unit: str = "°C"
    supported_features: ClimateEntityFeature = ClimateEntityFeature.TARGET_TEMPERATURE
    device: str = "main"


@dataclass
class HaHeliothermSwitchEntityDescription(SensorEntityDescription):
    """A class that describes HaHeliotherm Modbus switch entities."""

    device: str = "main"


@dataclass
class HaHeliothermButtonEntityDescription(SensorEntityDescription):
    """A class that describes HaHeliotherm Modbus button entities."""

    device: str = "main"


CLIMATE_TYPES: dict[str, list[HaHeliothermClimateEntityDescription]] = {
    "climate_hkr_raum_soll": HaHeliothermClimateEntityDescription(
        name="Raum Solltemperatur",
        key="climate_hkr_raum_soll",
        min_value=10,
        max_value=25,
        step=0.5,
        temperature_unit="°C",
    ),
    "climate_rlt_kuehlen": HaHeliothermClimateEntityDescription(
        name="Kühlen RLT Soll",
        key="climate_rlt_kuehlen",
        min_value=15,
        max_value=25,
        step=1,
        temperature_unit="°C",
    ),
    "climate_ww_bereitung": HaHeliothermClimateEntityDescription(
        name="Warmwasserbereitung",
        key="climate_ww_bereitung",
        min_value=5,
        max_value=65,
        step=0.5,
        temperature_unit="°C",
        supported_features=ClimateEntityFeature.TARGET_TEMPERATURE_RANGE,
    ),

#---------------------eingefügt-------------------------------------------------
    "climate_rl_soll": HaHeliothermClimateEntityDescription(
        name="Rücklaufsolltemperatur",
        key="climate_rl_soll",
        min_value=5,
        max_value=65,
        step=0.5,
        temperature_unit="°C",
        supported_features=ClimateEntityFeature.TARGET_TEMPERATURE
        #----hier keine Range, sondern fester Wert-------
    ),
#---------------------eingefügt-------------------------------------------------
    # Phase 2: MKR Climate Entities
    "climate_mkr1_raum_soll": HaHeliothermClimateEntityDescription(
        name="MKR1 Raum Solltemperatur",
        key="climate_mkr1_raum_soll",
        min_value=10,
        max_value=25,
        step=0.5,
        temperature_unit="°C",
        device="mkr1",
    ),
    "climate_mkr1_rlt_kuehlen": HaHeliothermClimateEntityDescription(
        name="MKR1 Kühlen RLT",
        key="climate_mkr1_rlt_kuehlen",
        min_value=15,
        max_value=25,
        step=0.5,
        temperature_unit="°C",
        device="mkr1",
    ),
    "climate_mkr2_raum_soll": HaHeliothermClimateEntityDescription(
        name="MKR2 Raum Solltemperatur",
        key="climate_mkr2_raum_soll",
        min_value=10,
        max_value=25,
        step=0.5,
        temperature_unit="°C",
        device="mkr2",
    ),
    "climate_mkr2_rlt_kuehlen": HaHeliothermClimateEntityDescription(
        name="MKR2 Kühlen RLT",
        key="climate_mkr2_rlt_kuehlen",
        min_value=15,
        max_value=25,
        step=0.5,
        temperature_unit="°C",
        device="mkr2",
    ),

}

NUMBER_TYPES: dict[str, list[HaHeliothermNumberEntityDescription]] = {
    # Phase 1: HKR Heizkurven
    "hkr_heizgrenze": HaHeliothermNumberEntityDescription(
        name="HKR Heizgrenze",
        key="hkr_heizgrenze",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=-10,
        native_max_value=30,
        native_step=0.5,
        mode="slider",
        device="hkr",
    ),
    "hkr_rlt_soll_ohg": HaHeliothermNumberEntityDescription(
        name="HKR RLT Soll oHG",
        key="hkr_rlt_soll_ohg",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=20,
        native_max_value=65,
        native_step=0.5,
        mode="slider",
        device="hkr",
    ),
    "hkr_rlt_soll_0": HaHeliothermNumberEntityDescription(
        name="HKR RLT Soll 0°C",
        key="hkr_rlt_soll_0",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=20,
        native_max_value=65,
        native_step=0.5,
        mode="slider",
        device="hkr",
    ),
    "hkr_rlt_soll_uhg": HaHeliothermNumberEntityDescription(
        name="HKR RLT Soll uHG",
        key="hkr_rlt_soll_uhg",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=20,
        native_max_value=65,
        native_step=0.5,
        mode="slider",
        device="hkr",
    ),
    # Phase 2: WW Minimaltemp
    "ww_minimaltemp": HaHeliothermNumberEntityDescription(
        name="WW Minimaltemp",
        key="ww_minimaltemp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=5,
        native_max_value=65,
        native_step=0.5,
        mode="slider",
        device="ww",
    ),
    # Phase 2: Override Values (entity_category=CONFIG)
    "aussentemp_override_wert": HaHeliothermNumberEntityDescription(
        name="Außentemp Override Wert",
        key="aussentemp_override_wert",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=-30,
        native_max_value=50,
        native_step=0.5,
        mode="box",
        device="main",
        #entity_category="config",
    ),
    "puffer_override_wert": HaHeliothermNumberEntityDescription(
        name="Pufferspeicher Override Wert",
        key="puffer_override_wert",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=5,
        native_max_value=80,
        native_step=0.5,
        mode="box",
        device="buffer",
        #entity_category="config",
    ),
    "brauchwasser_override_wert": HaHeliothermNumberEntityDescription(
        name="Brauchwasser Override Wert",
        key="brauchwasser_override_wert",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=5,
        native_max_value=80,
        native_step=0.5,
        mode="box",
        device="ww",
        #entity_category="config",
    ),
    # Phase 3: MKR1 Heizkurven
    "mkr1_heizgrenze": HaHeliothermNumberEntityDescription(
        name="MKR1 Heizgrenze",
        key="mkr1_heizgrenze",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=-10,
        native_max_value=30,
        native_step=0.5,
        mode="slider",
        device="mkr1",
    ),
    "mkr1_rlt_soll_ohg": HaHeliothermNumberEntityDescription(
        name="MKR1 RLT Soll oHG",
        key="mkr1_rlt_soll_ohg",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=20,
        native_max_value=65,
        native_step=0.5,
        mode="slider",
        device="mkr1",
    ),
    "mkr1_rlt_soll_0": HaHeliothermNumberEntityDescription(
        name="MKR1 RLT Soll 0°C",
        key="mkr1_rlt_soll_0",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=20,
        native_max_value=65,
        native_step=0.5,
        mode="slider",
        device="mkr1",
    ),
    "mkr1_rlt_soll_uhg": HaHeliothermNumberEntityDescription(
        name="MKR1 RLT Soll uHG",
        key="mkr1_rlt_soll_uhg",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=20,
        native_max_value=65,
        native_step=0.5,
        mode="slider",
        device="mkr1",
    ),
    # Phase 3: MKR2 Heizkurven
    "mkr2_heizgrenze": HaHeliothermNumberEntityDescription(
        name="MKR2 Heizgrenze",
        key="mkr2_heizgrenze",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=-10,
        native_max_value=30,
        native_step=0.5,
        mode="slider",
        device="mkr2",
    ),
    "mkr2_rlt_soll_ohg": HaHeliothermNumberEntityDescription(
        name="MKR2 RLT Soll oHG",
        key="mkr2_rlt_soll_ohg",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=20,
        native_max_value=65,
        native_step=0.5,
        mode="slider",
        device="mkr2",
    ),
    "mkr2_rlt_soll_0": HaHeliothermNumberEntityDescription(
        name="MKR2 RLT Soll 0°C",
        key="mkr2_rlt_soll_0",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=20,
        native_max_value=65,
        native_step=0.5,
        mode="slider",
        device="mkr2",
    ),
    "mkr2_rlt_soll_uhg": HaHeliothermNumberEntityDescription(
        name="MKR2 RLT Soll uHG",
        key="mkr2_rlt_soll_uhg",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=20,
        native_max_value=65,
        native_step=0.5,
        mode="slider",
        device="mkr2",
    ),
    # Phase 3: PV/SG Parameter (entity_category=CONFIG)
    "pv_energie": HaHeliothermNumberEntityDescription(
        name="PV Energie",
        key="pv_energie",
        native_unit_of_measurement="W",
        device_class=NumberDeviceClass.POWER,
        native_min_value=0,
        native_max_value=10000,
        native_step=100,
        mode="box",
        device="solar",
        #entity_category="config",
    ),
    "ueberheizen_pv_sg": HaHeliothermNumberEntityDescription(
        name="Überheizen bei PV/SG",
        key="ueberheizen_pv_sg",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=0,
        native_max_value=10,
        native_step=0.5,
        mode="slider",
        device="solar",
        #entity_category="config",
    ),
    "unterkuehlen_pv_sg": HaHeliothermNumberEntityDescription(
        name="Unterkühlen bei PV/SG",
        key="unterkuehlen_pv_sg",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=0,
        native_max_value=10,
        native_step=0.5,
        mode="slider",
        device="solar",
        #entity_category="config",
    ),
}

SELECT_TYPES: dict[str, list[HaHeliothermSelectEntityDescription]] = {
    "select_betriebsart": HaHeliothermSelectEntityDescription(
        name="Betriebsart",
        key="select_betriebsart",
        select_options=[
            "Aus",
            "Auto",
            "Kühlen",
            "Sommer",
            "Dauerbetrieb",
            "Absenken",
            "Urlaub",
            "Party",
        ],
        default_select_option="Auto",
    ),
    "select_mkr1_betriebsart": HaHeliothermSelectEntityDescription(
        name="MKR 1 Betriebsart",
        key="select_mkr1_betriebsart",
        select_options=[
            "Aus",
            "Auto",
            "Kühlen",
            "Sommer",
            "Dauerbetrieb",
            "Absenken",
            "Urlaub",
            "Party",
        ],
        default_select_option="Auto",
    ),
    "select_mkr2_betriebsart": HaHeliothermSelectEntityDescription(
        name="MKR 2 Betriebsart",
        key="select_mkr2_betriebsart",
        select_options=[
            "Aus",
            "Auto",
            "Kühlen",
            "Sommer",
            "Dauerbetrieb",
            "Absenken",
            "Urlaub",
            "Party",
        ],
        default_select_option="Auto",
    ),
}

SENSOR_TYPES: dict[str, list[HaHeliothermSensorEntityDescription]] = {
    "temp_aussen": HaHeliothermSensorEntityDescription(
        name="Außentemperautr",
        key="temp_aussen",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        device="main",
    ),
    "temp_brauchwasser": HaHeliothermSensorEntityDescription(
        name="Brauchwasser Temperatur",
        key="temp_brauchwasser",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        device="ww",
    ),
    "temp_vorlauf": HaHeliothermSensorEntityDescription(
        name="Vorlauf Temperatur",
        key="temp_vorlauf",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    "temp_ruecklauf": HaHeliothermSensorEntityDescription(
        name="Rücklauf Temperatur",
        key="temp_ruecklauf",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    "temp_pufferspeicher": HaHeliothermSensorEntityDescription(
        name="Pufferspeicher Temperatur",
        key="temp_pufferspeicher",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        device="buffer",
    ),
    "temp_eq_eintritt": HaHeliothermSensorEntityDescription(
        name="Energiequellen Eintrittstemperatur",
        key="temp_eq_eintritt",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    "temp_eq_austritt": HaHeliothermSensorEntityDescription(
        name="Energiequellen Austrittstemperatur",
        key="temp_eq_austritt",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    "temp_sauggas": HaHeliothermSensorEntityDescription(
        name="Sauggas Temperatur",
        key="temp_sauggas",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    "temp_verdampfung": HaHeliothermSensorEntityDescription(
        name="Verdampfungs Temperatur",
        key="temp_verdampfung",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    "temp_kodensation": HaHeliothermSensorEntityDescription(
        name="Kondensations Temperatur",
        key="temp_kodensation",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    "temp_heissgas": HaHeliothermSensorEntityDescription(
        name="Heissgas Temperatur",
        key="temp_heissgas",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    "bar_niederdruck": HaHeliothermSensorEntityDescription(
        name="Niederdruck (bar)",
        key="bar_niederdruck",
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
    ),
    "bar_hochdruck": HaHeliothermSensorEntityDescription(
        name="Hochdruck (bar)",
        key="bar_hochdruck",
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
    ),
    "vierwegeventil_luft": HaHeliothermSensorEntityDescription(
        name="Vierwegeventil Luft",
        key="vierwegeventil_luft",
        device="main",
    ),
    "wmz_durchfluss": HaHeliothermSensorEntityDescription(
        name="Wärmemengerzähler Durchfluss",
        key="wmz_durchfluss",
        native_unit_of_measurement="l/min",
        device="counters",
    ),
    "n_soll_verdichter": HaHeliothermSensorEntityDescription(
        name="Verdichter Drehzahl Soll",
        key="n_soll_verdichter",
        native_unit_of_measurement="‰",
        device="main",
    ),
    "cop": HaHeliothermSensorEntityDescription(
        name="COP",
        key="cop",
        native_unit_of_measurement="",
        device="main",
    ),
    "temp_frischwasser": HaHeliothermSensorEntityDescription(
        name="Frischwasser Temperatur",
        key="temp_frischwasser",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        device="ww",
    ),
    "temp_aussen_verzoegert": HaHeliothermSensorEntityDescription(
        name="Außentempeatur verzögert",
        key="temp_aussen_verzoegert",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        device="main",
    ),
    "hkr_solltemperatur": HaHeliothermSensorEntityDescription(
        name="Heizkreis Soll Temperatur",
        key="hkr_solltemperatur",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        device="hkr",
    ),
    "mkr1_solltemperatur": HaHeliothermSensorEntityDescription(
        name="Mischerkreis 1 Soll Temperatur",
        key="mkr1_solltemperatur",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        device="mkr1",
    ),
    "mkr2_solltemperatur": HaHeliothermSensorEntityDescription(
        name="Mischerkreis 2 Soll Temperatur",
        key="mkr2_solltemperatur",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        device="mkr2",
    ),
    "expansionsventil": HaHeliothermSensorEntityDescription(
        name="Expansionsventil",
        key="expansionsventil",
        native_unit_of_measurement="‰",
        device="main",
    ),
    "verdichteranforderung": HaHeliothermSensorEntityDescription(
        name="Anforderung",
        key="verdichteranforderung",
        device="main",
    ),
    "wmz_heizung": HaHeliothermSensorEntityDescription(
        name="Wärmemengenzähler Heizung",
        key="wmz_heizung",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "stromz_heizung": HaHeliothermSensorEntityDescription(
        name="Stromzähler Heizung",
        key="stromz_heizung",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "wmz_brauchwasser": HaHeliothermSensorEntityDescription(
        name="Wärmemengenzähler Brauchwasser",
        key="wmz_brauchwasser",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device="ww"
    ),
    "stromz_brauchwasser": HaHeliothermSensorEntityDescription(
        name="Stromzähler Brauchwasser",
        key="stromz_brauchwasser",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device="ww"
    ),
    "stromz_gesamt": HaHeliothermSensorEntityDescription(
        name="Stromzähler Gesamt",
        key="stromz_gesamt",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "stromz_leistung": HaHeliothermSensorEntityDescription(
        name="Stromzähler Leistung",
        key="stromz_leistung",
        native_unit_of_measurement="W",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "wmz_gesamt": HaHeliothermSensorEntityDescription(
        name="Wärmemengenzähler Gesamt",
        key="wmz_gesamt",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "wmz_leistung": HaHeliothermSensorEntityDescription(
        name="Wärmemengenzähler Leistung",
        key="wmz_leistung",
        native_unit_of_measurement="kW",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        device="counters",
    ),
    # Phase 1: Neue Sensoren
    "bsz_verdichter_ww": HaHeliothermSensorEntityDescription(
        name="Betriebsstundenzähler Verdichter Warmwasser",
        key="bsz_verdichter_ww",
        native_unit_of_measurement="h",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device="ww",
    ),
    "bsz_verdichter_hkr": HaHeliothermSensorEntityDescription(
        name="Betriebsstundenzähler Verdichter",
        key="bsz_verdichter_hkr",
        native_unit_of_measurement="h",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device="counters",
    ),
    "temp_raum1": HaHeliothermSensorEntityDescription(
        name="Raum 1 Temperatur",
        key="temp_raum1",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        device="hkr",
    ),
    "mkr1_temp_vorlauf": HaHeliothermSensorEntityDescription(
        name="Mischerkreis 1 Vorlauf",
        key="mkr1_temp_vorlauf",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        device="mkr1",
    ),
    "mkr1_temp_ruecklauf": HaHeliothermSensorEntityDescription(
        name="Mischerkreis 1 Rücklauf",
        key="mkr1_temp_ruecklauf",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        device="mkr1",
    ),
    "mkr2_temp_vorlauf": HaHeliothermSensorEntityDescription(
        name="Mischerkreis 2 Vorlauf",
        key="mkr2_temp_vorlauf",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        device="mkr2",
    ),
    "mkr2_temp_ruecklauf": HaHeliothermSensorEntityDescription(
        name="Mischerkreis 2 Rücklauf",
        key="mkr2_temp_ruecklauf",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        device="mkr2",
    ),
    # Phase 3: Solar & Durchfluss
    "solar_kt1": HaHeliothermSensorEntityDescription(
        name="Solarkollektor Temperatur ",
        key="solar_kt1",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        device="solar",
    ),
    "durchfluss_primaer": HaHeliothermSensorEntityDescription(
        name="Durchfluss primär",
        key="durchfluss_primaer",
        native_unit_of_measurement="l/min",
        device="counters",
    ),
}


BINARYSENSOR_TYPES: dict[str, list[HaHeliothermBinarySensorEntityDescription]] = {
    "on_off_heizkreispumpe": HaHeliothermBinarySensorEntityDescription(
        name="Heizkreispumpe",
        key="on_off_heizkreispumpe",
        device="pumps",
    ),
    "on_off_pufferladepumpe": HaHeliothermBinarySensorEntityDescription(
        name="Pufferladepumpe",
        key="on_off_pufferladepumpe",
        device="buffer",
    ),
    "on_off_verdichter": HaHeliothermBinarySensorEntityDescription(
        name="Verdichter",
        key="on_off_verdichter",
        device="main",
    ),
    "on_off_stoerung": HaHeliothermBinarySensorEntityDescription(
        name="Stoerung",
        key="on_off_stoerung",
        device="main",
    ),
    "on_off_evu_sperre": HaHeliothermBinarySensorEntityDescription(
        name="EVU Sperre",
        key="on_off_evu_sperre",
        device="main",
    ),
    "on_off_eq_ventilator": HaHeliothermBinarySensorEntityDescription(
        name="Energiequellen Ventilator",
        key="on_off_eq_ventilator",
        device="pumps",
    ),
    "ww_vorrang": HaHeliothermBinarySensorEntityDescription(
        name="Warmwasser Vorrang",
        key="ww_vorrang",
        device="ww",
    ),
    "kuehlen_umv_passiv": HaHeliothermBinarySensorEntityDescription(
        name="Kühlen UMV passiv",
        key="kuehlen_umv_passiv",
        device="main",
    ),
    # Phase 1: Neue Binary Sensoren
    "on_off_eq_pumpe": HaHeliothermBinarySensorEntityDescription(
        name="Energiequellen Pumpe",
        key="on_off_eq_pumpe",
        device="pumps",
    ),
}

SWITCH_TYPES: dict[str, list[HaHeliothermSwitchEntityDescription]] = {
    "climate_rl_soll_ovr": HaHeliothermSwitchEntityDescription(
        name="Rücklauf-Sollwert Override",
        key="climate_rl_soll_ovr",
        icon="mdi:toggle-switch",
        device="hkr",
    ),
    # Phase 2: Override Flags (entity_category=CONFIG)
    "aussentemp_override": HaHeliothermSwitchEntityDescription(
        name="Außentemp Override",
        key="aussentemp_override",
        icon="mdi:thermometer-alert",
        device="main",
        #entity_category="config",
    ),
    "puffer_override": HaHeliothermSwitchEntityDescription(
        name="Pufferspeicher Override",
        key="puffer_override",
        icon="mdi:water-thermometer",
        device="buffer",
        #entity_category="config",
    ),
    "brauchwasser_override": HaHeliothermSwitchEntityDescription(
        name="Brauchwasser Override",
        key="brauchwasser_override",
        icon="mdi:water-boiler-alert",
        device="ww",
        #entity_category="config",
    ),
}

BUTTON_TYPES: dict[str, list[HaHeliothermButtonEntityDescription]] = {
    # Phase 1: Entstörung Button
    "button_entstoerung": HaHeliothermButtonEntityDescription(
        name="Entstörung",
        key="button_entstoerung",
        icon="mdi:restart-alert",
        device="main",
    ),
}
