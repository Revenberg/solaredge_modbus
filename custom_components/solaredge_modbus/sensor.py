import logging
import re

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
#    PERCENTAGE,
#    POWER_VOLT_AMPERE_REACTIVE,
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    #BATTERY_STATUS,
    #BATTERY_STATUS_TEXT,
    DEVICE_STATUS,
    DEVICE_STATUS_TEXT,
    DOMAIN,
#    ENERGY_VOLT_AMPERE_HOUR,
#    ENERGY_VOLT_AMPERE_REACTIVE_HOUR,
    #METER_EVENTS,
#    MMPPT_EVENTS,
#    RRCR_STATUS,
#    SUNSPEC_DID,
#    SUNSPEC_SF_RANGE,
#    VENDOR_STATUS,
#    BatteryLimit,
#    SunSpecAccum,
    #SunSpecNotImpl,
)
#from .helpers import  update_accum
# scale_factor, float_to_hex
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    entities = []

    for inverter in hub.inverters:
        entities.append(SolarEdgeDevice(inverter, config_entry, coordinator))
        entities.append(Version(inverter, config_entry, coordinator))
        entities.append(SolarEdgeInverterStatus(inverter, config_entry, coordinator))
        entities.append(StatusVendor(inverter, config_entry, coordinator))
        entities.append(ACCurrentSensor(inverter, config_entry, coordinator, "A"))
        entities.append(ACCurrentSensor(inverter, config_entry, coordinator, "B"))
        entities.append(ACCurrentSensor(inverter, config_entry, coordinator, "C"))
        entities.append(VoltageSensor(inverter, config_entry, coordinator, "BC"))
        entities.append(VoltageSensor(inverter, config_entry, coordinator, "CA"))
        entities.append(VoltageSensor(inverter, config_entry, coordinator, "AB"))
        entities.append(ACPower(inverter, config_entry, coordinator))
        entities.append(ACFrequency(inverter, config_entry, coordinator))
        #entities.append(ACVoltAmp(inverter, config_entry, coordinator))
        #entities.append(ACVoltAmpReactive(inverter, config_entry, coordinator))
        #entities.append(ACPowerFactor(inverter, config_entry, coordinator))
        entities.append(ACEnergy(inverter, config_entry, coordinator))
        entities.append(DCCurrent(inverter, config_entry, coordinator, "1"))
        entities.append(DCCurrent(inverter, config_entry, coordinator, "2"))
        entities.append(DCVoltage(inverter, config_entry, coordinator, "1"))
        entities.append(DCVoltage(inverter, config_entry, coordinator, "2"))
        #entities.append(DCPower(inverter, config_entry, coordinator))
        entities.append(HeatSinkTemperature(inverter, config_entry, coordinator))
        #entities.append(SolarEdgeActivePowerLimit(inverter, config_entry, coordinator))
        #entities.append(SolarEdgeCosPhi(inverter, config_entry, coordinator))
        entities.append(ACGenerated(inverter, config_entry, coordinator, 
                                    "lifetimeproduction", 0))
        entities.append(ACGenerated(inverter, config_entry, coordinator, 
                                    "lastmonth", 0))
        entities.append(ACGenerated(inverter, config_entry, coordinator, 
                                    "monthenergy", 1))
        entities.append(ACGenerated(inverter, config_entry, coordinator, 
                                    "yearenergy", 0))
        entities.append(ACGenerated(inverter, config_entry, coordinator,  
                                    "lastyear", 0))
        entities.append(ACGenerated(inverter, config_entry, coordinator, 
                                    "today", 3))
        entities.append(ACGenerated(inverter, config_entry, coordinator, 
                                    "yesterday", 3))


    _LOGGER.debug(entities)
    if entities:
        async_add_entities(entities)

class SolarEdgeSensorBase(CoordinatorEntity, SensorEntity):
    should_poll = False
    #suggested_display_precision = 3
    _attr_has_entity_name = True
    
    def __init__(self, platform, config_entry, coordinator):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        """Initialize the sensor."""
        self._platform = platform
        self._config_entry = config_entry
    
    @property
    def device_info(self):
        return self._platform.device_info

    @property
    def config_entry_id(self):
        return self._config_entry.entry_id

    @property
    def config_entry_name(self):
        return self._config_entry.data["name"]

    @property
    def available(self) -> bool:
        return self._platform.online

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

class SolarEdgeDevice(SolarEdgeSensorBase):
    entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, platform, config_entry, coordinator):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""

    @property
    def unique_id(self) -> str:
        return f"{self._platform.uid_base}_device"

    @property
    def name(self) -> str:
        return "Device"

    @property
    def native_value(self):
        return self._platform.model

    @property
    def extra_state_attributes(self):
        attrs = {}

#        try:
#            if (
#                float_to_hex(self._platform.decoded_common["B_MaxChargePeakPower"])
#                != hex(SunSpecNotImpl.FLOAT32)
#                and self._platform.decoded_common["B_MaxChargePeakPower"] > 0
#            ):
#                attrs["batt_charge_peak"] = self._platform.decoded_common[
#                    "B_MaxChargePeakPower"
#                ]

#            if (
#                float_to_hex(self._platform.decoded_common["B_MaxDischargePeakPower"])
#                != hex(SunSpecNotImpl.FLOAT32)
#                and self._platform.decoded_common["B_MaxDischargePeakPower"] > 0
#            ):
#                attrs["batt_discharge_peak"] = self._platform.decoded_common[
#                    "B_MaxDischargePeakPower"
#                ]

#            if (
#                float_to_hex(self._platform.decoded_common["B_MaxChargePower"])
#                != hex(SunSpecNotImpl.FLOAT32)
#                and self._platform.decoded_common["B_MaxChargePower"] > 0
#            ):
#                attrs["batt_max_charge"] = self._platform.decoded_common[
#                    "B_MaxChargePower"
#                ]

#            if (
#                float_to_hex(self._platform.decoded_common["B_MaxDischargePower"])
#                != hex(SunSpecNotImpl.FLOAT32)
#                and self._platform.decoded_common["B_MaxDischargePower"] > 0
#            ):
#                attrs["batt_max_discharge"] = self._platform.decoded_common[
#                    "B_MaxDischargePower"
#                ]

#            if (
#                float_to_hex(self._platform.decoded_common["B_RatedEnergy"])
#                != hex(SunSpecNotImpl.FLOAT32)
#                and self._platform.decoded_common["B_RatedEnergy"] > 0
#            ):
#                attrs["batt_rated_energy"] = self._platform.decoded_common[
#                    "B_RatedEnergy"
#                ]

#        except KeyError:
#            pass

        attrs["device_id"] = self._platform.device_address
        attrs["manufacturer"] = self._platform.manufacturer
        attrs["model"] = self._platform.model

        if self._platform.has_parent:
            attrs["parent_device_id"] = self._platform.inverter_unit_id

        attrs["serial_number"] = self._platform.serial

#        try:
#            if self._platform.decoded_model["C_SunSpec_DID"] in SUNSPEC_DID:
#                attrs["sunspec_device"] = SUNSPEC_DID[
#                    self._platform.decoded_model["C_SunSpec_DID"]
#                ]

#        except KeyError:
#            pass

#        try:
#            attrs["sunspec_did"] = self._platform.decoded_model["C_SunSpec_DID"]

#        except KeyError:
#            pass

#        try:
#            if self._platform.decoded_mmppt is not None:
#                try:
#                    if self._platform.decoded_mmppt["mmppt_DID"] in SUNSPEC_DID:
#                        attrs["mmppt_device"] = SUNSPEC_DID[
#                            self._platform.decoded_mmppt["mmppt_DID"]
#                        ]

#                except KeyError:
#                    pass

#                attrs["mmppt_did"] = self._platform.decoded_mmppt["mmppt_DID"]
#                attrs["mmppt_units"] = self._platform.decoded_mmppt["mmppt_Units"]

#        except AttributeError:
#            pass

        return attrs


class Version(SolarEdgeSensorBase):
    entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, platform, config_entry, coordinator):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""

    @property
    def unique_id(self) -> str:
        return f"{self._platform.uid_base}_version"

    @property
    def name(self) -> str:
        return "Version"

    @property
    def native_value(self):
        return self._platform.fw_version

class ACCurrentSensor(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.CURRENT
    state_class = SensorStateClass.MEASUREMENT
    native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    suggested_display_precision = 1

    def __init__(self, platform, config_entry, coordinator, phase: str = None):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""
        self._phase = phase

    @property
    def unique_id(self) -> str:
        if self._phase is None:
            return f"{self._platform.uid_base}_ac_current"
        else:
            return f"{self._platform.uid_base}_ac_current_{self._phase.lower()}"

    @property
    def name(self) -> str:
        if self._phase is None:
            return "AC Current"
        else:
            return f"AC Current {self._phase.upper()}"

    @property
    def native_value(self):
        if self._phase is None:
            model_key = "ac_current"
        else:
            model_key = f"ac_current_{self._phase.lower()}"

        return self._platform.decoded_model[model_key]

class ACGenerated(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.POWER
    state_class = SensorStateClass.MEASUREMENT
    native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    suggested_display_precision = 0
    
    def __init__(self, platform, config_entry, coordinator, phase: str = None, 
                 suggested_display_precision: int = 0):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""
        self._phase = phase
        self.suggested_display_precision = suggested_display_precision

    @property
    def unique_id(self) -> str:
        if self._phase is None:
            return f"{self._platform.uid_base}_ac_generated"
        else:
            return f"{self._platform.uid_base}_ac_generated_{self._phase.lower()}"

    @property
    def name(self) -> str:
        if self._phase is None:
            return "AC Generated"
        else:
            return f"AC Generated {self._phase}"

    @property
    def native_value(self):
        if self._phase is None:
            model_key = "ac_generated"
        else:
            model_key = f"ac_generated_{self._phase.lower()}"

        return self._platform.decoded_model[model_key]

class VoltageSensor(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.VOLTAGE
    state_class = SensorStateClass.MEASUREMENT
    native_unit_of_measurement = UnitOfElectricPotential.VOLT
    suggested_display_precision = 0

    def __init__(self, platform, config_entry, coordinator, phase: str = None):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""
        self._phase = phase

    @property
    def unique_id(self) -> str:
        if self._phase is None:
            return f"{self._platform.uid_base}_ac_voltage"
        else:
            return f"{self._platform.uid_base}_ac_voltage_{self._phase.lower()}"

    @property
    def name(self) -> str:
        if self._phase is None:
            return "AC Voltage"
        else:
            return f"AC Voltage {self._phase}"

    @property
    def native_value(self):
        if self._phase is None:
            model_key = "ac_voltage"
        else:
            model_key = f"ac_voltage_{self._phase.lower()}"

        return self._platform.decoded_model[model_key]

class ACPower(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.POWER
    state_class = SensorStateClass.MEASUREMENT
    native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    icon = "mdi:solar-power"
    suggested_display_precision = 3

    def __init__(self, platform, config_entry, coordinator, phase: str = None):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""
        self._phase = phase

    @property
    def unique_id(self) -> str:
        if self._phase is None:
            return f"{self._platform.uid_base}_ac_power_output"
        else:
            return f"{self._platform.uid_base}_ac_power_output_{self._phase.lower()}"

    @property
    def name(self) -> str:
        if self._phase is None:
            return "AC Power"
        else:
            return f"AC Power {self._phase.upper()}"

    @property
    def native_value(self):
        if self._phase is None:
            model_key = "ac_power_output"
        else:
            model_key = f"ac_power_output_{self._phase.lower()}"

        return self._platform.decoded_model[model_key]

class ACFrequency(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.FREQUENCY
    state_class = SensorStateClass.MEASUREMENT
    native_unit_of_measurement = UnitOfFrequency.HERTZ
    suggested_display_precision = 1
    entity_registry_enabled_default = True

    def __init__(self, platform, config_entry, coordinator):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""

    @property
    def unique_id(self) -> str:
        return f"{self._platform.uid_base}_ac_frequency"

    @property
    def name(self) -> str:
        return "AC Frequency"

    @property
    def native_value(self):
                return self._platform.decoded_model["ac_frequency"]

class ACVoltAmp(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.APPARENT_POWER
    state_class = SensorStateClass.MEASUREMENT
    native_unit_of_measurement = UnitOfApparentPower.VOLT_AMPERE
    suggested_display_precision = 0

    def __init__(self, platform, config_entry, coordinator, phase: str = None):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""
        self._phase = phase

    @property
    def unique_id(self) -> str:
        if self._phase is None:
            return f"{self._platform.uid_base}_ac_va"
        else:
            return f"{self._platform.uid_base}_ac_va_{self._phase.lower()}"

    @property
    def name(self) -> str:
        if self._phase is None:
            return "AC VA"
        else:
            return f"AC VA {self._phase.upper()}"

    @property
    def native_value(self):
        if self._phase is None:
            model_key = "ac_va"
        else:
            model_key = f"ac_va_{self._phase.lower()}"


        return self._platform.decoded_model[model_key]

class ACEnergy(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.POWER
    state_class = SensorStateClass.TOTAL_INCREASING
    native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    suggested_display_precision = -3

    def __init__(self, platform, config_entry, coordinator, phase: str = None):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""
        self._phase = phase
        self.last = None

    @property
    def unique_id(self) -> str:
        if self._phase is None:
            return f"{self._platform.uid_base}_ac_energy_kwh"
        else:
            return f"{self._platform.uid_base}_{self._phase.lower()}_kwh"

    @property
    def icon(self) -> str:
        if self._phase is None:
            return None

        elif re.match("import", self._phase.lower()):
            return "mdi:transmission-tower-export"

        elif re.match("export", self._phase.lower()):
            return "mdi:transmission-tower-import"

        else:
            return None

    @property
    def name(self) -> str:
        if self._phase is None:
            return "AC Energy kWh"
        else:
            return f"{re.sub('_', ' ', self._phase)} kWh"

    @property
    def native_value(self):
        if self._phase is None:
            model_key = "ac_energy_wh"
        else:
            model_key = f"ac_energy_wh_{self._phase.lower()}"

        return self._platform.decoded_model[model_key]

class DCCurrent(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.CURRENT
    state_class = SensorStateClass.MEASUREMENT
    native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    icon = "mdi:current-dc"
    suggested_display_precision = 1

    def __init__(self, platform, config_entry, coordinator, phase: str = None):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""
        self._phase = phase

    @property
    def unique_id(self) -> str:
        if self._phase is None:
            return f"{self._platform.uid_base}_dc_current"
        else:
            return f"{self._platform.uid_base}_dc_current_{self._phase.lower()}"

    @property
    def name(self) -> str:
        if self._phase is None:
            return "DC Current"
        else:
            return f"DC Current {self._phase.upper()}"

    @property
    def native_value(self):
        if self._phase is None:
            model_key = "dc_current"
        else:
            model_key = f"dc_current_{self._phase.lower()}"

        return self._platform.decoded_model[model_key]

class DCVoltage(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.VOLTAGE
    state_class = SensorStateClass.MEASUREMENT
    native_unit_of_measurement = UnitOfElectricPotential.VOLT
    suggested_display_precision = 1

    def __init__(self, platform, config_entry, coordinator, phase: str = None):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""
        self._phase = phase

    @property
    def unique_id(self) -> str:
        if self._phase is None:
            return f"{self._platform.uid_base}_dc_voltage"
        else:
            return f"{self._platform.uid_base}_dc_voltage_{self._phase.lower()}"

    @property
    def name(self) -> str:
        if self._phase is None:
            return "DC Voltage"
        else:
            return f"DC Voltage {self._phase.upper()}"

    @property
    def native_value(self):
        if self._phase is None:
            model_key = "dc_voltage"
        else:
            model_key = f"dc_voltage_{self._phase.lower()}"

        return self._platform.decoded_model[model_key]

class DCPower(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.POWER
    state_class = SensorStateClass.MEASUREMENT
    native_unit_of_measurement = UnitOfPower.WATT
    icon = "mdi:solar-power"
    suggested_display_precision = 0

    def __init__(self, platform, config_entry, coordinator):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""

    @property
    def unique_id(self) -> str:
        return f"{self._platform.uid_base}_dc_power"

    @property
    def name(self) -> str:
        return "DC Power"

    @property
    def native_value(self):
       
        return self._platform.decoded_model["i_dc_power"]

class HeatSinkTemperature(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.TEMPERATURE
    state_class = SensorStateClass.MEASUREMENT
    native_unit_of_measurement = UnitOfTemperature.CELSIUS
    suggested_display_precision = 1

    def __init__(self, platform, config_entry, coordinator):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""

    @property
    def unique_id(self) -> str:
        return f"{self._platform.uid_base}_temp_sink"

    @property
    def name(self) -> str:
        return "Temp Sink"

    @property
    def native_value(self):
        return self._platform.decoded_model["i_temp_sink"]

class SolarEdgeStatusSensor(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.ENUM
    entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, platform, config_entry, coordinator):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""

    @property
    def unique_id(self) -> str:
        return f"{self._platform.uid_base}_status"

    @property
    def name(self) -> str:
        return "Status"

    @property
    def native_value(self):
        return str(DEVICE_STATUS[self._platform.decoded_model["i_status"]])

class SolarEdgeInverterStatus(SolarEdgeStatusSensor):
    options = list(DEVICE_STATUS.values())

    def __init__(self, platform, config_entry, coordinator):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""

    @property
    def unique_id(self) -> str:
        return f"{self._platform.uid_base}_i_status"
        
    @property
    def native_value(self):
       return str(DEVICE_STATUS[self._platform.decoded_model["i_status"]])

    @property
    def extra_state_attributes(self):
        attrs = {}

        try:
            if self._platform.decoded_model["I_Status"] in DEVICE_STATUS_TEXT:
                attrs["status_text"] = DEVICE_STATUS_TEXT[
                    self._platform.decoded_model["I_Status"]
                ]

                attrs["status_value"] = self._platform.decoded_model["I_Status"]

        except KeyError:
            pass

        return attrs

class StatusVendor(SolarEdgeSensorBase):
    entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, platform, config_entry, coordinator):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""

    @property
    def unique_id(self) -> str:
        return f"{self._platform.uid_base}_status_vendor"

    @property
    def name(self) -> str:
        return "Status Vendor"

    @property
    def native_value(self):
        return str(DEVICE_STATUS[self._platform.decoded_model["i_status_vendor"]])