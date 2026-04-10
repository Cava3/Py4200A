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

class SweepType(Enum):
    """Enum of possible sweep types"""
    LINEAR = 1
    LOG10 = 2
    LOG25 = 3
    LOG50 = 4

class DisplayMode(Enum):
    """Enum for the 2 possible display modes"""
    NONE = 0
    GRAPH = 1
    LIST = 2

class GraphPosition(Enum):
    """Enum for the 3 axis of the graph display"""
    X = "XN"
    Y1 = "YA"
    Y2 = "YB"

class RPMMode(Enum):
    """Enum for the RPM switching modes"""
    PMU = 0
    CV_2W = 1
    SMU = 2
    CV_4W = 3

class IntegrationTime(Enum):
    """Enum for SMU integration time (IT)"""
    SHORT = 1
    NORMAL = 2
    LONG = 3


class PMUMeasureMode(Enum):
    """Measurement mode for the PMU, set via ``:PMU:MEASURE:MODE``.

    Controls whether the instrument captures full waveforms or spot-mean
    (averaged) readings, and whether those readings are returned per-pulse
    (discrete) or averaged across all pulses in the burst.

    Attributes:
        NONE: No measurements acquired (mode 0).
        SPOT_MEAN_DISCRETE: Averaged V/I per pulse — one data point per pulse
            in the burst (mode 1). Default after ``:PMU:INIT``.
        WAVEFORM_DISCRETE: Time-sampled V/I/T per pulse — full waveform for
            every pulse in the burst (mode 2).
        SPOT_MEAN_AVERAGE: Like ``SPOT_MEAN_DISCRETE`` but all pulses are
            averaged into a single data set (mode 3).
        WAVEFORM_AVERAGE: Like ``WAVEFORM_DISCRETE`` but all pulses are
            averaged sample-by-sample into a single waveform (mode 4).
    """
    NONE                = 0
    SPOT_MEAN_DISCRETE  = 1
    WAVEFORM_DISCRETE   = 2
    SPOT_MEAN_AVERAGE   = 3
    WAVEFORM_AVERAGE    = 4

class MeasurementType(Enum):
    """Selects the data-retrieval protocol for a Measurement.

    Attributes:
        SMU: Uses the ``RD`` KXCI command (SMU / classic source-measure units).
        PMU_RPM: Uses the ``:PMU:DATA:COUNT?`` / ``:PMU:DATA:GET`` KXCI commands
            (Power Measurement Unit with Remote Pulse Measure card).
    """
    SMU = "SMU"
    PMU_RPM = "PMU_RPM"

class PMURequestedValue(Enum):
    """Tokens accepted by the *requestedValues* parameter of ``:PMU:DATA:GET``.

    **Waveform-capture mode** (time-domain acquisition):

    Attributes:
        V: Measured voltage.
        I: Measured current.
        T: Timestamp.
        S: Status word.

    **Spot-mean / Pulse I-V mode** (high/low pulse levels):

    Attributes:
        VH: Voltage - high level.
        IH: Current - high level.
        TH: Timestamp - high level.
        SH: Status - high level.
        VL: Voltage - low level.
        IL: Current - low level.
        TL: Timestamp - low level.
        SL: Status - low level.
    """
    # Waveform capture
    V  = "V"
    I  = "I"
    T  = "T"
    S  = "S"
    # Spot mean / Pulse I-V
    VH = "VH"
    IH = "IH"
    TH = "TH"
    SH = "SH"
    VL = "VL"
    IL = "IL"
    TL = "TL"
    SL = "SL"
