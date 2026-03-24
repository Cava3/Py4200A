"""
realtime/consts.py - Constants and utilities for the realtime module.
Author: Lucas LE DUDAL
"""
from enum import Enum


class CurrentSourceRange(Enum):
    """Current source range codes for the DI command."""
    AUTORANGE    = 0
    R_100PA      = 1   # 100 pA
    R_1NA        = 2   # 1 nA
    R_10NA       = 3   # 10 nA
    R_100NA      = 4   # 100 nA
    R_1UA        = 5   # 1 µA
    R_10UA       = 6   # 10 µA
    R_100UA      = 7   # 100 µA
    R_1MA        = 8   # 1 mA
    R_10MA       = 9   # 10 mA
    R_100MA      = 10  # 100 mA
    R_1A         = 11  # 1 A (HP SMU only)
    LIMITED_AUTO = 12
    FIXED_AUTO   = 13


class VoltageSourceRange(Enum):
    """Voltage source range codes for the DV command."""
    AUTORANGE    = 0
    R_20V        = 1
    R_200V       = 2
    R_200MV      = 3
    R_2V         = 4
    LIMITED_AUTO = 5


def parse_value(response: str) -> float:
    """
    Parse a numeric value from a KXCI measurement response.

    KXCI responses have the form ``X YY Z +N.NNNN E±NN`` where X is a status
    character, YY is the channel, Z is the mode (V/I), and the remainder is the
    reading in scientific notation. The mantissa and exponent may be separated
    by a space.

    Args:
        response: Raw string returned by the instrument.

    Returns:
        float: The parsed measurement value.

    Raises:
        ValueError: If no numeric value can be extracted.
    """
    try:
        return float(response)
    except:
        try:
            return float(response.split(" ")[1])
        except:
            raise ValueError(f"Cannot parse reading from response: {response!r}")
