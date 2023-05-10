"""Sensor SolarEdge."""
#import datetime
import asyncio
#import traceback

#from time import sleep

from datetime import timedelta
import logging

from homeassistant.const import CONF_SCAN_INTERVAL

from homeassistant.helpers.entity import Entity

from . import DOMAIN as SOLAREDGE_DOMAIN

#from homeassistant.helpers.entity import generate_entity_id

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.WARN)

ICON = "mdi:power-plug"
SCAN_INTERVAL = timedelta(seconds=60)

values = {}
meter1_values = {}

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Async_setup_platform."""
    if discovery_info is None:
        return

    _LOGGER.debug("fetching modbus client")
    instrument = hass.data.get(SOLAREDGE_DOMAIN)
    scan_interval = discovery_info[CONF_SCAN_INTERVAL]

    async_add_entities([SolarEdgeModbusSensor(instrument, scan_interval)], True)


class SolarEdgeModbusSensor(Entity):
    """Solar EdgeModbus Sensor."""

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
        #task =
        loop.create_task(self.modbus_loop())

    async def modbus_loop(self):
        """Modbus_loop."""
        _LOGGER.debug("modbus_loop")
        while True:
            try:
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
        """Unique Id."""
        return "SolarEdge"
