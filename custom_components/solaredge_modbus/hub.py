"""A demonstration 'hub' that connects several devices."""
from __future__ import annotations

# In a real implementation, this would be in an external library that's on PyPI.
# The PyPI package needs to be included in the `requirements` section of manifest.json
# See https://developers.home-assistant.io/docs/creating_integration_manifest
# for more information.
# This dummy hub always returns 5 rollers.
import asyncio
import random
import serial
import datetime
from .rs485eth import Instrument

from homeassistant.core import HomeAssistant
import logging
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

class Hub:
    """Solaredge modbus."""

    manufacturer = "Solaredge modbus"
    _device = ""
    _instrument = None
    _lastupdate = 0
    _values = []
    def __init__(self, hass: HomeAssistant, name: str, device: str, host: str, port: str) -> None:
        """Init solaredge."""
        self._name = name
        self._host = host
        self._post = port
        self._hass = hass
        self._device = device
        self._id = random.randint(1, 10000)
        _LOGGER.debug(self._device )
        _LOGGER.debug( self.get_device() )
        self.connection()

        SolarEdgeModbusSensor(self._instrument, 60)

#        self.rollers = [
#            Roller(f"{self._id}", 1, f"{self._name}", self),
#            ]

        self.online = True

    def get_device(self) -> str:
        """Get device."""
        _LOGGER.debug("get_device" )
        _LOGGER.debug( self._device )
        return self._device

    @property
    def hub_id(self) -> str:
        """ID for dummy hub."""
        return self._id

    def connect(self):
        """Connect to device."""
        if not self._instrument.isOpen():
            self._instrument.open()
            self._instrument.setRTS(False)

    def disconnect(self):
        """Disconnect device."""
        if self._instrument.isOpen():
            self._instrument.close()

    def connected(self):
        """Is connect to device."""
        return self._instrument.isOpen()

    def get_value(self, id: int) -> float:
          """Get data."""
          now = datetime.datetime.now()
          current = (now.hour * 100) +  now.minute
          if ( self._lastupdate != current):
            try:
              line = self._instrument.readline()
            except Exception as e:
              _LOGGER.error(f'exception: {e}')
              #print(traceback.format_exc())
            #_LOGGER.debug("==================== line =========================================")
            _LOGGER.info(line)
            #_LOGGER.debug("=============================================================")
            _LOGGER.info(line.decode("utf-8") )
            values = line.decode("utf-8").split(":")
            _LOGGER.info(values[1])
            _LOGGER.info(values[6])
            _LOGGER.info(values[9])
            _LOGGER.info(values[12])
            _LOGGER.info(values[15])
            _LOGGER.info(values[18])
            _LOGGER.info( values )
            self._values = [ values[1], values[6], values[9], values[11], values[15], values[18] ]
            self._lastupdate = current

            #_LOGGER.info("end--------------------------------------------------")
          _LOGGER.debug( self._values[id] )
          return self._values[id]

    def connection(self):
        """Test connectivity is OK."""
        instrument = Instrument(self._host, self._port, 1, debug=False)
        
        BAUDRATE = 9600
        self._instrument = serial.Serial(
                  self._device,
                  BAUDRATE,
                  timeout=10,
                  bytesize=serial.SEVENBITS,
                  parity=serial.PARITY_EVEN,
                  stopbits=serial.STOPBITS_ONE
          )

class Roller:
    """Dummy roller (device for HA) for Hello World example."""

    hub = None
    _hubid = 0
    def __init__(self, rollerid: str, hubid: int, name: str, myhub: Hub) -> None:
        """Init dummy roller."""
#        _LOGGER.debug("!@!@!@!@ Roller")
        self._id = rollerid
        self._hubid = hubid
        self.hub = myhub
#        _LOGGER.debug( hubid )
        myhub.get_device()
#        _LOGGER.debug( "-----------" )
#        _LOGGER.debug( myhub.get_device() )
#        _LOGGER.debug( "-----------" )
#        _LOGGER.debug( self.hub.get_device() )
        self.name = name
        self._callbacks = set()
        self._loop = asyncio.get_event_loop()
        self._target_position = 100
        self._current_position = 100
        # Reports if the roller is moving up or down.
        # >0 is up, <0 is down. This very much just for demonstration.
        self.moving = 0

        # Some static information about this device
        self.firmware_version = "0.0.1"
        self.model = "Solaredge modbus"

    def get_device(self) -> str:
        """Return dev from hub for roller."""
        _LOGGER.debug("--------------------------------")
        return self.hub.get_device()

    @property
    def roller_id(self) -> str:
        """Return ID for roller."""
        return self._id

    @property
    def position(self):
        """Return position for roller."""
        return self._current_position

    async def set_position(self, position: int) -> None:
        """Set dummy cover to the given position.

        State is announced a random number of seconds later.
        """
        self._target_position = position

        # Update the moving status, and broadcast the update
        self.moving = position - 50
        await self.publish_updates()

        self._loop.create_task(self.delayed_update())

    async def delayed_update(self) -> None:
        """Publish updates, with a random delay to emulate interaction with device."""
        await asyncio.sleep(random.randint(1, 10))
        self.moving = 0
        await self.publish_updates()

#    def register_callback(self, callback: Callable[[], None]) -> None:
#        """Register callback, called when Roller changes state."""
#        self._callbacks.add(callback)

#    def remove_callback(self, callback: Callable[[], None]) -> None:
#        """Remove previously registered callback."""
#        self._callbacks.discard(callback)

    # In a real implementation, this library would call it's call backs when it was
    # notified of any state changeds for the relevant device.
    async def publish_updates(self) -> None:
        """Schedule call all registered callbacks."""
        self._current_position = self._target_position
        for callback in self._callbacks:
            callback()

    @property
    def online(self) -> float:
        """Roller is online."""
        # The dummy roller is offline about 10% of the time. Returns True if online,
        # False if offline.
        return True # random.random() > 0.1

    @property
    def battery_level(self) -> int:
        """Battery level as a percentage."""
        return random.randint(0, 100)

    @property
    def battery_voltage(self) -> float:
        """Return a random voltage roughly that of a 12v battery."""
        return round(random.random() * 3 + 10, 2)

#    @property
#    def illuminance(self) -> int:
#        """Return a sample illuminance in lux."""
#        return random.randint(0, 500)

    @property
    def energy(self) -> int:
        """Return a sample energy in Kwh."""
        return self.hub.get_value(self._hubid)

class SolarEdgeModbusSensor(Entity):
    """SolarEdgeModbusSensor."""

    def __init__(self, instrument, scan_interval):
        """Init."""

        _LOGGER.debug("creating modbus sensor")
        #self.entity_id = generate_entity_id("sensor.{}", "SolarEdgeModbusSensor")

        self._instrument = instrument
        self._scan_interval = scan_interval
        self._state = 0
        self._device_state_attributes = {}

    def getValueLong(self, addr, numberOfDecimals=0, functioncode=0, signed=False):
        """GetValueLong."""

        rc = self._instrument.read_long(addr, functioncode=functioncode, signed=signed)
        return rc

    def getValueRegister(self, addr, numberOfDecimals=0, functioncode=0, signed=False):
        """GetValueRegister."""

        rc = self._instrument.read_register(addr, numberOfDecimals=numberOfDecimals, functioncode=functioncode, signed=signed)
        return rc

    def round(self, floatval):
        """Round."""
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
        """Async_added_to_hass."""

        _LOGGER.debug("added to hass, starting loop")
        loop = self.hass.loop
        loop.create_task(self.modbus_loop())

    async def modbus_loop(self):
        """Modbus_loop."""

        _LOGGER.debug("modbus_loop")
        while True:
            try:
                values = []
                values['ac_lifetimeproduction'] = self.getValueLong(3008, functioncode=4, signed=False) # Read All Time Energy (KWH Total) as Unsigned 32-Bit
                values['generatedtoday'] = self.getValueRegister(3014, numberOfDecimals=1, functioncode=4, signed=False) # Read Today Energy (KWH Total) as 16-Bit
                values['generatedyesterday'] = self.getValueRegister(3015, numberOfDecimals=1, functioncode=4, signed=False) # Read Today Energy (KWH Total) as 16-Bit
                values['ac_power_output'] = self.getValueLong(3004, functioncode=4, signed=False)

                values['dc_voltage1'] = self.getValueRegister(3021, numberOfDecimals=1, functioncode=4, signed=False)
                values['dc_current1'] = self.getValueRegister(3022, functioncode=4, signed=False)
                values['dc_voltage2'] = self.getValueRegister(3023, numberOfDecimals=1, functioncode=4, signed=False)
                values['dc_current2'] = self.getValueRegister(3024, functioncode=4, signed=False)

                values['ac_voltage_phase_a'] = self.getValueRegister(3033, numberOfDecimals=1,functioncode=4, signed=False)
                values['ac_voltage_phase_b'] = self.getValueRegister(3034, numberOfDecimals=1, functioncode=4, signed=False)
                values['ac_voltage_phase_c'] = self.getValueRegister(3035, numberOfDecimals=1, functioncode=4, signed=False)

                values['ac_current_phase_a'] = self.getValueRegister(3036, numberOfDecimals=1, functioncode=4, signed=False)
                values['ac_current_phase_b'] = self.getValueRegister(3037, numberOfDecimals=1, functioncode=4, signed=False)
                values['ac_current_phase_c'] = self.getValueRegister(3038, numberOfDecimals=1, functioncode=4, signed=False)

                values['ac_frequency'] = self.getValueRegister(3042, numberOfDecimals=2, functioncode=4, signed=False)
                values['heat_sink_temperature'] = self.getValueRegister(3041, numberOfDecimals=1, functioncode=4, signed=True)

                Realtime_DATA_yy = self.getValueRegister(3072, functioncode=4, signed=False) #Read Year
                Realtime_DATA_mm = self.getValueRegister(3073, functioncode=4, signed=False) #Read Month
                Realtime_DATA_dd = self.getValueRegister(3074, functioncode=4, signed=False) #Read Day
                Realtime_DATA_hh = self.getValueRegister(3075, functioncode=4, signed=False) #Read Hour
                Realtime_DATA_mi = self.getValueRegister(3076, functioncode=4, signed=False) #Read Minute
                Realtime_DATA_ss = self.getValueRegister(3077, functioncode=4, signed=False) #Read Second

                tms = "20" + str(Realtime_DATA_yy) + "-" + str(Realtime_DATA_mm) + "-" + str(Realtime_DATA_dd)
                tms = tms + " " + str(Realtime_DATA_hh) + ":" + str(Realtime_DATA_mi) + ':' + str(Realtime_DATA_ss)
                values['timestamp'] = tms

                values['ac_total_current'] = self.getValueRegister(3005, functioncode=4, signed=False)
                values['pvpower'] = self.getValueRegister(3007, functioncode=4, signed=False)
                values['ac_totalenergy'] = self.getValueRegister(3009, functioncode=4, signed=False)
                values['ac_monthenergy'] = self.getValueRegister(3011, functioncode=4, signed=False)
                values['ac_lastmonth'] = self.getValueRegister(3013, functioncode=4, signed=False)
                values['ac_yearenergy'] = self.getValueRegister(3017, functioncode=4, signed=False)
                values['ac_lastyear'] = self.getValueRegister(3019, functioncode=4, signed=False)

                #debug-print entire dictionary
                #for x in values.keys():
                #    _LOGGER.debug(x +" => " + str(values[x]))

                # Skip if increamenting counter has gone to 0, or become too large, this happens on inverter startup

                validValue = values['ac_lifetimeproduction'] > 0

                if validValue:
                    #main state is power production, other values can be fetched as attributes
                    self._state = 4
                    values['_state'] = self._state
                    self._device_state_attributes = values

            except TimeoutError:
              _LOGGER.debug("Timeout")
              self._state = 2
              values['_state'] = self._state
              self._device_state_attributes = values
              _LOGGER.debug( values )
            except Exception as e:
                self.status = 7
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
        return "SolarEdge Modbus"

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return ICON

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity."""
        return "W"

    @property
    def unique_id(self):
        """Unique_id."""
        return "SolarEdge"

