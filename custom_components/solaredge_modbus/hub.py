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

from homeassistant.core import HomeAssistant
import logging
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

class Hub:
    """Hub for s0 5 channel."""

    manufacturer = "SOS 5-channel s0"
    _device = ""
    _instrument = None
    _lastupdate = 0
    _values = []
    def __init__(self, hass: HomeAssistant, name: str, device: str) -> None:
        """Init dummy hub."""
        self._name = name
        self._hass = hass
        self._device = device
        self._id = random.randint(1, 10000)
        _LOGGER.debug(self._device )
        _LOGGER.debug( self.get_device() )
        self.connection()
        self.rollers = [
            Roller(f"{self._id}_1", 1, f"{self._name} Port 1", self),
            Roller(f"{self._id}_2", 2, f"{self._name} Port 2", self),
            Roller(f"{self._id}_3", 3, f"{self._name} Port 3", self),
            Roller(f"{self._id}_4", 4, f"{self._name} Port 4", self),
            Roller(f"{self._id}_5", 5, f"{self._name} Port 5", self),
        ]
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
        self.model = "s0 port"

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
