"""Reading RS485 via ETH."""
#
#   Copyright 2023 Sander Revenberg
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import struct
#import sys
import socket
import logging
import binascii

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

#if sys.version > "3":
#import binascii

#if sys.version > "3":
long = int

#_ASCII_HEADER = ":"
#_ASCII_FOOTER = "\r\n"
#_BYTEPOSITION_FOR_ASCII_HEADER = 0  # Relative to plain response
_BYTEPOSITION_FOR_SLAVEADDRESS = 0  # Relative to (stripped) response

BYTEORDER_BIG = 0
BYTEORDER_LITTLE = 1
BYTEORDER_BIG_SWAP = 2
BYTEORDER_LITTLE_SWAP = 3

# Replace with enum when Python3 only
_PAYLOADFORMAT_LONG = "long"
_PAYLOADFORMAT_REGISTER = "register"
_PAYLOADFORMAT_REGISTERS = "registers"

# ######################## #
# Modbus instrument object #
# ######################## #


class Instrument:
    """Instrument class for talking to instruments (slaves).

    Uses the Modbus RTU or ASCII protocols (via RS485 or RS232).

    Args:
        port (str): The serial port name, for example ``/dev/ttyUSB0`` (Linux),
        ``/dev/tty.usbserial`` (OS X) or ``COM4`` (Windows).
        slaveaddress (int): Slave address in the range 1 to 247 (use decimal numbers,
        not hex). Address 0 is for broadcast, and 248-255 are reserved.
        close_port_after_each_call (bool): If the serial port should be closed after
        each call to the instrument.
        debug (bool): Set this to :const:`True` to print the communication details

    """

    def __init__(
        self,
        eth_address,
        eth_port,
        slaveaddress=1,
        close_port_after_each_call=False,
    ):
        self.address = slaveaddress
        self.precalculate_read_size = True
        self.clear_buffers_before_each_transaction = True
        self.close_port_after_each_call = close_port_after_each_call
        self.handle_local_echo = False
        self.eth_address = eth_address
        self.eth_port = eth_port

    def _generic_command(
        self,
        registeraddress,
        numberOfDecimals=0,
        number_of_registers=0,
        signed=False,
        byteorder=BYTEORDER_BIG,
        payloadformat=None,
    ):
        """Perform generic command for reading and writing registers and bits.

        Args:
            registeraddress (int): The register address (use decimal numbers, not hex).
            value (numerical or string or None or list of int): The value to store in
            the register. Depends on payloadformat.
            numberOfDecimals (int): The number of decimals for content conversion.
            Only for a single register.
            number_of_registers (int): The number of registers to read/write. Only
            certain values allowed, depends on payloadformat.
            number_of_bits (int):T he number of registers to read/write.
            signed (bool): Whether the data should be interpreted as unsigned or
            signed. Only for a single register or for payloadformat='long'.
            byteorder (int): How multi-register data should be interpreted.
            payloadformat (None or string): Any of the _PAYLOADFORMAT_* values

        Returns:
            The register data in numerical value (int or float), or the bit value 0 or
            1 (int), or ``None``.

        Raises:
            TypeError, ValueError, ModbusException,
            serial.SerialException (inherited from IOError)

        """
        # Create payload
        ps1 = _num_to_twobyte_string(registeraddress) 
        ps2 = _num_to_twobyte_string(number_of_registers)
        
        request = _embed_payload(
            self.address, f'{ps1}{ps2}'
        )

        # Communicate
        response = self._communicate(request)
        # Extract payload
        payload_from_slave = _extract_payload(
            response, self.address
        )
        
        # Parse response payload
        return _parse_payload(
            payload_from_slave,
            numberOfDecimals,
            number_of_registers,
            signed,
            byteorder,
            payloadformat,
        )

    def _communicate(self, request):
        """Talk to the slave via a serial port.

        Args:
            request (str): The raw request that is to be sent to the slave.
            
        Returns:
            The raw data (string) returned from the slave.

        Raises:
            TypeError, ValueError, ModbusException,
            serial.SerialException (inherited from IOError)

        """
        
        request = bytes(
            request, encoding="latin1"
        )  # Convert types to make it Python3 compatible

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        
        sock.connect((self.eth_address, self.eth_port))
        sock.send(request)
        answer = sock.recv(1024)
        sock.close()

#        if sys.version_info[0] > 2:
#            answer = str(answer, encoding="latin1")
        answer = str(answer, encoding="latin1")

        if not answer:
            raise NoResponseError("No communication with the instrument (no answer)")

        return answer

class ModbusException(IOError):
    """Base class for Modbus communication exceptions.

    Inherits from IOError, which is an alias for OSError in Python3.
    """

class MasterReportedException(ModbusException):
    """Base class for exceptions that the master (computer) detects."""

class NoResponseError(MasterReportedException):
    """No response from the slave."""

class InvalidResponseError(MasterReportedException):
    """The response does not fulfill the Modbus standad, for example wrong checksum."""

def _parse_payload(
    payload,
    numberOfDecimals,
    number_of_registers,
    signed,
    byteorder,
    payloadformat,
):
    registerdata = payload[1:]
    
    if payloadformat == _PAYLOADFORMAT_LONG:
        return _bytestring_to_long(
            registerdata, signed, number_of_registers, byteorder
        )

 #   if payloadformat == _PAYLOADFORMAT_REGISTERS:
 #       return _bytestring_to_valuelist(registerdata, number_of_registers)

#    el
    if payloadformat == _PAYLOADFORMAT_REGISTER:
        return _twobyte_string_to_num(
            registerdata, numberOfDecimals, signed=signed
        )

def _embed_payload(slaveaddress, payloaddata):
    """Build a request from the slaveaddress, the function code and the payload data.

    Args:
        slaveaddress (int): The address of the slave.
        
    Returns:
        The built (raw) request string for sending to the slave (including CRC etc).

    Raises:
        ValueError, TypeError.

    """

    first_part = (
        _num_to_onebyte_string(slaveaddress)
        + _num_to_onebyte_string(4)
        + payloaddata
    )
    request = first_part + _calculate_crc_string(first_part)

    return request

def _extract_payload(response, slaveaddress):
    """Extract the payload data part from the slave's response.

    Args:
        response (str): The raw response byte string from the slave.
        This is different for RTU and ASCII.
        slaveaddress (int): The adress of the slave. Used here for error checking only.
        
    Returns:
        The payload part of the *response* string. Conversion from Modbus ASCII
        has been done if applicable.

    Raises:
        ValueError, TypeError, ModbusException (or subclasses).

    Raises an exception if there is any problem with the received address,
    the 4 or the CRC.

    """
    MINIMAL_RESPONSE_LENGTH_RTU = 4    
    plainresponse = response

    # Validate response length
    if len(response) < MINIMAL_RESPONSE_LENGTH_RTU:
        raise InvalidResponseError(
            "Too short Modbus RTU response (minimum length "
            + f"{MINIMAL_RESPONSE_LENGTH_RTU} bytes). Response: {response!r}"
        )

    calculate_checksum = _calculate_crc_string
    number_of_checksum_bytes = 2

    received_checksum = response[-number_of_checksum_bytes:]
    response_without_checksum = response[0 : (len(response) - number_of_checksum_bytes)]
    calculated_checksum = calculate_checksum(response_without_checksum)

    if received_checksum != calculated_checksum:
        text = (
            f"Checksum error: {received_checksum!r} instead of "
            + f"{calculated_checksum!r} . The response "
            + f"is: {response!r} (plain response: {plainresponse!r})"
        )
        raise InvalidResponseError(text)

    # Check slave address
    responseaddress = ord(response[_BYTEPOSITION_FOR_SLAVEADDRESS])

    if responseaddress != slaveaddress:
        raise InvalidResponseError(
            f"Wrong return slave address: {responseaddress} instead of"
            + f" {slaveaddress}. "
            + f"The response is: {response!r}"
        )

    # Read data payload
    first_databyte_number = 2

    last_databyte_number = len(response) - 2

    payload = response[first_databyte_number:last_databyte_number]
    return payload

def _num_to_onebyte_string(inputvalue):
    """Convert a numerical value to a one-byte string.

    Args:
        inputvalue (int): The value to be converted. Should be >=0 and <=255.

    Returns:
        A one-byte string created by chr(inputvalue).

    Raises:
        TypeError, ValueError

    """

    return chr(inputvalue)

def _num_to_twobyte_string(value, numberOfDecimals=0, lsb_first=False, signed=False):
    r"""Convert a numerical value to a two-byte string, possibly scaling it.

    Args:
        value (float or int): The numerical value to be converted.
        numberOfDecimals (int): Number of decimals, 0 or more, for scaling.
        lsb_first (bool): Whether the least significant byte should be first
        in the resulting string.
        signed (bool): Whether negative values should be accepted.

    Returns:
        A two-byte string.

    Raises:
        TypeError, ValueError. Gives DeprecationWarning instead of ValueError
        for some values in Python 2.6.

    Use ``numberOfDecimals=1`` to multiply ``value`` by 10 before sending it to
    the slave register. Similarly ``numberOfDecimals=2`` will multiply ``value``
    by 100 before sending it to the slave register.

    Use the parameter ``signed=True`` if making a bytestring that can hold
    negative values. Then negative input will be automatically converted into
    upper range data (two's complement).

    The byte order is controlled by the ``lsb_first`` parameter, as seen here:

    ======================= ============= ====================================
    ``lsb_first`` parameter Endianness    Description
    ======================= ============= ====================================
    False (default)         Big-endian    Most significant byte is sent first
    True                    Little-endian Least significant byte is sent first
    ======================= ============= ====================================

    For example:
        To store for example value=77.0, use ``numberOfDecimals = 1`` if the
        register will hold it as 770 internally. The value 770 (dec) is 0302 (hex),
        where the most significant byte is 03 (hex) and the least significant byte
        is 02 (hex). With ``lsb_first = False``, the most significant byte is given
        first
        why the resulting string is ``\x03\x02``, which has the length 2.

    """
    multiplier = 10 ** numberOfDecimals
    integer = int(float(value) * multiplier)

    if lsb_first:
        formatcode = "<"  # Little-endian
    else:
        formatcode = ">"  # Big-endian
    if signed:
        formatcode += "h"  # (Signed) short (2 bytes)
    else:
        formatcode += "H"  # Unsigned short (2 bytes)

    outstring = _pack(formatcode, integer)
    assert len(outstring) == 2
    return outstring

def _twobyte_string_to_num(bytestring, numberOfDecimals=0, signed=False):
    r"""Convert a two-byte string to a numerical value, possibly scaling it.

    Args:
        bytestring (str): A string of length 2.
        numberOfDecimals (int): The number of decimals. Defaults to 0.
        signed (bol): Whether large positive values should be interpreted as negative
        values.

    Returns:
        The numerical value (int or float) calculated from the ``bytestring``.

    Raises:
        TypeError, ValueError

    Use the parameter ``signed=True`` if converting a bytestring that can hold
    negative values. Then upper range data will be automatically converted into
    negative return values (two's complement).

    Use ``numberOfDecimals=1`` to divide the received data by 10 before returning
    the value. Similarly ``numberOfDecimals=2`` will divide the received data by
    100 before returning the value.

    The byte order is big-endian, meaning that the most significant byte is sent first.

    """
    formatcode = ">"  # Big-endian
    if signed:
        formatcode += "h"  # (Signed) short (2 bytes)
    else:
        formatcode += "H"  # Unsigned short (2 bytes)

    fullregister = _unpack(formatcode, bytestring)

    if numberOfDecimals == 0:
        return fullregister
    divisor = 10 ** numberOfDecimals
    return fullregister / float(divisor)

def _bytestring_to_long(
    bytestring, signed=False, number_of_registers=2, byteorder=BYTEORDER_BIG
):
    """Convert a bytestring to a long integer.

    Long integers (32 bits = 4 bytes) are stored in two consecutive 16-bit registers
    in the slave.

    Args:
        bytestring (str): A string of length 4.
        signed (bol): Whether large positive values should be interpreted as
        negative values.
        number_of_registers (int): Should be 2. For error checking only.
        byteorder (int): How multi-register data should be interpreted.

    Returns:
        The numerical value (int).

    Raises:
        ValueError, TypeError

    """

    if byteorder in [BYTEORDER_BIG, BYTEORDER_BIG_SWAP]:
        formatcode = ">"
    else:
        formatcode = "<"
    if signed:
        formatcode += "l"  # (Signed) long (4 bytes)
    else:
        formatcode += "L"  # Unsigned long (4 bytes)

    if byteorder in [BYTEORDER_BIG_SWAP, BYTEORDER_LITTLE_SWAP]:
        bytestring = _swap(bytestring)
    return _unpack(formatcode, bytestring)

#def _bytestring_to_valuelist(bytestring, number_of_registers):
#    """Convert a bytestring to a list of numerical values.

#    The bytestring is interpreted as 'unsigned INT16'.

#    Args:
#        bytestring (str): The string from the slave. Length = 2*number_of_registers
#        number_of_registers (int): The number of registers. For error checking.

#    Returns:
#        A list of integers.

#    Raises:
#        TypeError, ValueError

#    """
#    values = []
#    for i in range(number_of_registers):
#        offset = 2 * i
#        substring = bytestring[offset : (offset + 2)]
#        values.append(_twobyte_string_to_num(substring))

#    return values

def _pack(formatstring, value):
    """Pack a value into a bytestring.

    Uses the built-in :mod:`struct` Python module.

    Args:
        formatstring (str): String for the packing. See the :mod:`struct`
        module for details.
        value (depends on formatstring): The value to be packed

    Returns:
        A bytestring (str).

    Raises:
        ValueError

    Note that the :mod:`struct` module produces byte buffers for Python3,
    but bytestrings for Python2. This is compensated for automatically.

    """

    try:
        result = struct.pack(formatstring, value)
    except Exception:
        errortext = (
            "The value to send is probably out of range, as the num-to-bytestring "
        )
        errortext += f"conversion failed. Value: {value!r} "
        + f"Struct format code is: {formatstring}"
        raise ValueError(errortext)

#    if sys.version_info[0] > 2:
    return str(
        result, encoding="latin1"
    )  # Convert types to make it Python3 compatible
 #   return result

def _unpack(formatstring, packed):
    """Unpack a bytestring into a value.

    Uses the built-in :mod:`struct` Python module.

    Args:
        formatstring (str): String for the packing. See the :mod:`struct`
        module for details.
        packed (str): The bytestring to be unpacked.

    Returns:
        A value. The type depends on the formatstring.

    Raises:
        ValueError

    Note that the :mod:`struct` module wants byte buffers for Python3,
    but bytestrings for Python2. This is compensated for automatically.

    """

    #if sys.version_info[0] > 2:
    packed = bytes(
        packed, encoding="latin1"
    )  # Convert types to make it Python3 compatible

    try:
        value = struct.unpack(formatstring, packed)[0]
    except Exception:
        errortext1 = "The received bytestring is probably wrong, as the "
        errortext2 = f"bytestring-to-num  conversion failed. Bytestring: {packed!r} "
        errortext3 = f"Struct format code is: {formatstring}"
        
        raise InvalidResponseError(f"{errortext1}{errortext2}{errortext3}")

    return value

def _swap(bytestring):
    """Swap characters pairwise in a string.

    This corresponds to a "byte swap".

    Args:
        bytestring (str): input. The length should be an even number.

    Return the string with characters swapped.

    """
    length = len(bytestring)
    if length % 2:
        raise ValueError(
            f"The length of the bytestring should be even. Given {bytestring!r}."
        )
    templist = list(bytestring)
    templist[1:length:2], templist[:length:2] = (
        templist[:length:2],
        templist[1:length:2],
    )
    return "".join(templist)

#def _hexencode(bytestring, insert_spaces=False):
#    """Convert a byte string to a hex encoded string.

#    For example 'J' will return '4A', and ``'\x04'`` will return '04'.

#    Args:
#        bytestring (str): Can be for example ``'A\x01B\x45'``.
#        insert_spaces (bool): Insert space characters between pair of characters
#        to increase readability.

#    Returns:
#        A string of twice the length, with characters in the range '0' to '9' and
#        'A' to 'F'. The string will be longer if spaces are inserted.

#    Raises:
#        TypeError, ValueError

#    """
#    separator = "" if not insert_spaces else " "

#    # Use plain string formatting instead of binhex.hexlify,
#    # in order to have it Python 2.x and 3.x compatible

#    byte_representions = []
#    for char in bytestring:
#        byte_representions.append(f"{ord(char):02X}")
#    return separator.join(byte_representions).strip()

#def _hexdecode(hexstring):
#    """Convert a hex encoded string to a byte string.

#    For example '4A' will return 'J', and '04' will return ``'\x04'`` (which has
#    length 1).

#    Args:
#        hexstring (str): Can be for example 'A3' or 'A3B4'. Must be of even length.
#        Allowed characters are '0' to '9', 'a' to 'f' and 'A' to 'F' (not space).

#    Returns:
#        A string of half the length, with characters corresponding to all 0-255
#        values for each byte.

#    Raises:
#        TypeError, ValueError

#    """
#    # Note: For Python3 the appropriate would be: raise TypeError(new_error_message)
#    # from err but the Python2 interpreter will indicate SyntaxError.
#    # Thus we need to live with this warning in Python3:
#    # 'During handling of the above exception, another exception occurred'

#    if len(hexstring) % 2 != 0:
#        raise ValueError(
#            f"The input hexstring must be of even length. Given: {hexstring!r}"
#        )

#    #if sys.version_info[0] > 2:
#    converted_bytes = bytes(hexstring, "latin1")
#    try:
#        return str(binascii.unhexlify(converted_bytes), encoding="latin1")
#    except binascii.Error as err:
#        new_error_message = f"Hexdecode reported an error: {err.args[0]!s}. "
#        + f"Input hexstring: {hexstring}"
#        raise TypeError(new_error_message)

#    else:
#        try:
#            return hexstring.decode("hex")
#        except TypeError:
#            # TODO When Python3 only, show info from first exception
#            raise TypeError(
#                f"Hexdecode reported an error. Input hexstring: {hexstring}"
#            )

_CRC16TABLE = (
    0,
    49345,
    49537,
    320,
    49921,
    960,
    640,
    49729,
    50689,
    1728,
    1920,
    51009,
    1280,
    50625,
    50305,
    1088,
    52225,
    3264,
    3456,
    52545,
    3840,
    53185,
    52865,
    3648,
    2560,
    51905,
    52097,
    2880,
    51457,
    2496,
    2176,
    51265,
    55297,
    6336,
    6528,
    55617,
    6912,
    56257,
    55937,
    6720,
    7680,
    57025,
    57217,
    8000,
    56577,
    7616,
    7296,
    56385,
    5120,
    54465,
    54657,
    5440,
    55041,
    6080,
    5760,
    54849,
    53761,
    4800,
    4992,
    54081,
    4352,
    53697,
    53377,
    4160,
    61441,
    12480,
    12672,
    61761,
    13056,
    62401,
    62081,
    12864,
    13824,
    63169,
    63361,
    14144,
    62721,
    13760,
    13440,
    62529,
    15360,
    64705,
    64897,
    15680,
    65281,
    16320,
    16000,
    65089,
    64001,
    15040,
    15232,
    64321,
    14592,
    63937,
    63617,
    14400,
    10240,
    59585,
    59777,
    10560,
    60161,
    11200,
    10880,
    59969,
    60929,
    11968,
    12160,
    61249,
    11520,
    60865,
    60545,
    11328,
    58369,
    9408,
    9600,
    58689,
    9984,
    59329,
    59009,
    9792,
    8704,
    58049,
    58241,
    9024,
    57601,
    8640,
    8320,
    57409,
    40961,
    24768,
    24960,
    41281,
    25344,
    41921,
    41601,
    25152,
    26112,
    42689,
    42881,
    26432,
    42241,
    26048,
    25728,
    42049,
    27648,
    44225,
    44417,
    27968,
    44801,
    28608,
    28288,
    44609,
    43521,
    27328,
    27520,
    43841,
    26880,
    43457,
    43137,
    26688,
    30720,
    47297,
    47489,
    31040,
    47873,
    31680,
    31360,
    47681,
    48641,
    32448,
    32640,
    48961,
    32000,
    48577,
    48257,
    31808,
    46081,
    29888,
    30080,
    46401,
    30464,
    47041,
    46721,
    30272,
    29184,
    45761,
    45953,
    29504,
    45313,
    29120,
    28800,
    45121,
    20480,
    37057,
    37249,
    20800,
    37633,
    21440,
    21120,
    37441,
    38401,
    22208,
    22400,
    38721,
    21760,
    38337,
    38017,
    21568,
    39937,
    23744,
    23936,
    40257,
    24320,
    40897,
    40577,
    24128,
    23040,
    39617,
    39809,
    23360,
    39169,
    22976,
    22656,
    38977,
    34817,
    18624,
    18816,
    35137,
    19200,
    35777,
    35457,
    19008,
    19968,
    36545,
    36737,
    20288,
    36097,
    19904,
    19584,
    35905,
    17408,
    33985,
    34177,
    17728,
    34561,
    18368,
    18048,
    34369,
    33281,
    17088,
    17280,
    33601,
    16640,
    33217,
    32897,
    16448,
)
"""CRC-16 lookup table with 256 elements.

Built with this code::

    poly=0xA001
    table = []
    for index in range(256):
        data = index << 1
        crc = 0
        for _ in range(8, 0, -1):
            data >>= 1
            if (data ^ crc) & 0x0001:
                crc = (crc >> 1) ^ poly
            else:
                crc >>= 1
        table.append(crc)
    output = ''
    for i, m in enumerate(table):
        if not i%11:
            output += "\n"
        output += f"{m:5.0f}, "
    print output
"""

def _calculate_crc_string(inputstring):
    """Calculate CRC-16 for Modbus.

    Args:
        inputstring (str): An arbitrary-length message (without the CRC).

    Returns:
        A two-byte CRC string, where the least significant byte is first.

    """
    # Preload a 16-bit register with ones
    register = 0xFFFF

    for char in inputstring:
        register = (register >> 8) ^ _CRC16TABLE[(register ^ ord(char)) & 0xFF]

    return _num_to_twobyte_string(register, lsb_first=True)


#def _calculate_lrc_string(inputstring):
#    """Calculate LRC for Modbus.

#    Args:
#        inputstring (str): An arbitrary-length message (without the beginning
#        colon and terminating CRLF). It should already be decoded from hex-string.

#    Returns:
#        A one-byte LRC bytestring (not encoded to hex-string)

#    Algorithm from the document 'MODBUS over serial line specification and
#    implementation guide V1.02'.

#    The LRC is calculated as 8 bits (one byte).

#    For example a LRC 0110 0001 (bin) = 61 (hex) = 97 (dec) = 'a'. This function will
#    then return 'a'.

#    """

#    register = 0
#    for character in inputstring:
#        register += ord(character)

#    lrc = ((register ^ 0xFF) + 1) & 0xFF

#    return _num_to_onebyte_string(lrc)
