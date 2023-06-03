import sys
from enum import IntEnum
#from typing import Final

if sys.version_info.minor >= 11:
    # Needs Python 3.11
    from enum import StrEnum
else:
    try:
        from homeassistant.backports.enum import StrEnum

    except ImportError:
        from enum import Enum

        class StrEnum(str, Enum):
            pass


DOMAIN = "solaredge_modbus"
DEFAULT_NAME = "SolarEdge"

# units missing in homeassistant core
#ENERGY_VOLT_AMPERE_HOUR: Final = "VAh"
#ENERGY_VOLT_AMPERE_REACTIVE_HOUR: Final = "varh"


class RetrySettings(IntEnum):
    """Retry settings when opening a connection to the inverter fails."""

    Time = 800  # first attempt in milliseconds
    Ratio = 2  # time multiplier between each attempt
    Limit = 4  # number of attempts before failing

class ConfDefaultInt(IntEnum):
    SCAN_INTERVAL = 60
    PORT = 8899

class SunSpecNotImpl(IntEnum):
    INT16 = 0x8000
    UINT16 = 0xFFFF
    INT32 = 0x80000000
    UINT32 = 0xFFFFFFFF
    FLOAT32 = 0x7FC00000


# parameter names per sunspec
DEVICE_STATUS = {
    1: "I_STATUS_OFF",
    2: "I_STATUS_SLEEPING",
    3: "I_STATUS_STARTING",
    4: "I_STATUS_MPPT",
    5: "I_STATUS_THROTTLED",
    6: "I_STATUS_SHUTTING_DOWN",
    7: "I_STATUS_FAULT",
    8: "I_STATUS_STANDBY",
}

# English descriptions of parameter names
DEVICE_STATUS_TEXT = {
    1: "Off",
    2: "Sleeping (Auto-Shutdown)",
    3: "Grid Monitoring",
    4: "Production",
    5: "Production (Curtailed)",
    6: "Shutting Down",
    7: "Fault",
    8: "Maintenance",
}

VENDOR_STATUS = {
    SunSpecNotImpl.INT16: None,
    0: "No Error",
    17: "Temperature Too High",
    25: "Isolation Faults",
    27: "Hardware Error",
    31: "AC Voltage Too High",
    33: "AC Voltage Too High",
    32: "AC Voltage Too Low",
    34: "AC Frequency Too High",
    35: "AC Frequency Too Low",
    41: "AC Voltage Too Low",
    44: "No Country Selected",
    61: "AC Voltage Too Low",
    62: "AC Voltage Too Low",
    63: "AC Voltage Too Low",
    64: "AC Voltage Too High",
    65: "AC Voltage Too High",
    66: "AC Voltage Too High",
    67: "AC Voltage Too Low",
    68: "AC Voltage Too Low",
    69: "AC Voltage Too Low",
    79: "AC Frequency Too High",
    80: "AC Frequency Too High",
    81: "AC Frequency Too High",
    82: "AC Frequency Too Low",
    83: "AC Frequency Too Low",
    84: "AC Frequency Too Low",
    95: "Hardware Error",
    97: "Vin Buck Max",
    104: "Temperature Too High",
    106: "Hardware Error",
    107: "Battery Communication Error",
    110: "Meter Communication Error",
    120: "Hardware Error",
    121: "Isolation Faults",
    125: "Hardware Error",
    126: "Hardware Error",
    150: "Arc Fault Detected",
    151: "Arc Fault Detected",
    153: "Hardware Error",
    256: "Arc Detected",
}

SUNSPEC_DID = {
    101: "Single Phase Inverter",
    102: "Split Phase Inverter",
    103: "Three Phase Inverter",
    160: "Multiple MPPT Inverter Extension",
    201: "Single Phase Meter",
    202: "Split Phase Meter",
    203: "Three Phase Wye Meter",
    204: "Three Phase Delta Meter",
}

METER_EVENTS = {
    2: "M_EVENT_Power_Failure",
    3: "M_EVENT_Under_Voltage",
    4: "M_EVENT_Low_PF",
    5: "M_EVENT_Over_Current",
    6: "M_EVENT_Over_Voltage",
    7: "M_EVENT_Missing_Sensor",
    8: "M_EVENT_Reserved1",
    9: "M_EVENT_Reserved2",
    10: "M_EVENT_Reserved3",
    11: "M_EVENT_Reserved4",
    12: "M_EVENT_Reserved5",
    13: "M_EVENT_Reserved6",
    14: "M_EVENT_Reserved7",
    15: "M_EVENT_Reserved8",
    16: "M_EVENT_OEM1",
    17: "M_EVENT_OEM2",
    18: "M_EVENT_OEM3",
    19: "M_EVENT_OEM4",
    20: "M_EVENT_OEM5",
    21: "M_EVENT_OEM6",
    22: "M_EVENT_OEM7",
    23: "M_EVENT_OEM8",
    24: "M_EVENT_OEM9",
    25: "M_EVENT_OEM10",
    26: "M_EVENT_OEM11",
    27: "M_EVENT_OEM12",
    28: "M_EVENT_OEM13",
    29: "M_EVENT_OEM14",
    30: "M_EVENT_OEM15",
}

LIMIT_CONTROL = {0: "Total", 1: "Per Phase"}
