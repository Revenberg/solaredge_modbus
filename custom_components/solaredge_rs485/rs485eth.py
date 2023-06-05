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
import socket
import logging

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

long = int

BYTEORDER_BIG = 0
BYTEORDER_LITTLE = 1
BYTEORDER_BIG_SWAP = 2
BYTEORDER_LITTLE_SWAP = 3

_PAYLOADFORMAT_LONG = "long"
_PAYLOADFORMAT_INT = "int"
_PAYLOADFORMAT_REGISTER = "register"

class Instrument:
    """Instrument class for talking to instruments (slaves).

    Uses the rs485 RTU or ASCII protocols (via RS485).

    Args:
        port (str): The port number
        debug (bool): Set this to :const:`True` to print the communication details

    """

    def __init__(
        self,
        eth_address,
        eth_port,
    ):
        self.precalculate_read_size = True
        self.clear_buffers_before_each_transaction = True
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
            TypeError, ValueError, rs485Exception,
            serial.SerialException (inherited from IOError)

        """
        # Create payload
        ps1 = _num_to_twobyte_string(registeraddress)
        ps2 = _num_to_twobyte_string(number_of_registers)

        first_part = (
            chr(1)
            + chr(4)
            + f'{ps1}{ps2}'
        )
 
        request = first_part + _calculate_crc_string(first_part)

        # Communicate
        response = self._communicate(request)
        # Extract payload
        payload_from_slave = _extract_payload( response )
        
        if payload_from_slave == "":
            return None

        # Parse response payload
        return _parse_payload(
            payload_from_slave,
            numberOfDecimals,
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
            TypeError, ValueError, rs485Exception,
            serial.SerialException (inherited from IOError)

        """

        request = bytes(
            request, encoding="latin1"
        )  # Convert types to make it Python3 compatible

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)

            sock.connect((self.eth_address, self.eth_port))
            sock.send(request)
            answer = sock.recv(1024)
            sock.close()

        except Exception:
            raise NoResponseError("No communication with the instrument (timeout)")

        answer = str(answer, encoding="latin1")

        if not answer:
            raise NoResponseError("No communication with the instrument (no answer)")

        return answer

class rs485Exception(IOError):
    """Base class for rs485 communication exceptions.

    Inherits from IOError, which is an alias for OSError in Python3.
    """

class MasterReportedException(rs485Exception):
    """Base class for exceptions that the master (computer) detects."""

class NoResponseError(MasterReportedException):
    """No response from the slave."""

class InvalidResponseError(MasterReportedException):
    """The response does not fulfill the rs485 standad, for example wrong checksum."""

def _parse_payload(
    payload,
    numberOfDecimals,
    signed,
    byteorder,
    payloadformat,
):
    registerdata = payload[1:]

    if payloadformat == _PAYLOADFORMAT_LONG:
        return _bytestring_to_long(
            registerdata, signed, byteorder, numberOfDecimals
        )

    if payloadformat == _PAYLOADFORMAT_INT:
        return _twobyte_string_to_num(
            registerdata, numberOfDecimals, signed=signed
        )

    if payloadformat == _PAYLOADFORMAT_REGISTER:
        return _twobyte_string_to_num(
            registerdata, numberOfDecimals, signed=signed
        )

def _extract_payload(response):
    """Extract the payload data part from the slave's response.

    Args:
        response (str): The raw response byte string from the slave.
        This is different for RTU and ASCII.

    Returns:
        The payload part of the *response* string. Conversion from rs485 ASCII
        has been done if applicable.

    Raises:
        ValueError, TypeError, rs485Exception (or subclasses).

    Raises an exception if there is any problem with the received address,
    the 4 or the CRC.

    """
    MINIMAL_RESPONSE_LENGTH_RTU = 4
    plainresponse = response

    # Validate response length
    if len(response) < MINIMAL_RESPONSE_LENGTH_RTU:
        raise InvalidResponseError(
            "Too short rs485 RTU response (minimum length "
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

    # Read data payload
    first_databyte_number = 2

    last_databyte_number = len(response) - 2

    payload = response[first_databyte_number:last_databyte_number]
    return payload

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
    bytestring, signed=False, byteorder=BYTEORDER_BIG, numberOfDecimals=0
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

    fullregister = _unpack(formatcode, bytestring)

    if numberOfDecimals == 0:
        return fullregister
    divisor = 10 ** numberOfDecimals
    return fullregister / float(divisor)

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

    return str(
        result, encoding="latin1"
    )
    
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

    """

    packed = bytes(
        packed, encoding="latin1"
    )
    try:
        value = struct.unpack(formatstring, packed)[0]
    except Exception as error:
        errortext1 = "The received bytestring is probably wrong, as the "
        errortext2 = f"bytestring-to-num  conversion failed. Bytestring: {packed!r} "
        errortext3 = f"Struct format code is: {formatstring}"
        errortext4 = error

        raise InvalidResponseError(f"{errortext1}{errortext2}{errortext3}{errortext4}")

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
    """Calculate CRC-16 for rs485.

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
