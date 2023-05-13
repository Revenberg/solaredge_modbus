"""Constance definition."""
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorEntityDescription,
    STATE_CLASS_MEASUREMENT,
    STATE_CLASS_TOTAL_INCREASING,
)

from homeassistant.const import (
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_POWER_FACTOR,
 #   DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_VOLTAGE,
    ELECTRIC_CURRENT_AMPERE,
#    ELECTRIC_CURRENT_MILLIAMPERE,
    ELECTRIC_POTENTIAL_VOLT,
    ENERGY_KILO_WATT_HOUR,
    FREQUENCY_HERTZ,
    PERCENTAGE,
 #   POWER_VOLT_AMPERE,
    POWER_WATT,
)

DOMAIN = "SolarEdge_modbus"
DEFAULT_NAME = "SolarEdge"
DEFAULT_SCAN_INTERVAL = 2
DEFAULT_PORT = 502
CONF_SolarEdge_HUB = "SolarEdge_hub"
ATTR_MANUFACTURER = "SolarEdge"

@dataclass
class SolarEdgeModbusSensorEntityDescription(SensorEntityDescription):
    """A class that describes SolarEdge Modbus sensor entities."""

SENSOR_TYPES: dict[str, list[SolarEdgeModbusSensorEntityDescription]] = {
    "voltage_a": SolarEdgeModbusSensorEntityDescription(
        name="Voltage L1",
        key="voltage_a",
        native_unit_of_measurement=ELECTRIC_POTENTIAL_VOLT,
        device_class=DEVICE_CLASS_VOLTAGE,
    ),
    "current_a": SolarEdgeModbusSensorEntityDescription(
        name="Current L1",
        key="current_a",
        native_unit_of_measurement=ELECTRIC_CURRENT_AMPERE,
        device_class=DEVICE_CLASS_CURRENT,
    ),
    "power_a": SolarEdgeModbusSensorEntityDescription(
        name="Power L1",
        key="power_a",
        native_unit_of_measurement=POWER_WATT,
        device_class=DEVICE_CLASS_POWER,
        state_class=STATE_CLASS_MEASUREMENT,
    ),
    "import_energy_a": SolarEdgeModbusSensorEntityDescription(
        name="Import Energy L1",
        key="import_energy_a",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        device_class=DEVICE_CLASS_ENERGY,
        state_class=STATE_CLASS_TOTAL_INCREASING,
    ),
    "export_energy_a": SolarEdgeModbusSensorEntityDescription(
        name="Export Energy L1",
        key="export_energy_a",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        device_class=DEVICE_CLASS_ENERGY,
        state_class=STATE_CLASS_TOTAL_INCREASING,
    ),
    "power_factor_a": SolarEdgeModbusSensorEntityDescription(
        name="Power Factor L1",
        key="power_factor_a",
        native_unit_of_measurement=PERCENTAGE,
        device_class=DEVICE_CLASS_POWER_FACTOR,
    ),
    "voltage_b": SolarEdgeModbusSensorEntityDescription(
        name="Voltage L2",
        key="voltage_b",
        native_unit_of_measurement=ELECTRIC_POTENTIAL_VOLT,
        device_class=DEVICE_CLASS_VOLTAGE,
    ),
    "current_b": SolarEdgeModbusSensorEntityDescription(
        name="Current L2",
        key="current_b",
        native_unit_of_measurement=ELECTRIC_CURRENT_AMPERE,
        device_class=DEVICE_CLASS_CURRENT,
    ),
    "power_b": SolarEdgeModbusSensorEntityDescription(
        name="Power L2",
        key="power_b",
        native_unit_of_measurement=POWER_WATT,
        device_class=DEVICE_CLASS_POWER,
        state_class=STATE_CLASS_MEASUREMENT,
    ),
    "import_energy_b": SolarEdgeModbusSensorEntityDescription(
        name="Import Energy L2",
        key="import_energy_b",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        device_class=DEVICE_CLASS_ENERGY,
        state_class=STATE_CLASS_TOTAL_INCREASING,
    ),
    "export_energy_b": SolarEdgeModbusSensorEntityDescription(
        name="Export Energy L2",
        key="export_energy_b",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        device_class=DEVICE_CLASS_ENERGY,
        state_class=STATE_CLASS_TOTAL_INCREASING,
    ),
    "power_factor_b": SolarEdgeModbusSensorEntityDescription(
        name="Power Factor L2",
        key="power_factor_b",
        native_unit_of_measurement=PERCENTAGE,
        device_class=DEVICE_CLASS_POWER_FACTOR,
    ),

    "voltage_c": SolarEdgeModbusSensorEntityDescription(
        name="Voltage L3",
        key="voltage_c",
        native_unit_of_measurement=ELECTRIC_POTENTIAL_VOLT,
        device_class=DEVICE_CLASS_VOLTAGE,
    ),
    "current_c": SolarEdgeModbusSensorEntityDescription(
        name="Current L3",
        key="current_c",
        native_unit_of_measurement=ELECTRIC_CURRENT_AMPERE,
        device_class=DEVICE_CLASS_CURRENT,
    ),
    "power_c": SolarEdgeModbusSensorEntityDescription(
        name="Power L3",
        key="power_c",
        native_unit_of_measurement=POWER_WATT,
        device_class=DEVICE_CLASS_POWER,
        state_class=STATE_CLASS_MEASUREMENT,
    ),
    "import_energy_c": SolarEdgeModbusSensorEntityDescription(
        name="Import Energy L3",
        key="import_energy_c",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        device_class=DEVICE_CLASS_ENERGY,
        state_class=STATE_CLASS_TOTAL_INCREASING,
    ),
    "export_energy_c": SolarEdgeModbusSensorEntityDescription(
        name="Export Energy L3",
        key="export_energy_c",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        device_class=DEVICE_CLASS_ENERGY,
        state_class=STATE_CLASS_TOTAL_INCREASING,
    ),
    "power_factor_c": SolarEdgeModbusSensorEntityDescription(
        name="Power Factor L3",
        key="power_factor_c",
        native_unit_of_measurement=PERCENTAGE,
        device_class=DEVICE_CLASS_POWER_FACTOR,
    ),
    "frequency": SolarEdgeModbusSensorEntityDescription(
        name="Frequency",
        key="frequency",
        native_unit_of_measurement=FREQUENCY_HERTZ,
    ),
    "total_power": SolarEdgeModbusSensorEntityDescription(
        name="Total Power",
        key="total_power",
        native_unit_of_measurement=POWER_WATT,
        device_class=DEVICE_CLASS_POWER,
        state_class=STATE_CLASS_MEASUREMENT,
    ),
    "total_import_energy": SolarEdgeModbusSensorEntityDescription(
        name="Total Import Energy",
        key="total_import_energy",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        device_class=DEVICE_CLASS_ENERGY,
        state_class=STATE_CLASS_TOTAL_INCREASING,
    ),
    "total_export_energy": SolarEdgeModbusSensorEntityDescription(
        name="Total Export Energy",
        key="total_export_energy",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        device_class=DEVICE_CLASS_ENERGY,
        state_class=STATE_CLASS_TOTAL_INCREASING,
    ),
}
