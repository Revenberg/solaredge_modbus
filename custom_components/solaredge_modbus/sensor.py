"""Sensor definition."""
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.components.sensor import SensorEntity
import logging
from typing import Optional
#, dict, Any
#import homeassistant.util.dt as dt_util

from .const import ATTR_MANUFACTURER, DOMAIN, SENSOR_TYPES, SolarEdgeModbusSensorEntityDescription

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Async_setup_entry."""
    hub_name = entry.data[CONF_NAME]
    hub = hass.data[DOMAIN][hub_name]["hub"]

    device_info = {
        "identifiers": {(DOMAIN, hub_name)},
        "name": hub_name,
        "manufacturer": ATTR_MANUFACTURER,
    }

    entities = []
    for sensor_description in SENSOR_TYPES.values():
        sensor = SolarEdgeModbusSensor(
            hub_name,
            hub,
            device_info,
            sensor_description,
        )
        entities.append(sensor)

    async_add_entities(entities)
    return True


class SolarEdgeModbusSensor(SensorEntity):
    """Representation of an SolarEdge Modbus sensor."""

    def __init__(
        self,
        platform_name,
        hub,
        device_info,
        description: SolarEdgeModbusSensorEntityDescription,
    ):
        """Initialize the sensor."""
        self._platform_name = platform_name
        self._attr_device_info = device_info
        self._hub = hub
        self.entity_description: SolarEdgeModbusSensorEntityDescription = description

    async def async_added_to_hass(self):
        """Register callbacks."""
        self._hub.async_add_SolarEdge_modbus_sensor(self._modbus_data_updated)

    async def async_will_remove_from_hass(self) -> None:
        """Async_will_remove_from_hass."""
        self._hub.async_remove_SolarEdge_modbus_sensor(self._modbus_data_updated)

    @callback
    def _modbus_data_updated(self):
        self.async_write_ha_state()

    @callback
    def _update_state(self):
        if self._key in self._hub.data:
            self._state = self._hub.data[self._key]

    @property
    def name(self):
        """Return the name."""
        return f"{self._platform_name} {self.entity_description.name}"

    @property
    def unique_id(self) -> Optional[str]:
        """Unique id."""
        return f"{self._platform_name}_{self.entity_description.key}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return (
            self._hub.data[self.entity_description.key]
            if self.entity_description.key in self._hub.data
            else None
        )
