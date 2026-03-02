"""
Constants and enums for the KI4200A library.

Authors: Lucas LE DUDAL
"""

from enum import Enum

class ElectricalUnit(Enum):
    """Enum of possible electrical units for measurements, sources, and limits."""
    NONE = 0 # OFF
    VOLT = 1
    AMPERE = 2
    COMMON = 3

class SourceFunction(Enum):
    """Enum of possible source functions"""
    NONE = 0
    SWEEP = 1
    STEP = 2
    CONSTANT = 3

class BoardType(Enum):
    """Enum of possible board types that can be equipped in the KI4200A."""
    NONE = 0 # OFF
    SMU = 1
    PMU = 2
    CVU = 3
    RPM = 4

class Status(Enum):
    """Enum of all possible tasks and states an equipment can have"""
    INITIALIZING = "Initializing"
    CONNECTING = "Connecting"
    CONFIGURING = "Configuring"
    SCANNING = "Scanning"
    READY = "Ready"
    READY_NOT_RESET = "Ready, not reset"
    DISCONNECTED = "Disconnected"
