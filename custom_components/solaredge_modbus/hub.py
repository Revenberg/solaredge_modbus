import asyncio
import logging
import threading
from collections import OrderedDict
from typing import Any, Dict, Optional

from homeassistant.core import HomeAssistant

from .rs485eth import Instrument

try:
    #from pymodbus.client import ModbusTcpClient
    #from pymodbus.constants import Endian
    from pymodbus.exceptions import ConnectionException, ModbusIOException
    #from pymodbus.payload import BinaryPayloadDecoder
    from pymodbus.pdu import ExceptionResponse, ModbusExceptions
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
        #if not self.is_socket_open():
        #    raise HubInitFailed(f"Could not 
        # open Modbus/TCP connection to {self._host}")

        #if self._adv_storage_control:
        #    _LOGGER.warning(
        #        (
        #            "Power Control Options: Storage Control is enabled. "
        #            "Use at your own risk!"
        #        ),
        #    )

        #if self._adv_site_limit_control:
        #    _LOGGER.warning(
        #        (
        #            "Power Control Options: Site Limit Control is enabled. "
        #            "Use at your own risk!"
        #        ),
        #    )

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

        #if not self.is_socket_open():
        #    self._online = False
        #    raise DataUpdateFailed(
        #        f"Could not open Modbus/TCP connection to {self._host}"
        #    )

        #else:
        self._online = True
        try:
            for inverter in self.inverters:
                await self._hass.async_add_executor_job(inverter.read_modbus_data)
        #        for meter in self.meters:
        #            await self._hass.async_add_executor_job(meter.read_modbus_data)
        #        for battery in self.batteries:
        #            await self._hass.async_add_executor_job(battery.read_modbus_data)

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
                                      eth_port=self._port, debug=False)
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

    #def read_holding_registers(self, unit, address, count):
    #    """Read holding registers."""
    #    with self._lock:
    #        kwargs = {"slave": unit} if unit else {}
    #        return self._client.read_holding_registers(address, count, **kwargs)

    def _write_registers(self):
        """Write registers."""
        with self._lock:
            kwargs = {"slave": self._wr_unit} if self._wr_unit else {}
            return self._client.write_registers(
                self._wr_address, self._wr_payload, **kwargs
            )

    async def write_registers(self, unit, address, payload):
        self._wr_unit = unit
        self._wr_address = address
        self._wr_payload = payload

        if not self.is_socket_open():
            await self.connect()

        try:
            result = await self._hass.async_add_executor_job(self._write_registers)

        except ConnectionException as e:
            _LOGGER.error(f"Write command failed: {e}")
            self._online = False
            ##await self.disconnect()

        else:
            if result.isError():
                if type(result) is ModbusIOException:
                    _LOGGER.error("Write command failed: No response from device.")
                    self._online = False
                    ##await self.disconnect()

                elif type(result) is ExceptionResponse:
                    if result.exception_code == ModbusExceptions.IllegalAddress:
                        _LOGGER.error(
                            (
                                "Write command failed: "
                                f"Illegal address {hex(self._wr_address)}"
                            ),
                        )
                        self._online = False
                        ##await self.disconnect()

                else:
                    raise ModbusWriteError(result)

        if self._sleep_after_write > 0:
            _LOGGER.debug(f"Sleeping {self._sleep_after_write} seconds after write.")
            await asyncio.sleep(self._sleep_after_write)


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
        #inverter_data = self.hub.read_holding_registers(
        #    unit=self.inverter_unit_id, address=40000, count=4
        #)
        #if inverter_data.isError():
        #    _LOGGER.debug(f"Inverter {self.inverter_unit_id}: {inverter_data}")
        

        #    if type(inverter_data) is ModbusIOException:
        #        raise DeviceInvalid(
        #            f"No response from inverter ID {self.inverter_unit_id}"
        #        )

        #    if type(inverter_data) is ExceptionResponse:
        #        if inverter_data.exception_code == ModbusExceptions.IllegalAddress:
        #            raise DeviceInvalid(
        #                f"ID {self.inverter_unit_id} is not a SunSpec inverter."
        #            )

        #    raise ModbusReadError(inverter_data)

        #decoder = BinaryPayloadDecoder.fromRegisters(
        #    inverter_data.registers, byteorder=Endian.Big
        #)

        #decoded_ident = OrderedDict(
        #    [
        #        ("C_SunSpec_ID", decoder.decode_32bit_uint()),
        #        ("C_SunSpec_DID", decoder.decode_16bit_uint()),
        #        ("C_SunSpec_Length", decoder.decode_16bit_uint()),
        #    ]
        #)

        #for name, value in iter(decoded_ident.items()):
        #    _LOGGER.debug(
        #        (
        #            f"Inverter {self.inverter_unit_id}: "
        #            f"{name} {hex(value) if isinstance(value, int) else value}"
        #        ),
        #    )

        #if (
        #    decoded_ident["C_SunSpec_ID"] == SunSpecNotImpl.UINT32
        #    or decoded_ident["C_SunSpec_DID"] == SunSpecNotImpl.UINT16
        #    or decoded_ident["C_SunSpec_ID"] != 0x53756E53
        #    or decoded_ident["C_SunSpec_DID"] != 0x0001
        #    or decoded_ident["C_SunSpec_Length"] != 65
        #):
        #    raise DeviceInvalid(
        #        f"ID {self.inverter_unit_id} is not a SunSpec inverter."
        #    )

        #inverter_data = self.hub.read_holding_registers(
        #    unit=self.inverter_unit_id, address=40004, count=65
        #)
        #if inverter_data.isError():
        #    _LOGGER.debug(f"Inverter {self.inverter_unit_id}: {inverter_data}")
        #    raise ModbusReadError(inverter_data)

        #decoder = BinaryPayloadDecoder.fromRegisters(
        #    inverter_data.registers, byteorder=Endian.Big
        #)

        #self.decoded_common = OrderedDict(
        #    [
        #        (
        #            "C_Manufacturer",
        #            parse_modbus_string(decoder.decode_string(32)),
        #        ),
        #        ("C_Model", parse_modbus_string(decoder.decode_string(32))),
        #        ("C_Option", parse_modbus_string(decoder.decode_string(16))),
        #        ("C_Version", parse_modbus_string(decoder.decode_string(16))),
        #        (
        #            "C_SerialNumber",
        #            parse_modbus_string(decoder.decode_string(32)),
        #        ),
        #        ("C_Device_address", decoder.decode_16bit_uint()),
        #    ]
        #)

        #for name, value in iter(self.decoded_common.items()):
        #    _LOGGER.debug(
        #        (
        #            f"Inverter {self.inverter_unit_id}: "
        #            f"{name} {hex(value) if isinstance(value, int) else value}"
        #        ),
        #    )

        #self.hub.inverter_common[self.inverter_unit_id] = self.decoded_common

        #mmppt_common = self.hub.read_holding_registers(
        #    unit=self.inverter_unit_id, address=40121, count=9
        #)
        #if mmppt_common.isError():
        #    _LOGGER.debug(f"Inverter {self.inverter_unit_id} MMPPT: {mmppt_common}")

        #    if type(mmppt_common) is ModbusIOException:
        #        raise ModbusReadError(
        #            f"No response from inverter ID {self.inverter_unit_id}"
        #        )

        #    elif type(mmppt_common) is ExceptionResponse:
        #        if mmppt_common.exception_code == ModbusExceptions.IllegalAddress:
        #            _LOGGER.debug(
        #                f"Inverter {self.inverter_unit_id} is NOT Multiple MPPT"
        #            )
        #            self.decoded_mmppt = None

        #    else:
        #        raise ModbusReadError(mmppt_common)

        #else:
        #    decoder = BinaryPayloadDecoder.fromRegisters(
        #        mmppt_common.registers, byteorder=Endian.Big
        #    )

        #    self.decoded_mmppt = OrderedDict(
        #        [
        #            ("mmppt_DID", decoder.decode_16bit_uint()),
        #            ("mmppt_Length", decoder.decode_16bit_uint()),
        #            ("ignore", decoder.skip_bytes(12)),
        #            ("mmppt_Units", decoder.decode_16bit_uint()),
        #        ]
        #    )

        #    try:
        #        del self.decoded_mmppt["ignore"]
        #    except KeyError:
        #        pass

        #    for name, value in iter(self.decoded_mmppt.items()):
        #        _LOGGER.debug(
        #            (
        #                f"Inverter {self.inverter_unit_id} MMPPT: "
        #                f"{name} {hex(value) if isinstance(value, int) else value}"
        #            ),
        #        )

        #    if (
        #        self.decoded_mmppt["mmppt_DID"] == SunSpecNotImpl.UINT16
        #        or self.decoded_mmppt["mmppt_Units"] == SunSpecNotImpl.UINT16
        #        or self.decoded_mmppt["mmppt_DID"] not in [160]
        #        or self.decoded_mmppt["mmppt_Units"] not in [2, 3]
        #    ):
        #        _LOGGER.debug(f"Inverter {self.inverter_unit_id} is NOT Multiple MPPT")
        #        self.decoded_mmppt = None

        #    else:
        #        _LOGGER.debug(f"Inverter {self.inverter_unit_id} is Multiple MPPT")

        #self.hub.mmppt_common[self.inverter_unit_id] = self.decoded_mmppt

        #self.manufacturer = self.decoded_common["C_Manufacturer"]
        self.manufacturer = "SolarEdge"
        #self.model = self.decoded_common["C_Model"]
        self.model = "SolarEdge"
        #self.option = self.decoded_common["C_Option"]
        #self.fw_version = self.decoded_common["C_Version"]
        self.fw_version = 1234
        #self.serial = self.decoded_common["C_SerialNumber"]
        self.serial = 1234
        #self.device_address = self.decoded_common["C_Device_address"]
        self.device_address = 1234
        #self.name = f"{self.hub.hub_id.capitalize()} I{self.inverter_unit_id}"
        self.uid_base = "1234"

        self._device_info = {
            "identifiers": {(DOMAIN, "1234")},
            "name": "SolarEdge RS485",
            "manufacturer": "SolarEdge",
            "model": self.model,
            "sw_version": self.fw_version,
            #"hw_version": self.option,
        }
        
    def getValueLong(self, addr, numberOfDecimals=0, functioncode=0, signed=False):
        rc = self.hub._client.read_long(addr, functioncode=functioncode, signed=signed)
        return rc

    def getValueRegister(self, addr, numberOfDecimals=0, functioncode=0, signed=False):
        rc = self.hub._client.read_register(addr, numberOfDecimals=numberOfDecimals, 
                                            functioncode=functioncode, signed=signed)
        return rc

    def getValueString(self, addr, functioncode=3, number_of_registers=4):
        rc = self.hub._client.read_string(addr, functioncode=functioncode)
        return rc

    def round(self, floatval):
        return round(floatval, 2)
    
    def read_modbus_data(self) -> None:
        _LOGGER.debug("read_modbus_data")
        #inverter_data = self.hub.read_holding_registers(
        #    unit=self.inverter_unit_id, address=40069, count=40
        #)
        #if inverter_data.isError():
        #    _LOGGER.debug(f"Inverter {self.inverter_unit_id}: {inverter_data}")
        #    raise ModbusReadError(inverter_data)

        #decoder = BinaryPayloadDecoder.fromRegisters(
        #    inverter_data.registers, byteorder=Endian.Big
        #)

        # https://ginlongsolis.freshdesk.com/helpdesk/attachments/36112313359

        self.decoded_model = OrderedDict(
            [
                ("C_SunSpec_DID", self.getValueRegister(3000, functioncode=4, 
                                        signed=False)),
                ("AC_output_type", self.getValueRegister(3003, functioncode=4, 
                                        signed=False)),
                ("DC_input_type", self.getValueRegister(3004, functioncode=4, 
                                        signed=False)),
                
#                ("C_SunSpec_DID", decoder.decode_16bit_uint()),
#                ("C_SunSpec_Length", decoder.decode_16bit_uint()),
                ("AC_Current", self.getValueRegister(3005, functioncode=4, 
                                        signed=False)),
                ("AC_Current_A", self.getValueRegister(3036, numberOfDecimals=1, 
                                        functioncode=4, signed=False)),
                ("AC_Current_B", self.getValueRegister(3037, numberOfDecimals=1, 
                                        functioncode=4, signed=False)),
                ("AC_Current_C", self.getValueRegister(3038, numberOfDecimals=1, 
                                        functioncode=4, signed=False)),
                ("AC_Voltage_AB", self.getValueRegister(3033, numberOfDecimals=1,
                                        functioncode=4, signed=False)),
                ("AC_Voltage_BC", self.getValueRegister(3034, numberOfDecimals=1, 
                                        functioncode=4, signed=False)),
                ("AC_Voltage_CA", self.getValueRegister(3035, numberOfDecimals=1, 
                                        functioncode=4, signed=False)),
                ("DC_Voltage_1", self.getValueRegister(3031, numberOfDecimals=1, 
                                        functioncode=4, signed=False)),
                ("DC_Current_1", self.getValueRegister(3022, functioncode=4, 
                                        signed=False)),
                ("DC_Voltage_2", self.getValueRegister(3023, numberOfDecimals=1, 
                                        functioncode=4, signed=False)),
                ("DC_Current_2", self.getValueRegister(3024, functioncode=4, 
                                        signed=False)),

#                ("AC_Voltage_AN", decoder.decode_16bit_uint()),
#                ("AC_Voltage_BN", decoder.decode_16bit_uint()),
#                ("AC_Voltage_CN", decoder.decode_16bit_uint()),
#                ("AC_Voltage_SF", decoder.decode_16bit_int()),
                ("AC_Power", self.getValueLong(3004, functioncode=4, 
                                               signed=False)),
#                ("AC_Power_SF", decoder.decode_16bit_int()),
                ("AC_Frequency", self.getValueRegister(3042, numberOfDecimals=2, 
                                                functioncode=4, signed=False)),
                
#                ("AC_VA", decoder.decode_16bit_int()),
#                ("AC_VA_SF", decoder.decode_16bit_int()),
#                ("AC_var", decoder.decode_16bit_int()),
#                ("AC_var_SF", decoder.decode_16bit_int()),
#                ("AC_PF", decoder.decode_16bit_int()),
#                ("AC_PF_SF", decoder.decode_16bit_int()),
#                ("AC_Energy_WH", decoder.decode_32bit_uint()),
#                ("AC_Energy_WH_SF", decoder.decode_16bit_uint()),
#                ("I_DC_Current", decoder.decode_16bit_uint()),
#                ("I_DC_Current_SF", decoder.decode_16bit_int()),
#                ("I_DC_Voltage", decoder.decode_16bit_uint()),
#                ("I_DC_Voltage_SF", decoder.decode_16bit_int()),
                ("I_DC_Power", self.getValueRegister(3007, functioncode=4, 
                                                signed=False)),
#                ("I_DC_Power_SF", decoder.decode_16bit_int()),
#                ("I_Temp_Cab", decoder.decode_16bit_int()),
                ("I_Temp_Sink", self.getValueRegister(3041, numberOfDecimals=1, 
                                                functioncode=4, signed=True)),
#                ("I_Temp_Trns", decoder.decode_16bit_int()),
#                ("I_Temp_Other", decoder.decode_16bit_int()),
#                ("I_Temp_SF", decoder.decode_16bit_2int()),
#                ("I_Status", decoder.decode_16bit_int()),
                ("I_Status", 3),
                ("I_Status_Vendor", 3),
                ("SN_1", self.getValueString(3061, functioncode=3)),
                ("SN_2", self.getValueString(3062, functioncode=3)),
                ("SN_3", self.getValueString(3063, functioncode=3)),
                ("SN_4", self.getValueString(3064, functioncode=3)),
            ]
        )

        _LOGGER.debug(f"Inverter: {self.decoded_model}")
        #if (
        #    self.decoded_model["C_SunSpec_DID"] == SunSpecNotImpl.UINT16
        #    or self.decoded_model["C_SunSpec_DID"] not in [101, 102, 103]
        #    or self.decoded_model["C_SunSpec_Length"] != 50
        #):
        #    raise DeviceInvalid(f"Inverter {self.inverter_unit_id} not usable.")

        #""" Multiple MPPT Extension """
        #if self.decoded_mmppt is not None:
        #    if self.decoded_mmppt["mmppt_Units"] == 2:
        #        mmppt_registers = 48

        #    elif self.decoded_mmppt["mmppt_Units"] == 3:
        #        mmppt_registers = 68

        #    else:
        #        self.decoded_mmppt = None
        #        raise DeviceInvalid(
        #            f"Inverter {self.inverter_unit_id} MMPPT must be 2 or 3 units"
        #        )

        #    inverter_data = self.hub.read_holding_registers(
        #        unit=self.inverter_unit_id, address=40123, count=mmppt_registers
        #    )
        #    if inverter_data.isError():
        #        _LOGGER.debug(f"Inverter {self.inverter_unit_id}: {inverter_data}")
        #        raise ModbusReadError(inverter_data)

        #    decoder = BinaryPayloadDecoder.fromRegisters(
        #        inverter_data.registers, byteorder=Endian.Big
        #    )

        #    if self.decoded_mmppt["mmppt_Units"] in [2, 3]:
        #        self.decoded_model.update(
        #            OrderedDict(
        #                [
        #                    ("mmppt_DCA_SF", decoder.decode_16bit_int()),
        #                    ("mmppt_DCV_SF", decoder.decode_16bit_int()),
        #                    ("mmppt_DCW_SF", decoder.decode_16bit_int()),
        #                    ("mmppt_DCWH_SF", decoder.decode_16bit_int()),
        #                    ("mmppt_Events", decoder.decode_32bit_uint()),
        #                    ("ignore", decoder.skip_bytes(2)),
        #                    ("mmppt_TmsPer", decoder.decode_16bit_uint()),
        #                    ("mmppt_0_ID", decoder.decode_16bit_uint()),
        #                    (
        #                        "mmppt_0_IDStr",
        #                        parse_modbus_string(decoder.decode_string(16)),
        #                    ),
        #                    ("mmppt_0_DCA", decoder.decode_16bit_uint()),
        #                    ("mmppt_0_DCV", decoder.decode_16bit_uint()),
        #                    ("mmppt_0_DCW", decoder.decode_16bit_uint()),
        #                    ("mmppt_0_DCWH", decoder.decode_32bit_uint()),
        #                    ("mmppt_0_Tms", decoder.decode_32bit_uint()),
        #                    ("mmppt_0_Tmp", decoder.decode_16bit_int()),
        #                    ("mmppt_0_DCSt", decoder.decode_16bit_uint()),
        #                    ("mmppt_0_DCEvt", decoder.decode_32bit_uint()),
        #                    ("mmppt_1_ID", decoder.decode_16bit_uint()),
        #                    (
        #                        "mmppt_1_IDStr",
        #                        parse_modbus_string(decoder.decode_string(16)),
        #                    ),
        #                    ("mmppt_1_DCA", decoder.decode_16bit_uint()),
        #                    ("mmppt_1_DCV", decoder.decode_16bit_uint()),
        #                    ("mmppt_1_DCW", decoder.decode_16bit_uint()),
        #                    ("mmppt_1_DCWH", decoder.decode_32bit_uint()),
        #                    ("mmppt_1_Tms", decoder.decode_32bit_uint()),
        #                    ("mmppt_1_Tmp", decoder.decode_16bit_int()),
        #                    ("mmppt_1_DCSt", decoder.decode_16bit_uint()),
        #                    ("mmppt_1_DCEvt", decoder.decode_32bit_uint()),
        #                ]
        #            )
        #        )

        #    if self.decoded_mmppt["mmppt_Units"] in [3]:
        #        self.decoded_model.update(
        #            OrderedDict(
        #                [
        #                    ("mmppt_2_ID", decoder.decode_16bit_uint()),
        #                    (
        #                        "mmppt_2_IDStr",
        #                        parse_modbus_string(decoder.decode_string(16)),
        #                    ),
        #                    ("mmppt_2_DCA", decoder.decode_16bit_uint()),
        #                    ("mmppt_2_DCV", decoder.decode_16bit_uint()),
        #                    ("mmppt_2_DCW", decoder.decode_16bit_uint()),
        #                    ("mmppt_2_DCWH", decoder.decode_32bit_uint()),
        #                    ("mmppt_2_Tms", decoder.decode_32bit_uint()),
        #                    ("mmppt_2_Tmp", decoder.decode_16bit_int()),
        #                    ("mmppt_2_DCSt", decoder.decode_16bit_uint()),
        #                    ("mmppt_2_DCEvt", decoder.decode_32bit_uint()),
        #                ]
        #            )
        #        )

        #    try:
        #        del self.decoded_model["ignore"]
        #    except KeyError:
        #        pass

        #""" Global Dynamic Power Control and Status """
        #if self.global_power_control is True or self.global_power_control is None:
        #    inverter_data = self.hub.read_holding_registers(
        #        unit=self.inverter_unit_id, address=61440, count=4
        #    )
        #    if inverter_data.isError():
        #        _LOGGER.debug(f"Inverter {self.inverter_unit_id}: {inverter_data}")

        #        if type(inverter_data) is ModbusIOException:
        #            raise ModbusReadError(
        #                f"No response from inverter ID {self.inverter_unit_id}"
        #            )

        #        if type(inverter_data) is ExceptionResponse:
        #            if inverter_data.exception_code == ModbusExceptions.IllegalAddress:
        #                self.global_power_control = False
        #                _LOGGER.debug(
        #                    (
        #                        f"Inverter {self.inverter_unit_id}: "
        #                        "global power control NOT available"
        #                    )
        #                )

        #        if self.global_power_control is not False:
        #            raise ModbusReadError(inverter_data)

        #    else:
        #        decoder = BinaryPayloadDecoder.fromRegisters(
        #            inverter_data.registers,
        #            byteorder=Endian.Big,
        #            wordorder=Endian.Little,
        #        )

        #        self.decoded_model.update(
        #            OrderedDict(
        #                [
        #                    ("I_RRCR", decoder.decode_16bit_uint()),
        #                    ("I_Power_Limit", decoder.decode_16bit_uint()),
        #                    ("I_CosPhi", decoder.decode_32bit_float()),
        #                ]
        #            )
        #        )
        #        self.global_power_control = True

        #""" Power Control Options """
        #if self.advanced_power_control is True or self.advanced_power_control is None:
        #    inverter_data = self.hub.read_holding_registers(
        #        unit=self.inverter_unit_id, address=61762, count=2
        #    )
        #    if inverter_data.isError():
        #        _LOGGER.debug(f"Inverter {self.inverter_unit_id}: {inverter_data}")

        #        if type(inverter_data) is ModbusIOException:
        #            raise ModbusReadError(
        #                f"No response from inverter ID {self.inverter_unit_id}"
        #            )

        #        if type(inverter_data) is ExceptionResponse:
        #            if inverter_data.exception_code == ModbusExceptions.IllegalAddress:
        #                self.advanced_power_control = False
        #                _LOGGER.debug(
        #                    (
        #                        f"Inverter {self.inverter_unit_id}: "
        #                        "advanced power control NOT available"
        #                    )
        #                )

        #        if self.advanced_power_control is not False:
        #            raise ModbusReadError(inverter_data)

        #    else:
        #        decoder = BinaryPayloadDecoder.fromRegisters(
        #            inverter_data.registers, byteorder=Endian.Big
        #        )

        #        self.decoded_model.update(
        #            OrderedDict(
        #                [
        #                    ("I_AdvPwrCtrlEn", decoder.decode_32bit_int()),
        #                ]
        #            )
        #        )
        #        self.advanced_power_control = True

        #""" Site Limit Control """
        #if self.site_limit_control is True or self.site_limit_control is None:
        #    inverter_data = self.hub.read_holding_registers(
        #        unit=self.inverter_unit_id, address=57344, count=4
        #    )
        #    if inverter_data.isError():
        #        _LOGGER.debug(f"Inverter {self.inverter_unit_id}: {inverter_data}")

        #        if type(inverter_data) is ModbusIOException:
        #            raise ModbusReadError(
        #                f"No response from inverter ID {self.inverter_unit_id}"
        #            )

        #        if type(inverter_data) is ExceptionResponse:
        #            if inverter_data.exception_code == ModbusExceptions.IllegalAddress:
        #                self.site_limit_control = False
        #                _LOGGER.debug(
        #                    (
        #                        f"Inverter {self.inverter_unit_id}: "
        #                        "site limit control NOT available"
        #                    )
        #                )

        #        if self.site_limit_control is not False:
        #            raise ModbusReadError(inverter_data)

        #    else:
        #        self.site_limit_control = True

        #        decoder = BinaryPayloadDecoder.fromRegisters(
        #            inverter_data.registers,
        #            byteorder=Endian.Big,
        #            wordorder=Endian.Little,
        #        )

        #        self.decoded_model.update(
        #            OrderedDict(
        #                [
        #                    ("E_Lim_Ctl_Mode", decoder.decode_16bit_uint()),
        #                    ("E_Lim_Ctl", decoder.decode_16bit_uint()),
        #                    ("E_Site_Limit", decoder.decode_32bit_float()),
        #                ]
        #            )
        #        )

        #    """ External Production Max Power """
        #    inverter_data = self.hub.read_holding_registers(
        #        unit=self.inverter_unit_id, address=57362, count=2
        #    )
        #    if inverter_data.isError():
        #        _LOGGER.debug(f"Inverter {self.inverter_unit_id}: {inverter_data}")

        #        if type(inverter_data) is ModbusIOException:
        #            raise ModbusReadError(
        #                f"No response from inverter ID {self.inverter_unit_id}"
        #            )

        #        if type(inverter_data) is ExceptionResponse:
        #            if inverter_data.exception_code == ModbusExceptions.IllegalAddress:
        #                try:
        #                    del self.decoded_model["Ext_Prod_Max"]
        #                except KeyError:
        #                    pass

        #                _LOGGER.debug(
        #                    (
        #                        f"Inverter {self.inverter_unit_id}: "
        #                        "Ext_Prod_Max NOT available"
        #                    )
        #                )

        #        if self.site_limit_control is not False:
        #            raise ModbusReadError(inverter_data)

        #    else:
        #        decoder = BinaryPayloadDecoder.fromRegisters(
        #            inverter_data.registers,
        #            byteorder=Endian.Big,
        #            wordorder=Endian.Little,
        #        )

        #        self.decoded_model.update(
        #            OrderedDict(
        #                [
        #                    ("Ext_Prod_Max", decoder.decode_32bit_float()),
        #                ]
        #            )
        #        )

        #for name, value in iter(self.decoded_model.items()):
        #    if isinstance(value, float):
        #        display_value = float_to_hex(value)
        #    else:
        #        display_value = hex(value) if isinstance(value, int) else value
        #    _LOGGER.debug(f"Inverter {self.inverter_unit_id}: {name} {display_value}")

        #""" Power Control Options: Storage Control """
        #if self.hub.option_storage_control is True and self.decoded_storage 
        # is not None:
        #    for battery in self.hub.batteries:
        #        if self.inverter_unit_id != battery.inverter_unit_id:
        #            continue

        #        inverter_data = self.hub.read_holding_registers(
        #            unit=self.inverter_unit_id, address=57348, count=14
        #        )
        #        if inverter_data.isError():
        #            _LOGGER.debug(f"Inverter {self.inverter_unit_id}: {inverter_data}")

        #            if type(inverter_data) is ModbusIOException:
        #                raise ModbusReadError(
        #                    f"No response from inverter ID {self.inverter_unit_id}"
        #                )

        #            if type(inverter_data) is ExceptionResponse:
        #                if (
        #                    inverter_data.exception_code
        #                    == ModbusExceptions.IllegalAddress
        #                ):
        #                    self.decoded_storage = False
        #                    _LOGGER.debug(
        #                        (
        #                            f"Inverter {self.inverter_unit_id}: "
        #                            "storage control NOT available"
        #                        )
        #                    )

        #            if self.decoded_storage is not None:
        #                raise ModbusReadError(inverter_data)

        #        decoder = BinaryPayloadDecoder.fromRegisters(
        #            inverter_data.registers,
        #            byteorder=Endian.Big,
        #            wordorder=Endian.Little,
        #        )

        #        self.decoded_storage = OrderedDict(
        #            [
        #                ("control_mode", decoder.decode_16bit_uint()),
        #                ("ac_charge_policy", decoder.decode_16bit_uint()),
        #                ("ac_charge_limit", decoder.decode_32bit_float()),
        #                ("backup_reserve", decoder.decode_32bit_float()),
        #                ("default_mode", decoder.decode_16bit_uint()),
        #                ("command_timeout", decoder.decode_32bit_uint()),
        #                ("command_mode", decoder.decode_16bit_uint()),
        #                ("charge_limit", decoder.decode_32bit_float()),
        #                ("discharge_limit", decoder.decode_32bit_float()),
        #            ]
        #        )

        #        for name, value in iter(self.decoded_storage.items()):
        #            if isinstance(value, float):
        #                display_value = float_to_hex(value)
        #            else:
        #                display_value = hex(value) if isinstance(value, int) else 
        # value
        #            _LOGGER.debug(
        #                f"Inverter {self.inverter_unit_id}: {name} {display_value}"
        #            )

    async def write_registers(self, address, payload):
        """Write inverter register."""
        await self.hub.write_registers(self.inverter_unit_id, address, payload)

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

