"""Platform for sensor integration."""
# This file shows the setup for the sensors associated with the cover.
# They are setup in the same way with the call to the async_setup_entry function
# via HA from the module __init__. Each sensor has a device_class, this tells HA how
# to display it in the UI (for know types). The unit_of_measurement property tells HA
# what the unit is, so it can display the correct range. For predefined types (such as
# battery), the unit_of_measurement should match what's expected.
import random
import asyncio
#import serial

from homeassistant.const import (
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_ILLUMINANCE,
    ENERGY_KILO_WATT_HOUR,
    CONF_DEVICE,
)
#    PERCENTAGE,
#    ATTR_VOLTAGE,
from homeassistant.helpers.entity import Entity
from homeassistant import config_entries, core
#from homeassistant.helpers.aiohttp_client import async_get_clientsession
#from homeassistant.helpers.entity import Entity
from datetime import timedelta

#from .hub import Hub

from .const import DOMAIN, CONF_SCAN_INTERVAL
#, CONF_SERIAL
import logging

values = {}

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

ICON = "mdi:power-plug"
#SCAN_INTERVAL = timedelta(seconds=60)
_LOGGER.debug( __name__ )
#
#    _LOGGER.debug(  async_add_entities )
#    _LOGGER.debug(  config_entry.entry_id )
#    _LOGGER.debug(  config_entry )
#    _LOGGER.debug("---------------------------------------------------")
#    _LOGGER.debug("---------------------------------------------------")
#    _LOGGER.debug("---------------------------------------------------")
#    instrument = hass.data.get(SOLAREDGE_DOMAIN)
#    scan_interval = discovery_info[CONF_SCAN_INTERVAL]

#    async_add_entities([SolarEdgeModbusSensor(instrument, scan_interval)], True)

# See cover.py for more details.
# Note how both entities for each roller sensor (battry and illuminance) are added at
# the same time to the same list. This way only a single async_add_devices call is
# required.
async def async_setup_entry(hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    _LOGGER.debug("async_setup_entry")
    hub = hass.data[DOMAIN][config_entry.entry_id]

#    _LOGGER.debug("---------------------------------------------------")
#    _LOGGER.debug("---------------------------------------------------")
#    _LOGGER.debug("---------------------------------------------------")
#    _LOGGER.debug("---------------------------------------------------")
#    _LOGGER.debug("---------------------------------------------------")
#    _LOGGER.debug(  async_add_entities )
#    _LOGGER.debug(  config_entry.entry_id )
#    _LOGGER.debug(  config_entry )
#    _LOGGER.debug("!@!@!@!@!@!@!@!@!@!@!@!@!@!@!@!@!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
#    for key, value in hass.data[DOMAIN]:
#       print(key, ' : ', value)
#    config = hass.data[DOMAIN][config_entry.entry_id]
#    if config_entry.options:
#        config.update(config_entry.options)
    device = hass.data.get( CONF_DEVICE )
    _LOGGER.debug(  device  )
    title =  hass.data.get( 'title' )
    _LOGGER.debug(  title  )
    _LOGGER.debug("---------------------------------------------------")
    _LOGGER.debug(hub._instrument)
    _LOGGER.debug("---------------------------------------------------")
#    hub = Hub(hass, title, device)

    # The dummy hub provides a `test_connection` method to ensure it's working
    # as expected
#    result = await hub.connection()
#    if not result:
        # If there is an error, raise an exception to notify HA that there was a
        # problem. The UI will also show there was a problem
#        raise CannotConnect

#    ser =  hass.data.get( CONF_SERIAL )
#    _LOGGER.debug(  ser )
#    _LOGGER.debug( config["devices"] )
#    _LOGGER.debug("!@!@!@!@!@!@!@!@!@!@!@!@!@!@!@!@!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
#    session = async_get_clientsession(hass)
#    _LOGGER.debug( session )
#    _LOGGER.debug("!@!@!@!@!@!@!@!@!@!@!@!@!@!@!@!@!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
#    for key, value in config_entry:
#       print(key, ' : ', value)

    #_LOGGER.debug( config['host'] )
    #_LOGGER.debug( config['devices'] )

#    BAUDRATE = 9600
#    instrument = serial.Serial(
#                  device,
#                  BAUDRATE,
#                  timeout=10,
#                  bytesize=serial.SEVENBITS,
#                  parity=serial.PARITY_EVEN,
#                  stopbits=serial.STOPBITS_ONE
#    )

#    hass.data[config_entry.entry_id + "serial" ] = instrument

#    new_devices = []
#    for roller in hub.rollers:
#        new_devices.append(BatterySensor(roller))
#        new_devices.append(IlluminanceSensor(roller))
#        new_devices.append(EnergySensor(roller))
#    if new_devices:
#        async_add_entities(new_devices, True)
    #scan_interval =
    timedelta(seconds=60)

#    async_add_entities([energySensor1(hub._instrument, scan_interval)], True)
    async_add_entities([energySensor1(hub._instrument, hub._name, 60)], True)

class energySensor1(Entity):
    """energySensor1."""

    _attr_unit_of_measurement = ENERGY_KILO_WATT_HOUR
    device_clasync_added_to_hassass = DEVICE_CLASS_ENERGY
    p1 = 0
    p2 = 0
    p3 = 0
    p4 = 0
    p5 = 0

    def __init__(self, instrument, name, scan_interval):
        """init."""
        _LOGGER.debug("creating Energy sensor")
        self._instrument = instrument
        self._scan_interval = scan_interval
        self._state = 0
        self._name = name
        self._device_state_attributes = {}

    def getValueLong(self, addr, numberOfDecimals=0, functioncode=0, signed=False):
        """Get value long."""
        rc = self._instrument.read_long(addr, functioncode=functioncode, signed=signed)
        return rc

    def getValueRegister(self, addr, numberOfDecimals=0, functioncode=0, signed=False):
        """Get value register."""
        rc = self._instrument.read_register(addr, numberOfDecimals=numberOfDecimals, functioncode=functioncode, signed=signed)
        return rc

    def round(self, floatval):
        """Get value round."""
        return round(floatval, 2)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._device_state_attributes

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    async def async_added_to_hass(self):
        """async_added_to_hass."""
        _LOGGER.debug("added to hass, starting loop")
        loop = self.hass.loop
        #task =
        loop.create_task(self.energy_loop())

    async def energy_loop(self):
        """Energy loop."""
        while True:
            try:
                _LOGGER.debug("=============================================================")
                _LOGGER.debug("=============================================================")
                line = self._instrument.readline()
                _LOGGER.debug("=============================================================")
                _LOGGER.info(line)
                _LOGGER.info(line.decode("utf-8") )
                if (line.decode("utf-8") != ""):
                  valuesS = line.decode("utf-8").split(":")
                  self._serial = valuesS[1]
                  values['Serial'] = valuesS[1]
                  values['P1'] = valuesS[6]
                  values['P2'] = valuesS[9]
                  values['P3'] = valuesS[12]
                  values['P4'] = valuesS[15]
                  values['P5'] = valuesS[18]

                  if self.p1 != valuesS[6]:
                  #    _LOGGER.debug("=============================================================")
                    _LOGGER.debug("========================= p1 ================================")
                    _LOGGER.debug( self.p1)
                    _LOGGER.debug(valuesS[6])
                  #    _LOGGER.debug("=============================================================")
                  if self.p2 != valuesS[9]:
                  #    _LOGGER.debug("=============================================================")
                    _LOGGER.debug("========================= p2 ================================")
                    _LOGGER.debug( self.p2)
                    _LOGGER.debug(valuesS[9])
                  #    _LOGGER.debug("=============================================================")
                  if self.p3 != valuesS[12]:
                  #    _LOGGER.debug("=============================================================")
                    _LOGGER.debug("========================= p3 ================================")
                    _LOGGER.debug( self.p3)
                    _LOGGER.debug(valuesS[12])
                  #    _LOGGER.debug("=============================================================")
                  if self.p4 != valuesS[15]:
                  #    _LOGGER.debug("=============================================================")
                    _LOGGER.debug("========================= p4 ================================")
                    _LOGGER.debug( self.p4)
                    _LOGGER.debug(valuesS[15])
                  #    _LOGGER.debug("=============================================================")
                  if self.p5 != valuesS[18]:
                  #    _LOGGER.debug("=============================================================")
                    _LOGGER.debug("========================= p5 ================================")
                    _LOGGER.debug( self.p5)
                    _LOGGER.debug(valuesS[18])
                  #    _LOGGER.debug("=============================================================")

                  self.p1 = values['P1']
                  self.p2 = values['P2']
                  self.p3 = values['P3']
                  self.p4 = values['P4']
                  self.p5 = values['P5']

                #debug-print entire dictionary
                #for x in values.keys():
                #    _LOGGER.debug(x +" => " + str(values[x]))

                # Skip if increamenting counter has gone to 0, or become too large, this happens on inverter startup

   #             validValue = values['ac_lifetimeproduction'] > 0

#                if validValue:
                    #main state is power production, other values can be fetched as attributes
                  self._state = 1
                  values['_state'] = self._state
                  self._device_state_attributes = values

            except TimeoutError:
              _LOGGER.debug("Timeout")
              self._state = 2
              values['_state'] = self._state
              self._device_state_attributes = values
              _LOGGER.debug( values )
            except Exception as e:
                self.status = 3
                _LOGGER.error(f'exception: {e}')
                #print(traceback.format_exc())
                values['_state'] = self._state
                self._device_state_attributes = values

            _LOGGER.debug( "_state: " + str(self._state) )

            # tell HA there is new data
            self.async_schedule_update_ha_state()
            await asyncio.sleep(self._scan_interval)

    @property
    def name(self):
        """Return the name of the sensor."""

        return self._name

    @property
    def should_poll(self):
        """Return the polling state."""

        return False

    @property
    def icon(self):
        """Return the icon to use in the frontend."""

        return ICON

#    @property
##    def unit_of_measurement(self):
#        """Return the unit of measurement of this entity."""
#        return "W"

    @property
    def unique_id(self):
        """Get uniq id."""

        return self._name


# This base class shows the common properties and methods for a sensor as used in this
# example. See each sensor for further details about properties and methods that
# have been overridden.
class SensorBase(Entity):
    """Base representation of a Hello World Sensor."""

    should_poll = False

    def __init__(self, roller):
        """Initialize the sensor."""

        _LOGGER.debug("SensorBase")
        self._roller = roller

    # To link this entity to the cover device, this property must return an
    # identifiers value matching that used in the cover, but no other information such
    # as name. If name is returned, this entity will then also become a device in the
    # HA UI.
    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {"identifiers": {(DOMAIN, self._roller.roller_id)}}

    # This property is important to let HA know if this entity is online or not.
    # If an entity is offline (return False), the UI will refelect this.
    @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return self._roller.online and self._roller.hub.online

    async def async_added_to_hass(self):
        """Run when this Entity has been added to HA."""
        # Sensors should also register callbacks to HA when their state changes
        self._roller.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._roller.remove_callback(self.async_write_ha_state)

class EnergySensor(SensorBase):
    """Representation of a Sensor."""

    # The class of this device. Note the value should come from the homeassistant.const
    # module. More information on the available devices classes can be seen here:
    # https://developers.home-assistant.io/docs/core/entity/sensor
    device_clasync_added_to_hassass = DEVICE_CLASS_ENERGY
    instrument = None
    # The unit of measurement for this entity. As it's a DEVICE_CLASS_ENERGY, this
    # should be PERCENTAGE. A number of units are supported by HA, for some
    # examples, see:
    # https://developers.home-assistant.io/docs/core/entity/sensor#available-device-classes
    _attr_unit_of_measurement = ENERGY_KILO_WATT_HOUR

    def __init__(self, roller):
        """As per the sensor, this must be a unique value within this domain. This is done by using the device ID, and appending "_ENERGY"."""
        super().__init__(roller)
        _LOGGER.debug("__init__")
        self._attr_unique_id = f"{self._roller.roller_id}_energy"

        # The name of the entity
        self._attr_name = f"{self._roller.name} energy"
        _LOGGER.debug("random")
        _LOGGER.debug( self._roller.name )
        _LOGGER.debug(self)
        _LOGGER.debug(roller)
#        _LOGGER.debug( roller.get_device() )
        #_LOGGER.debug(roller.data)
#        self._state = random.randint(0, 1000)
       # _LOGGER.debug("=============================================================")

    async def async_added_to_hass(self):
        """async_added_to_hass."""
        _LOGGER.debug("added to hass, starting loop")
        loop = self.hass.loop
        #task =
        loop.create_task(self.solaredge_modbus_loop())

    async def solaredge_modbus_loop(self):
        """solaredge_modbus_loop."""

        while True:
#            values['test'] = 'test'
            try:
        #      _LOGGER.debug("=============================================================")
        #      _LOGGER.debug("========== !!!!!!!!!!!!!!!!!!!!!!!!!!!!! ====================")
        #      _LOGGER.debug(self)
        #      _LOGGER.debug( self._roller.name )
#              _LOGGER.debug( self._roller.get_value() )
#              serial = hass.data.get( "path" )
         #     _LOGGER.debug( self )
#              self.read_one_packet()
              self._state = self.state
              values['_state'] = self._state
              self._device_state_attributes = values
            except Exception as e:
                self.status = 7
                _LOGGER.error(f'exception: {e}')
                #print(traceback.format_exc())
                values['_state'] = self._state
                self._device_state_attributes = values

            # tell HA there is new data
            self.async_schedule_update_ha_state()
            await asyncio.sleep( CONF_SCAN_INTERVAL )

    # The value of this sensor. As this is a DEVICE_CLASS_ENERGY, this value must be
    # the ENERGY level as a percentage (between 0 and 100)
    @property
    def state(self):
        """state."""
        """Return the state of the sensor."""
        return self._roller.energy

#    @property
#    def unit_of_measurement(self):
#        """Return the unit of measurement of this entity."""
#        return "W"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity."""

        return 'W'

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._attr_name

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        ICON = "mdi:power-plug"
        return ICON

    #@property
    #def unit_of_measurement(self):
    #    """Return the unit of measurement of this entity."""
    #    return "W"

    @property
    def unique_id(self):
        """Unique id."""
        return self._attr_name

class BatterySensor(SensorBase):
    """Representation of a Sensor."""

    # The class of this device. Note the value should come from the homeassistant.const
    # module. More information on the available devices classes can be seen here:
    # https://developers.home-assistant.io/docs/core/entity/sensor
    device_class = DEVICE_CLASS_BATTERY

    # The unit of measurement for this entity. As it's a DEVICE_CLASS_BATTERY, this
    # should be PERCENTAGE. A number of units are supported by HA, for some
    # examples, see:
    # https://developers.home-assistant.io/docs/core/entity/sensor#available-device-classes
    #_attr_unit_of_measurement = PERCENTAGE

    def __init__(self, roller):
        """Init."""
        super().__init__(roller)

        # As per the sensor, this must be a unique value within this domain. This is done
        # by using the device ID, and appending "_battery"
        self._attr_unique_id = f"{self._roller.roller_id}_battery"

        # The name of the entity
        self._attr_name = f"{self._roller.name} Battery"

        self._state = random.randint(0, 100)

    # The value of this sensor. As this is a DEVICE_CLASS_BATTERY, this value must be
    # the battery level as a percentage (between 0 and 100)
    @property
    def state(self):
        """Return the state of the sensor."""
        return self._roller.battery_level


# This is another sensor, but more simple compared to the battery above. See the
# comments above for how each field works.
class IlluminanceSensor(SensorBase):
    """Representation of a Sensor."""

    device_class = DEVICE_CLASS_ILLUMINANCE
    _attr_unit_of_measurement = "lx"

    def __init__(self, roller):
        """Initialize the sensor."""
        super().__init__(roller)
        # As per the sensor, this must be a unique value within this domain. This is done
        # by using the device ID, and appending "_battery"
        self._attr_unique_id = f"{self._roller.roller_id}_illuminance"

        # The name of the entity
        self._attr_name = f"{self._roller.name} Illuminance"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._roller.illuminance
