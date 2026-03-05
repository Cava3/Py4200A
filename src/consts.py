"""
Constants and enums for the KI4200A library.

Authors: Lucas LE DUDAL
"""

from enum import Enum

class SMUMode(Enum):
    """Enum of SMU types"""
    SMU = 0 # Full def
    VS = 1  # Voltage source only
    VM = 2  # Voltage meter only

class SourceType(Enum):
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
    # SWEEP2 = 4

class BoardType(Enum):
    """Enum of possible board types that can be equipped in the KI4200A."""
    NONE = 0 # OFF
    SMU = 1
    CVU = 2
    PMU_RPM = 3

class Status(Enum):
    """Enum of all possible tasks and states an equipment can have"""
    INITIALIZING = "Initializing"
    CONNECTING = "Connecting"
    CONFIGURING = "Configuring"
    SCANNING = "Scanning"
    READY = "Ready"
    READY_NOT_RESET = "Ready, not reset"
    DISCONNECTED = "Disconnected"
