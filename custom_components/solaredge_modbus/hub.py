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
        number_of_inverters: int = 1,
        start_device_id: int = 1,
        detect_meters: bool = True,
        detect_batteries: bool = False,
        keep_modbus_open: bool = False,
        advanced_power_control: bool = False,
        adv_storage_control: bool = False,
        adv_site_limit_control: bool = False,
        allow_battery_energy_reset: bool = False,
        sleep_after_write: int = 3,
        battery_rating_adjust: int = 0,
    ):
        """Initialize the Modbus hub."""
        self._hass = hass
        self._name = name
        self._host = host
        self._port = port
        self._detect_meters = detect_meters
        self._detect_batteries = detect_batteries
        self._keep_modbus_open = keep_modbus_open
        self._advanced_power_control = advanced_power_control
        self._adv_storage_control = adv_storage_control
        self._adv_site_limit_control = adv_site_limit_control
        self._allow_battery_energy_reset = allow_battery_energy_reset
        self._sleep_after_write = sleep_after_write
        self._battery_rating_adjust = battery_rating_adjust
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

        _LOGGER.debug(
            (
                f"{DOMAIN} configuration: "
                f"detect_meters={self._detect_meters}, "
                f"detect_batteries={self._detect_batteries}, "
                f"keep_modbus_open={self._keep_modbus_open}, "
                f"advanced_power_control={self._advanced_power_control}, "
                f"adv_storage_control={self._adv_storage_control}, "
                f"adv_site_limit_control={self._adv_site_limit_control}, "
                f"allow_battery_energy_reset={self._allow_battery_energy_reset}, "
                f"sleep_after_write={self._sleep_after_write}, "
                f"battery_rating_adjust={self._battery_rating_adjust}, "
            ),
        )

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

        _LOGGER.debug(f"inverters: {self.inverters}")
        try:
            for inverter in self.inverters:
                _LOGGER.debug(f"inverter: {inverter}")
                await self._hass.async_add_executor_job(inverter.read_modbus_data)
            _LOGGER.debug("---------------------2---------------------")

        except ModbusReadError as e:
            #await self.disconnect()
            _LOGGER.debug("--------------------------3----------------")
            raise HubInitFailed(f"Read error: {e}")

        except DeviceInvalid as e:
            #await self.disconnect()
            _LOGGER.debug("---------------------------4---------------")
            raise HubInitFailed(f"Invalid device: {e}")

        except ConnectionException as e:
            #await self.disconnect()
            _LOGGER.debug("-------------------------------5-----------")
            raise HubInitFailed(f"Connection failed: {e}")

        self.initalized = True

    async def async_refresh_modbus_data(self, _now: Optional[int] = None) -> bool:
        if not self.is_socket_open():
            await self.connect()

        if not self.initalized:
            try:
                await self._async_init_solaredge()

            except ConnectionException as e:
                #await self.disconnect()
                raise HubInitFailed(f"Setup failed: {e}")

        self._online = True
        try:
            for inverter in self.inverters:
                await self._hass.async_add_executor_job(inverter.read_modbus_data)

        except ModbusReadError as e:
            self._online = False
        #        #await self.disconnect()
            raise DataUpdateFailed(f"Update failed: {e}")

        except DeviceInvalid as e:
            self._online = False
                #if not self._keep_modbus_open:
                    #await self.disconnect()
            raise DataUpdateFailed(f"Invalid device: {e}")

        except ConnectionException as e:
            self._online = False
                #await self.disconnect()
            raise DataUpdateFailed(f"Connection failed: {e}")

        #if not self._keep_modbus_open:
            #await self.disconnect()

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

    @property
    def option_storage_control(self) -> bool:
        return self._adv_storage_control

    @property
    def option_export_control(self) -> bool:
        return self._adv_site_limit_control

    @property
    def keep_modbus_open(self) -> bool:
        return self._keep_modbus_open

    @property
    def allow_battery_energy_reset(self) -> bool:
        return self._allow_battery_energy_reset

    @property
    def battery_rating_adjust(self) -> int:
        return (self._battery_rating_adjust + 100) / 100

    @keep_modbus_open.setter
    def keep_modbus_open(self, value: bool) -> None:
        if value is True:
            self._keep_modbus_open = True
        else:
            self._keep_modbus_open = False

        _LOGGER.debug(f"keep_modbus_open={self._keep_modbus_open}")

    @property
    def coordinator_timeout(self) -> int:
        _LOGGER.debug(f"coordinator timeout is {self._coordinator_timeout}")
        return self._coordinator_timeout

#    async def disconnect(self) -> None:
#        """Disconnect modbus client."""
        #if self._client is not None:
        #    await self._hass.async_add_executor_job(self._client.close)
#        x = 1
#        x = x + 1

    async def connect(self) -> None:
        """Connect modbus client."""
        #with self._lock:
        if self._client is None:
            self._client = Instrument(eth_address=self._host,
                                      eth_port=self._port)
            # self._client = ModbusTcpClient(host=self._host, port=self._port)

            #await self._hass.async_add_executor_job(self._client.connect)

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
    def __init__(self, device_id: int, hub: SolarEdgeModbusMultiHub) -> None:
        self.inverter_unit_id = device_id
        self.hub = hub
        self.decoded_common = []
        self.decoded_model = []
        self.decoded_mmppt = []
        self.decoded_storage = []
        self.has_parent = False
        self.global_power_control = None
        self.advanced_power_control = None
        self.site_limit_control = None
        self.manufacturer = "SolarEdge"
               
    def init_device(self) -> None:
        
        _LOGGER.debug("init_device")
        self.read_modbus_data_common()
                
        #self.manufacturer = self.decoded_common["C_Manufacturer"]
        self.manufacturer = "SolarEdge"
        #self.model = self.decoded_common["C_Model"]
        self.model = "Solis RS485"
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

    def getValueLong(self, addr, signed=False):
        return self.hub._client._generic_command(
            registeraddress=addr,
            number_of_registers=2,
            signed=signed,
            byteorder=0,
            payloadformat="long",
        )

    def getValueRegister(self, addr, numberOfDecimals=0, signed=False):
        return self.hub._client._generic_command(
            registeraddress=addr,
            numberOfDecimals=numberOfDecimals,
            number_of_registers=1,
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
        _LOGGER.debug("read_modbus_data")

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
                ("SN", self.getValueRegister(3062, signed=False)),
                
            ]
        )

    def read_modbus_data(self) -> None:
        _LOGGER.debug("read_modbus_data")

        # https://ginlongsolis.freshdesk.com/helpdesk/attachments/36112313359

        self.decoded_model = OrderedDict(
            [
                ("AC_Power", self.getValueLong(3005, 
                                               signed=False)),
                ("AC_Current", self.getValueRegister(3006, 
                                        signed=False)),
                ("I_DC_Power", self.getValueRegister(3008, 
                                                signed=False)),
                
                ("AC_Energy_WH",  self.getValueRegister(3009, 
                                                    signed=False)),
                
                ("ac_lifetimeproduction", self.getValueLong(3008, 
                                                    signed=False)),
                
                ("ac_monthenergy",  self.getValueRegister(3011, 
                                                    signed=False)),
                ("ac_lastmonth",  self.getValueRegister(3013, 
                                                    signed=False)),
                ("ac_yearenergy",  self.getValueRegister(3017, 
                                                    signed=False)),
                ("ac_lastyear",  self.getValueRegister(3019, 
                                                    signed=False)),
                
                ("generatedtoday", self.getValueRegister(3014, numberOfDecimals=1,
                                              signed=False)),
                ("generatedyesterday", self.getValueRegister(3015, numberOfDecimals=1,
                                                    signed=False)),
                ("ac_power_output", self.getValueLong(3004,  
                                                    signed=False)),
                
                ("DC_Voltage_1", self.getValueRegister(3021, numberOfDecimals=1,
                                        signed=False)),
                ("DC_Current_1", self.getValueRegister(3022, 
                                        signed=False)),
                ("DC_Voltage_2", self.getValueRegister(3023, numberOfDecimals=1,
                                         signed=False)),
                ("DC_Current_2", self.getValueRegister(3024, 
                                        signed=False)),
                ("AC_Voltage_AB", self.getValueRegister(3033, numberOfDecimals=1,
                                         signed=False)),
                ("AC_Voltage_BC", self.getValueRegister(3034, numberOfDecimals=1,
                                         signed=False)),
                ("AC_Voltage_CA", self.getValueRegister(3035, numberOfDecimals=1,
                                         signed=False)),
                ("AC_Current_A", self.getValueRegister(3036, numberOfDecimals=1,
                                         signed=False)),
                ("AC_Current_B", self.getValueRegister(3037, numberOfDecimals=1,
                                         signed=False)),
                ("AC_Current_C", self.getValueRegister(3038, numberOfDecimals=1,
                                         signed=False)),
                ("I_Temp_Sink", self.getValueRegister(3041, numberOfDecimals=1,
                                                 signed=True)),
                ("AC_Frequency", self.getValueRegister(3042, numberOfDecimals=2,
                                                 signed=False)),
                ("I_Status", 3),
                ("I_Status_Vendor", 3),
            ]
        )
        _LOGGER.debug(f"Inverter: {self.decoded_common}")
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
