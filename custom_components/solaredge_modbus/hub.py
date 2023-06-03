import logging
import threading
from collections import OrderedDict
from typing import Any, Dict, Optional

from homeassistant.core import HomeAssistant

from .rs485eth import Instrument

try:
    #from pymodbus.client import ModbusTcpClient
    #from pymodbus.constants import Endian
    from pymodbus.exceptions import ConnectionException
    ##, ModbusIOException
    #from pymodbus.payload import BinaryPayloadDecoder
    ## from pymodbus.pdu import ExceptionResponse, ModbusExceptions
except ImportError:
    raise ImportError("pymodbus is not installed, or pymodbus version is not supported")

from .const import DOMAIN
#, SunSpecNotImpl
#from .helpers import float_to_hex, parse_modbus_string

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

class SolarEdgeException(Exception):
    """Base class for other exceptions"""

    pass


class HubInitFailed(SolarEdgeException):
    """Raised when an error happens during init"""

    pass


class DeviceInitFailed(SolarEdgeException):
    """Raised when a device can't be initialized"""

    pass

class ModbusReadError(SolarEdgeException):
    """Raised when a modbus read fails"""

    pass


class ModbusWriteError(SolarEdgeException):
    """Raised when a modbus write fails"""

    pass


class DataUpdateFailed(SolarEdgeException):
    """Raised when an update cycle fails"""

    pass


class DeviceInvalid(SolarEdgeException):
    """Raised when a device is not usable or invalid"""

    pass


class SolarEdgeModbusMultiHub:
    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        host: str,
        port: int,
#        number_of_inverters: int = 1,
#        start_device_id: int = 1,
#        adv_storage_control: bool = False,
#        adv_site_limit_control: bool = False,
#        allow_battery_energy_reset: bool = False,
        #sleep_after_write: int = 3,
        #battery_rating_adjust: int = 0,
    ):
        """Initialize the Modbus hub."""
        self._hass = hass
        self._name = name
        self._host = host
        self._port = port
#        self._adv_storage_control = adv_storage_control
#        self._adv_site_limit_control = adv_site_limit_control
#        self._allow_battery_energy_reset = allow_battery_energy_reset
#        self._sleep_after_write = sleep_after_write
#        self._battery_rating_adjust = battery_rating_adjust
        self._lock = threading.Lock()
        self._id = name.lower()
        self._coordinator_timeout = 30
        self._client = None
        self._id = name.lower()
        self._lock = threading.Lock()
        self.inverters = []
        self.meters = []
        self.batteries = []
        self.inverter_common = {}
        self.mmppt_common = {}

        self._wr_unit = None
        self._wr_address = None
        self._wr_payload = None

        self.initalized = False
        self._online = False

    async def _async_init_solaredge(self) -> None:
        inverter_unit_id = 1

        try:
            new_inverter = SolarEdgeInverter(inverter_unit_id, self)
            await self._hass.async_add_executor_job(new_inverter.init_device)
            self.inverters.append(new_inverter)

        except ModbusReadError as e:
            ##await self.disconnect()
            _LOGGER.debug("---------------1---------------------------")
            raise HubInitFailed(f"{e}")

        except DeviceInvalid as e:
            """Inverters are required"""
            _LOGGER.error(f"Inverter device ID {inverter_unit_id}: {e}")
            raise HubInitFailed(f"{e}")

        try:
            for inverter in self.inverters:
                await self._hass.async_add_executor_job(inverter.read_modbus_data)

        except ModbusReadError as e:
            self._online = False
            raise HubInitFailed(f"Read error: {e}")

        except DeviceInvalid as e:
            self._online = False
            raise HubInitFailed(f"Invalid device: {e}")

        except ConnectionException as e:
            self._online = False
            raise HubInitFailed(f"Connection failed: {e}")

        self.initalized = True

    async def async_refresh_modbus_data(self, _now: Optional[int] = None) -> bool:
        if not self.is_socket_open():
            await self.connect()

        if not self.initalized:
            try:
                await self._async_init_solaredge()

            except ConnectionException as e:
                raise HubInitFailed(f"Setup failed: {e}")

        self._online = True
        try:
            for inverter in self.inverters:
                await self._hass.async_add_executor_job(inverter.read_modbus_data)

        except ModbusReadError as e:
            self._online = False
            raise DataUpdateFailed(f"Update failed: {e}")

        except DeviceInvalid as e:
            self._online = False
            raise DataUpdateFailed(f"Invalid device: {e}")

        except ConnectionException as e:
            self._online = False
            raise DataUpdateFailed(f"Connection failed: {e}")

        return True

    @property
    def online(self):
        return self._online

    @property
    def name(self):
        """Return the name of this hub."""
        return self._name

    @property
    def hub_id(self) -> str:
        return self._id

#    @property
#    def option_storage_control(self) -> bool:
#        return self._adv_storage_control

#    @property
#    def option_export_control(self) -> bool:
#        return self._adv_site_limit_control

#    @property
#    def allow_battery_energy_reset(self) -> bool:
#        return self._allow_battery_energy_reset

#    @property
#    def battery_rating_adjust(self) -> int:
#        return (self._battery_rating_adjust + 100) / 100

    @property
    def coordinator_timeout(self) -> int:
        _LOGGER.debug(f"coordinator timeout is {self._coordinator_timeout}")
        return self._coordinator_timeout

    async def connect(self) -> None:
        """Connect modbus client."""
        if self._client is None:
            self._client = Instrument(eth_address=self._host,
                                      eth_port=self._port)

    def is_socket_open(self) -> bool:
#        """Check modbus client connection status."""
        #with self._lock:
        if self._client is None:
            return False

        return True

    async def shutdown(self) -> None:
        """Shut down the hub."""
        self._online = False
        # #await self.disconnect()
        self._client = None

class SolarEdgeInverter:
    _delta_energy = 0
    def __init__(self, device_id: int, hub: SolarEdgeModbusMultiHub) -> None:
        self.inverter_unit_id = device_id
        self.hub = hub
        self.decoded_common = []
        self.decoded_model = []
        self.decoded_mmppt = []
        self.decoded_storage = []
        self.has_parent = False
        self.global_power_control = None
#        self.site_limit_control = None
        self.manufacturer = "SolarEdge"
        self._delta_energy = 0

    def init_device(self) -> None:

        _LOGGER.debug("init_device")
        self.read_modbus_data_common()

        #self.manufacturer = self.decoded_common["C_Manufacturer"]
        self.manufacturer = "SolarEdge"
        #self.model = self.decoded_common["C_Model"]
        self.model = "SolarEdge RS485"
        #self.option = self.decoded_common["C_Option"]
        #self.fw_version = self.decoded_common["C_Version"]

        self.fw_version = self.decoded_common["C_SunSpec_DID"]
        #self.serial = self.decoded_common["C_SerialNumber"]
        self.serial = self.decoded_common["SN"]
        self.device_address = f"{self.hub._host}:{self.hub._port}"

        #self.name = f"{self.hub.hub_id.capitalize()} I{self.inverter_unit_id}"
        self.uid_base = f"{self.hub.hub_id.capitalize()} I"
        + self.decoded_common["C_SunSpec_DID"]

        self._device_info = {
            "identifiers": {(DOMAIN, int(self.decoded_common["C_SunSpec_DID"]))},
            "name": self.device_address,
            "manufacturer": "SolarEdge",
            "model": self.model,
            "sw_version": self.fw_version,
            #"hw_version": self.option,
        }

    def getValueLong(self, addr, signed=False,
                     numberOfDecimals=6):
        #_LOGGER.debug("getValueLong")
        #_LOGGER.debug(addr)
        return self.hub._client._generic_command(
            registeraddress=addr,
            numberOfDecimals=numberOfDecimals,
            number_of_registers=2,
            signed=signed,
            byteorder=0,
            payloadformat="long",
        )

    def getValueInt(self, addr, signed=False,
                     numberOfDecimals=1):
        #_LOGGER.debug("getValueInt")
        #_LOGGER.debug(addr)
        return self.hub._client._generic_command(
            registeraddress=addr,
            numberOfDecimals=numberOfDecimals,
            number_of_registers=1,
            signed=signed,
            byteorder=1,
            payloadformat="int",
        )
        
    def getValueRegister(self, addr, numberOfDecimals=0,
                         signed=False, number_of_registers=1):
        return self.hub._client._generic_command(
            registeraddress=addr,
            numberOfDecimals=numberOfDecimals,
            number_of_registers=number_of_registers,
            signed=signed,
            payloadformat="register",
        )

#    def getValueString(self, addr, functioncode=3, number_of_registers=4):
#        return self.hub._client._generic_command(
#            functioncode=functioncode,
#            registeraddress=addr,
#            number_of_registers=number_of_registers,
#            payloadformat="string",
#        )

    def round(self, floatval):
        return round(floatval, 2)

    def read_modbus_data_common(self) -> None:
        #_LOGGER.debug("read_modbus_data")

        try:
            C_SunSpec_DID = self.getValueRegister(3000,
                                        signed=False)

        except ConnectionException as e:
            _LOGGER.error(f"Connection error: {e}")
            self._online = False
            raise ModbusReadError(f"{e}")

        self.decoded_common = OrderedDict(
            [
                ("C_SunSpec_DID", C_SunSpec_DID),
                ("SN", self.getValueRegister(3062)),
            ]
        )

    def read_modbus_data(self) -> None:
        # _LOGGER.debug("read_modbus_data")

        # https://ginlongsolis.freshdesk.com/helpdesk/attachments/36112313359

        self.decoded_model = OrderedDict(
            [
                ("ac_power_output", self.getValueLong(3004) * 1000), # 3005

                ("dc_output_power", self.getValueLong(3006) * 1000), # 3007
                ("ac_generated_lifetimeproduction", 
                                    self.getValueLong(3008) * 1000000), # 3009
                ("ac_energy_wh",  self.getValueLong(3009)),
                ("ac_generated_monthenergy",  self.getValueLong(3011)), # 3011
                ("ac_generated_lastmonth",  self.getValueLong(3013)), # 3013
                ("ac_generated_yearenergy",  self.getValueLong(3017)), # 3017
                ("ac_generated_lastyear",  self.getValueLong(3019)), # 3019

                ("ac_generated_today", self.getValueInt(3014) /10), # 3015
                ("ac_generated_yesterday", self.getValueInt(3015) / 10), # 3016
                ("dc_voltage_1", self.getValueInt(3021)), # 3022 U16
                ("dc_current_1", self.getValueInt(3022)), # 3023 U16
                ("dc_voltage_2", self.getValueInt(3023)), # 3024 U16
                ("dc_current_2", self.getValueInt(3024)), # 3025 U16
                ("ac_voltage_ab", self.getValueInt(3033)), # 3034 U16
                ("ac_voltage_bc", self.getValueInt(3034)), # 3035 U16
                ("ac_voltage_ca", self.getValueInt(3035)), # 3036 U16
                ("ac_current_a", self.getValueInt(3036)), # 3037 U16
                ("ac_current_b", self.getValueInt(3037)), # 3038 U16
                ("ac_current_c", self.getValueInt(3038)), # 3039 U16
                ("i_temp_sink", self.getValueInt(3041, signed=True)), # 3042 U16
                ("ac_frequency", self.getValueInt(3042, numberOfDecimals=2)), # 3043 U16
                ("i_status",  self.getValueInt(3071, numberOfDecimals=0)), # 3072 U16
                ("i_status_vendor",  self.getValueInt(3043, 
                                                      numberOfDecimals=0)), # 3044 U16
            ]
        )

        self.hub._online = True
#        _LOGGER.debug(f"Inverter: {self.decoded_common}")
        _LOGGER.debug(f"Inverter: {self.decoded_model}")

    @property
    def online(self) -> bool:
        """Device is online."""
        return self.hub.online

    @property
    def device_info(self) -> Optional[Dict[str, Any]]:
        return self._device_info

    @property
    def is_mmppt(self) -> bool:
        if self.decoded_mmppt is None:
            return False

        return True
