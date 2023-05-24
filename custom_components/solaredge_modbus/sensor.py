import logging
import re

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    POWER_VOLT_AMPERE_REACTIVE,
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
    METER_EVENTS,
#    MMPPT_EVENTS,
#    RRCR_STATUS,
#    SUNSPEC_DID,
#    SUNSPEC_SF_RANGE,
#    VENDOR_STATUS,
#    BatteryLimit,
#    SunSpecAccum,
    SunSpecNotImpl,
)
from .helpers import  update_accum
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
        _LOGGER.debug("====================== 01 ======")
        entities.append(SolarEdgeDevice(inverter, config_entry, coordinator))
        _LOGGER.debug("====================== 02 ======")
        entities.append(Version(inverter, config_entry, coordinator))
        _LOGGER.debug("====================== 03 ======")
        entities.append(SolarEdgeInverterStatus(inverter, config_entry, coordinator))
        _LOGGER.debug("====================== 04 ======")
        entities.append(StatusVendor(inverter, config_entry, coordinator))
        _LOGGER.debug("====================== 05 ======")
        entities.append(ACCurrentSensor(inverter, config_entry, coordinator))
        _LOGGER.debug("====================== 06 ======")
        entities.append(ACCurrentSensor(inverter, config_entry, coordinator, "A"))
        _LOGGER.debug("====================== 07 ======")
        entities.append(ACCurrentSensor(inverter, config_entry, coordinator, "B"))
        _LOGGER.debug("====================== 08 ======")
        entities.append(ACCurrentSensor(inverter, config_entry, coordinator, "C"))
        _LOGGER.debug("====================== 09 ======")
        entities.append(VoltageSensor(inverter, config_entry, coordinator, "AB"))
        _LOGGER.debug("====================== 10 ======")
        entities.append(VoltageSensor(inverter, config_entry, coordinator, "BC"))
        _LOGGER.debug("====================== 11 ======")
        entities.append(VoltageSensor(inverter, config_entry, coordinator, "CA"))
        _LOGGER.debug("====================== 12 ======")
        entities.append(VoltageSensor(inverter, config_entry, coordinator, "AN"))
        _LOGGER.debug("====================== 13 ======")
        entities.append(VoltageSensor(inverter, config_entry, coordinator, "BN"))
        _LOGGER.debug("====================== 14 ======")
        entities.append(VoltageSensor(inverter, config_entry, coordinator, "CN"))
        _LOGGER.debug("====================== 15 ======")
        entities.append(ACPower(inverter, config_entry, coordinator))
        _LOGGER.debug("====================== 16 ======")
        entities.append(ACFrequency(inverter, config_entry, coordinator))
        _LOGGER.debug("====================== 17 ======")
        entities.append(ACVoltAmp(inverter, config_entry, coordinator))
        _LOGGER.debug("====================== 18 ======")
        entities.append(ACVoltAmpReactive(inverter, config_entry, coordinator))
        _LOGGER.debug("====================== 19 ======")
        entities.append(ACPowerFactor(inverter, config_entry, coordinator))
        _LOGGER.debug("====================== 20 ======")
        entities.append(ACEnergy(inverter, config_entry, coordinator))
        _LOGGER.debug("====================== 21 ======")
        entities.append(DCCurrent(inverter, config_entry, coordinator, "1"))
        _LOGGER.debug("====================== 22 ======")
        entities.append(DCCurrent(inverter, config_entry, coordinator, "2"))
        _LOGGER.debug("====================== 22 ======")
        entities.append(DCVoltage(inverter, config_entry, coordinator, "1"))
        _LOGGER.debug("====================== 23 ======")
        entities.append(DCVoltage(inverter, config_entry, coordinator, "2"))
        _LOGGER.debug("====================== 23 ======")
        entities.append(DCPower(inverter, config_entry, coordinator))
        _LOGGER.debug("====================== 25 ======")
        entities.append(HeatSinkTemperature(inverter, config_entry, coordinator))
        _LOGGER.debug("====================== 26 ======")
        #entities.append(SolarEdgeActivePowerLimit(inverter, config_entry, coordinator))
        #entities.append(SolarEdgeCosPhi(inverter, config_entry, coordinator))
    
    _LOGGER.debug(entities)
    if entities:
        async_add_entities(entities)


class SolarEdgeSensorBase(CoordinatorEntity, SensorEntity):
    should_poll = False
    suggested_display_precision = 3
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

#    @property
#    def state(self) -> bool:
#        return self._platform.online

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

    def __init__(self, platform, config_entry, coordinator, phase: str = None):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""
        self._phase = phase
        _LOGGER.debug("__init__")
        _LOGGER.debug(phase)

#        if self._platform.decoded_model["C_SunSpec_DID"] in [101, 102, 103]:
#            self.SUNSPEC_NOT_IMPL = SunSpecNotImpl.UINT16
#        elif self._platform.decoded_model["C_SunSpec_DID"] in [201, 202, 203, 204]:
#            self.SUNSPEC_NOT_IMPL = SunSpecNotImpl.INT16
#        else:
#            raise RuntimeError(
#                "ACCurrentSensor C_SunSpec_DID "
#                f"{self._platform.decoded_model['C_SunSpec_DID']}"
#            )

    @property
    def unique_id(self) -> str:
        if self._phase is None:
            return f"{self._platform.uid_base}_ac_current"
        else:
            return f"{self._platform.uid_base}_ac_current_{self._phase.lower()}"

    @property
    def entity_registry_enabled_default(self) -> bool:
#        if self._phase is None:
#            return True

#        elif self._platform.decoded_model["C_SunSpec_DID"] in [
#            103,
#            203,
#            204,
#        ] and self._phase in [
#            "A",
#            "B",
#            "C",
#        ]:
#            return True

#        else:
#            return False
        return True

    @property
    def name(self) -> str:
        if self._phase is None:
            return "AC Current"
        else:
            return f"AC Current {self._phase.upper()}"

    @property
    def native_value(self):
        _LOGGER.debug("native_value")
        _LOGGER.debug(self._phase)
        if self._phase is None:
            model_key = "AC_Current"
        else:
            model_key = f"AC_Current_{self._phase.upper()}"
        _LOGGER.debug("========= 1 ==================")
        _LOGGER.debug(model_key)
        _LOGGER.debug("========= 2 ==================")
        _LOGGER.debug(self._platform.decoded_model)
        _LOGGER.debug("========= 3 ==================")
        _LOGGER.debug(self._platform.decoded_model[model_key])
        _LOGGER.debug("========= 4 ==================")
        
#        try:
#            if (
#                self._platform.decoded_model[model_key] == 
# self.SUNSPEC_NOT_IMPL
#                or self._platform.decoded_model["AC_Current_SF"] == 
# SunSpecNotImpl.INT16
#                or self._platform.decoded_model["AC_Current_SF"] 
# not in SUNSPEC_SF_RANGE
#            ):
#                return None

        self._platform.decoded_model[model_key]
#            else:
#                return scale_factor(
#                self._platform.decoded_model[model_key],
#                    self._platform.decoded_model["AC_Current_SF"],
#                )

#        except TypeError:
#            return None

#    @property
#    def suggested_display_precision(self):
#        return abs(self._platform.decoded_model["AC_Current_SF"])

class VoltageSensor(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.VOLTAGE
    state_class = SensorStateClass.MEASUREMENT
    native_unit_of_measurement = UnitOfElectricPotential.VOLT

    def __init__(self, platform, config_entry, coordinator, phase: str = None):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""
        self._phase = phase

#        if self._platform.decoded_model["C_SunSpec_DID"] in [101, 102, 103]:
#            self.SUNSPEC_NOT_IMPL = SunSpecNotImpl.UINT16
#        elif self._platform.decoded_model["C_SunSpec_DID"] in [201, 202, 203, 204]:
#            self.SUNSPEC_NOT_IMPL = SunSpecNotImpl.INT16
#        else:
#            raise RuntimeError(
#                "ACCurrentSensor C_SunSpec_DID "
#                f"{self._platform.decoded_model['C_SunSpec_DID']}"
#            )

    @property
    def unique_id(self) -> str:
        if self._phase is None:
            return f"{self._platform.uid_base}_ac_voltage"
        else:
            return f"{self._platform.uid_base}_ac_voltage_{self._phase.lower()}"

    @property
    def entity_registry_enabled_default(self) -> bool:
        if self._phase is None:
            raise NotImplementedError

       # elif self._phase in ["LN", "LL", "AB"]:
       #     return True

#        elif self._platform.decoded_model["C_SunSpec_DID"] in [
#            103,
#            203,
#            204,
#        ] and self._phase in [
#            "BC",
#            "CA",
#            "AN",
#            "BN",
#            "CN",
#        ]:
#            return True

        else:
            return True

    @property
    def name(self) -> str:
        if self._phase is None:
            return "AC Voltage"
        else:
            return f"AC Voltage {self._phase.upper()}"

    @property
    def native_value(self):
        if self._phase is None:
            model_key = "AC_Voltage"
        else:
            model_key = f"AC_Voltage_{self._phase.upper()}"

#        try:
#            if (
#                self._platform.decoded_model[model_key] == 
# self.SUNSPEC_NOT_IMPL
#                or self._platform.decoded_model["AC_Voltage_SF"] == 
# SunSpecNotImpl.INT16
#                or self._platform.decoded_model["AC_Voltage_SF"] 
# not in SUNSPEC_SF_RANGE
#            ):
#                return None

#            else:
        _LOGGER.debug(model_key)
        _LOGGER.debug(self._phase)

        self._platform.decoded_model[model_key]
#                return scale_factor(
#                    self._platform.decoded_model[model_key],
                  #  self._platform.decoded_model["AC_Voltage_SF"],
#                    self._platform.decoded_model["AC_Voltage_AB"],
#                )

#        except TypeError:
#            return None

#    @property
#    def suggested_display_precision(self):
#        return abs(self._platform.decoded_model["AC_Voltage_SF"])

class ACPower(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.POWER
    state_class = SensorStateClass.MEASUREMENT
    native_unit_of_measurement = UnitOfPower.WATT
    icon = "mdi:solar-power"

    def __init__(self, platform, config_entry, coordinator, phase: str = None):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""
        self._phase = phase

    @property
    def unique_id(self) -> str:
        if self._phase is None:
            return f"{self._platform.uid_base}_ac_power"
        else:
            return f"{self._platform.uid_base}_ac_power_{self._phase.lower()}"

    @property
    def entity_registry_enabled_default(self) -> bool:
        if self._phase is None:
            return True

#        elif self._platform.decoded_model["C_SunSpec_DID"] in [
#            203,
#            204,
#        ] and self._phase in [
#            "A",
#            "B",
#            "C",
#        ]:
#            return True

#        else:
#            return False
        return True

    @property
    def name(self) -> str:
        if self._phase is None:
            return "AC Power"
        else:
            return f"AC Power {self._phase.upper()}"

    @property
    def native_value(self):
        if self._phase is None:
            model_key = "AC_Power"
        else:
            model_key = f"AC_Power_{self._phase.upper()}"

        try:
#            if (
#                self._platform.decoded_model[model_key] == SunSpecNotImpl.INT16
#                or self._platform.decoded_model["AC_Power_SF"] == 
# SunSpecNotImpl.INT16
#            ):
#                return None

#            else:
                _LOGGER.debug(model_key)
                _LOGGER.debug(self._phase)

                self._platform.decoded_model[model_key]
#                return scale_factor(
#                    self._platform.decoded_model[model_key],
#                    self._platform.decoded_model["AC_Power_SF"],
#                )

        except TypeError:
            return None

#    @property
#    def suggested_display_precision(self):
#        return abs(self._platform.decoded_model["AC_Power_SF"])


class ACFrequency(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.FREQUENCY
    state_class = SensorStateClass.MEASUREMENT
    native_unit_of_measurement = UnitOfFrequency.HERTZ
    
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
        try:
#            if (
#                self._platform.decoded_model["AC_Frequency"] == 
# SunSpecNotImpl.UINT16
#                or self._platform.decoded_model["AC_Frequency_SF"]
#                == SunSpecNotImpl.INT16
#                or self._platform.decoded_model["AC_Frequency_SF"]
#                not in SUNSPEC_SF_RANGE
#            ):
#                return None

#            else:
                _LOGGER.debug("AC_Frequency")
                _LOGGER.debug(self._platform.decoded_model["AC_Frequency"])

                self._platform.decoded_model["AC_Frequency"]
                #return scale_factor(
                #    self._platform.decoded_model["AC_Frequency"],
                #    self._platform.decoded_model["AC_Frequency_SF"],
                #)

        except TypeError:
            return None

#    @property
#    def suggested_display_precision(self):
#        return abs(self._platform.decoded_model["AC_Frequency_SF"])


class ACVoltAmp(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.APPARENT_POWER
    state_class = SensorStateClass.MEASUREMENT
    native_unit_of_measurement = UnitOfApparentPower.VOLT_AMPERE

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
    def entity_registry_enabled_default(self) -> bool:
        return False

    @property
    def native_value(self):
        if self._phase is None:
            model_key = "AC_VA"
        else:
            model_key = f"AC_VA_{self._phase.upper()}"

        try:
#            if (
#                self._platform.decoded_model[model_key] == SunSpecNotImpl.INT16
#                or self._platform.decoded_model["AC_VA_SF"] == SunSpecNotImpl.INT16
#                or self._platform.decoded_model["AC_VA_SF"] not in SUNSPEC_SF_RANGE
#            ):
#                return None

#            else:
                _LOGGER.debug(model_key)
                _LOGGER.debug(self._phase)

                self._platform.decoded_model[model_key]
#                return scale_factor(
#                    self._platform.decoded_model[model_key],
#                    self._platform.decoded_model["AC_VA_SF"],
#                )

        except TypeError:
            return None

#    @property
#    def suggested_display_precision(self):
#        return abs(self._platform.decoded_model["AC_VA_SF"])


class ACVoltAmpReactive(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.REACTIVE_POWER
    state_class = SensorStateClass.MEASUREMENT
    native_unit_of_measurement = POWER_VOLT_AMPERE_REACTIVE

    def __init__(self, platform, config_entry, coordinator, phase: str = None):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""
        self._phase = phase

    @property
    def unique_id(self) -> str:
        if self._phase is None:
            return f"{self._platform.uid_base}_ac_var"
        else:
            return f"{self._platform.uid_base}_ac_var_{self._phase.lower()}"

    @property
    def name(self) -> str:
        if self._phase is None:
            return "AC var"
        else:
            return f"AC var {self._phase.upper()}"

    @property
    def entity_registry_enabled_default(self) -> bool:
        return False

    @property
    def native_value(self):
        if self._phase is None:
            model_key = "AC_var"
        else:
            model_key = f"AC_var_{self._phase.upper()}"

        try:
#            if (
#                self._platform.decoded_model[model_key] == SunSpecNotImpl.INT16
#                or self._platform.decoded_model["AC_var_SF"] == SunSpecNotImpl.INT16
#                or self._platform.decoded_model["AC_var_SF"] not in SUNSPEC_SF_RANGE
#            ):
#                return None

#            else:
                _LOGGER.debug(model_key)
                _LOGGER.debug(self._phase)

                self._platform.decoded_model[model_key]
#                return scale_factor(
#                    self._platform.decoded_model[model_key],
#                    self._platform.decoded_model["AC_var_SF"],
#                )

        except TypeError:
            return None

#    @property
#    def suggested_display_precision(self):
#        return abs(self._platform.decoded_model["AC_var_SF"])


class ACPowerFactor(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.POWER_FACTOR
    state_class = SensorStateClass.MEASUREMENT
    native_unit_of_measurement = PERCENTAGE

    def __init__(self, platform, config_entry, coordinator, phase: str = None):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""
        self._phase = phase

    @property
    def unique_id(self) -> str:
        if self._phase is None:
            return f"{self._platform.uid_base}_ac_pf"
        else:
            return f"{self._platform.uid_base}_ac_pf_{self._phase.lower()}"

    @property
    def name(self) -> str:
        if self._phase is None:
            return "AC PF"
        else:
            return f"AC PF {self._phase.upper()}"

    @property
    def entity_registry_enabled_default(self) -> bool:
        return False

    @property
    def native_value(self):
        if self._phase is None:
            model_key = "AC_PF"
        else:
            model_key = f"AC_PF_{self._phase.upper()}"

        try:
#            if (
#                self._platform.decoded_model[model_key] == SunSpecNotImpl.INT16
#                or self._platform.decoded_model["AC_PF_SF"] == SunSpecNotImpl.INT16
#                or self._platform.decoded_model["AC_PF_SF"] not in SUNSPEC_SF_RANGE
#            ):
#                return None

#            else:
                _LOGGER.debug(model_key)
                _LOGGER.debug(self._phase)

                self._platform.decoded_model[model_key]
#                return scale_factor(
#                    self._platform.decoded_model[model_key],
#                    self._platform.decoded_model["AC_PF_SF"],
#                )

        except TypeError:
            return None

#    @property
#    def suggested_display_precision(self):
#        return abs(self._platform.decoded_model["AC_PF_SF"])


class ACEnergy(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.ENERGY
    state_class = SensorStateClass.TOTAL_INCREASING
    native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
#    suggested_display_precision = 3

    def __init__(self, platform, config_entry, coordinator, phase: str = None):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""
        self._phase = phase
        self.last = None

#        if self._platform.decoded_model["C_SunSpec_DID"] in [101, 102, 103]:
#            self.SUNSPEC_NOT_IMPL = SunSpecNotImpl.UINT16
#        elif self._platform.decoded_model["C_SunSpec_DID"] in [201, 202, 203, 204]:
#            self.SUNSPEC_NOT_IMPL = SunSpecNotImpl.INT16
#        else:
#            raise RuntimeError(
#                "ACEnergy C_SunSpec_DID ",
#                f"{self._platform.decoded_model['C_SunSpec_DID']}",
#            )

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
    def unique_id(self) -> str:
        if self._phase is None:
            return f"{self._platform.uid_base}_ac_energy_kwh"
        else:
            return f"{self._platform.uid_base}_{self._phase.lower()}_kwh"

    @property
    def entity_registry_enabled_default(self) -> bool:
#        if self._phase is None or self._phase in [
#            "Exported",
#            "Imported",
#            "Exported_A",
#            "Imported_A",
#        ]:
#            return True

#        elif self._platform.decoded_model["C_SunSpec_DID"] in [
#            203,
#            204,
#        ] and self._phase in [
#            "Exported_B",
#            "Exported_C",
#            "Imported_B",
#            "Imported_C",
#        ]:
#            return True

#        else:
#            return False
        return False

    @property
    def name(self) -> str:
        if self._phase is None:
            return "AC Energy kWh"
        else:
            return f"{re.sub('_', ' ', self._phase)} kWh"

    @property
    def native_value(self):
        if self._phase is None:
            model_key = "AC_Energy_WH"
        else:
            model_key = f"AC_Energy_WH_{self._phase}"

        try:
#            if (
#                self._platform.decoded_model[model_key] == SunSpecAccum.NA32
#                or self._platform.decoded_model[model_key] > SunSpecAccum.LIMIT32
#                or self._platform.decoded_model["AC_Energy_WH_SF"]
#                == self.SUNSPEC_NOT_IMPL
#                or self._platform.decoded_model["AC_Energy_WH_SF"]
#                not in SUNSPEC_SF_RANGE
#            ):
#                return None

#            else:
                _LOGGER.debug(model_key)
                _LOGGER.debug(self._phase)

                value = self._platform.decoded_model[model_key]
#                value = scale_factor(
#                    self._platform.decoded_model[model_key],
#                    self._platform.decoded_model["AC_Energy_WH_SF"],
#                )

                try:
                    return update_accum(self, value) * 0.001
                except Exception:
                    return None

        except TypeError:
            return None


class DCCurrent(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.CURRENT
    state_class = SensorStateClass.MEASUREMENT
    native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    icon = "mdi:current-dc"

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
            model_key = "DC_Current"
        else:
            model_key = f"DC_Current_{self._phase.upper()}"

#        try:
#            if (
#                self._platform.decoded_model["I_DC_Current"] == SunSpecNotImpl.UINT16
#                or self._platform.decoded_model["I_DC_Current_SF"]
#                == SunSpecNotImpl.INT16
#                or self._platform.decoded_model["I_DC_Current_SF"]
#                not in SUNSPEC_SF_RANGE
#            ):
#                return None

#            else:
        _LOGGER.debug(model_key)
        self._platform.decoded_model[model_key]
#                return scale_factor(
#                    self._platform.decod#ed_model["I_DC_Current"],
#                    self._platform.decoded_model["I_DC_Current_SF"],
#                )

#        except TypeError:
#            return None

#    @property
#    def suggested_display_precision(self):
#        return abs(self._platform.decoded_model["I_DC_Current_SF"])


class DCVoltage(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.VOLTAGE
    state_class = SensorStateClass.MEASUREMENT
    native_unit_of_measurement = UnitOfElectricPotential.VOLT

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
            model_key = "DC_Voltage"
        else:
            model_key = f"DC_Voltage_{self._phase.upper()}"
    
        _LOGGER.debug(model_key)
        self._platform.decoded_model[model_key]

#    @property
#    def suggested_display_precision(self):
#        return abs(self._platform.decoded_model["I_DC_Voltage_SF"])


class DCPower(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.POWER
    state_class = SensorStateClass.MEASUREMENT
    native_unit_of_measurement = UnitOfPower.WATT
    icon = "mdi:solar-power"

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
        #try:
#            if (
#                self._platform.decoded_model["I_DC_Power"] == 
# SunSpecNotImpl.INT16
#                or self._platform.decoded_model["I_DC_Power_SF"] == 
# SunSpecNotImpl.INT16
#                or self._platform.decoded_model["I_DC_Power_SF"] 
# not in SUNSPEC_SF_RANGE
#            ):
#                return None

#            else:
        _LOGGER.debug("I_DC_Power")

        self._platform.decoded_model["I_DC_Power"]
#                return scale_factor(
#                    self._platform.decoded_model["I_DC_Power"],
#                    self._platform.decoded_model["I_DC_Power_SF"],
#                )

        #except TypeError:
        #    return None

#    @property
#    def suggested_display_precision(self):
#        return abs(self._platform.decoded_model["I_DC_Power_SF"])


class HeatSinkTemperature(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.TEMPERATURE
    state_class = SensorStateClass.MEASUREMENT
    native_unit_of_measurement = UnitOfTemperature.CELSIUS

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
        try:
#            if (
#                self._platform.decoded_model["I_Temp_Sink"] == 0x0
#                or self._platform.decoded_model["I_Temp_Sink"] == 
# SunSpecNotImpl.INT16
#                or self._platform.decoded_model["I_Temp_SF"] == 
# SunSpecNotImpl.INT16
#                or self._platform.decoded_model["I_Temp_SF"] 
# not in SUNSPEC_SF_RANGE
#            ):
#                return None

#            else:
                self._platform.decoded_model["I_Temp_Sink"]
#                return scale_factor(
#                    self._platform.decoded_model["I_Temp_Sink"],
#                    self._platform.decoded_model["I_Temp_SF"],
#                )

        except TypeError:
            return None

#    @property
#    def suggested_display_precision(self):
#        return abs(self._platform.decoded_model["I_Temp_SF"])


class SolarEdgeStatusSensor(SolarEdgeSensorBase):
    device_class = SensorDeviceClass.ENUM
    entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, platform, config_entry, coordinator):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""

    @property
    def unique_id(self) -> str:
        _LOGGER.debug("unique_id")
        _LOGGER.debug(self._platform.uid_base)
        
        return f"{self._platform.uid_base}_status"

    @property
    def name(self) -> str:
        return "Status"

    @property
    def native_value(self):
        _LOGGER.debug("native_value")
        return True

class SolarEdgeInverterStatus(SolarEdgeStatusSensor):
    options = list(DEVICE_STATUS.values())

    def __init__(self, platform, config_entry, coordinator):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""

    @property
    def native_value(self):
        try:
            if self._platform.decoded_model["I_Status"] == SunSpecNotImpl.INT16:
                return None

            return str(DEVICE_STATUS[self._platform.decoded_model["I_Status"]])

        except TypeError:
            return None

        except KeyError:
            return None

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
        _LOGGER.debug("I_Status_Vendor")

    #    try:
    #        if self._platform.decoded_model["I_Status_Vendor"] == SunSpecNotImpl.INT16:
    #            return None

    #        else:
    #            return str(self._platform.decoded_model["I_Status_Vendor"])

   #     except TypeError:
        return str(self._platform.decoded_model["I_Status_Vendor"])

    #@property
    #def extra_state_attributes(self):
    #    try:
    #        if self._platform.decoded_model["I_Status_Vendor"] in VENDOR_STATUS:
    #            return {
    #                "description": VENDOR_STATUS[
    #                    self._platform.decoded_model["I_Status_Vendor"]
    #                ]
    #            }

    #        else:
    #            return None

    #    except KeyError:
    #        return None

class MeterEvents(SolarEdgeSensorBase):
    entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, platform, config_entry, coordinator):
        super().__init__(platform, config_entry, coordinator)
        """Initialize the sensor."""

    @property
    def unique_id(self) -> str:
        return f"{self._platform.uid_base}_meter_events"

    @property
    def name(self) -> str:
        return "Meter Events"

    @property
    def native_value(self):
        _LOGGER.debug("M_Events")

        try:
            if self._platform.decoded_model["M_Events"] == SunSpecNotImpl.UINT32:
                return None

            else:
                return self._platform.decoded_model["M_Events"]

        except TypeError:
            return None

    @property
    def extra_state_attributes(self):
        attrs = {}
        m_events_active = []

        if int(str(self._platform.decoded_model["M_Events"])) == 0x0:
            attrs["events"] = str(m_events_active)
        else:
            for i in range(2, 31):
                try:
                    if int(str(self._platform.decoded_model["M_Events"])) & (1 << i):
                        m_events_active.append(METER_EVENTS[i])

                except KeyError:
                    pass

        attrs["bits"] = f"{int(self._platform.decoded_model['M_Events']):032b}"
        attrs["events"] = str(m_events_active)

        return attrs
