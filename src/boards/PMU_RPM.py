"""
PMU_RPM.py - Python module defining the PMU_RPM class, an PMU_RPM type board equipped in the Keithley 4200A.
Author: Lucas LE DUDAL

This module defines the PMU_RPM class, which inherits from the Board class and represents a specific \
type of board (an PMU_RPM) equipped in the KI4200A. The PMU_RPM class provides methods and attributes\
specific to PMU_RPMs such as PulseIV sourcing and measuring.
"""
from ..instrcomms import Communications
from .Board import Board
from ..consts import Status, BoardType, PMUSourceRange, PMUPulseMode


class PMU_RPM(Board):
    """
    This class represents a Power Management Unit - Remote Pulse Measure (PMU_RPM) board equipped in the Keithley 4200A.

    Attributes:
        name (str): The name of the PMU_RPM board (e.g., \"PMU1RPM1-1\", \"PMU1RPM1-2\")
        status (str): Current status of the PMU_RPM board
        type (BoardType): The type of the board, set to BoardType.PMU_RPM

    """
    stepper_index: int = 0

    def __init__(self, name: str, comm: Communications) -> None:
        """
        Initialize an PMU_RPM instance with the given name and set its type to BoardType.PMU_RPM.

        Args:
            name (str): The name of the PMU_RPM board (e.g., \"PMU1RPM1-1\", \"PMU1RPM1-2\").
        """
        super().__init__(name, comm)
        self.status = Status.INITIALIZING
        self.board_type: BoardType = BoardType.PMU_RPM

        # Derive the pulse-card channel number from the last character of the name.
        # For "PMU1RPM1-2" the channel is 2; falls back to 0 for unexpected formats.
        self._channel: int = int(name[-1]) if name[-1].isdigit() else 0

        s_slot = name[-3] + name[-1]
        self._slot = int(s_slot) if s_slot.isnumeric() else 0

        # Measurements definition
        from ..results import Measurement
        from ..consts import MeasurementType, SourceType
        self.vh_measurement = Measurement(comm, f"VH{self._channel}", MeasurementType.PMU_RPM, unit=SourceType.VOLT, pmu_offset=0)
        self.ih_measurement = Measurement(comm, f"IH{self._channel}", MeasurementType.PMU_RPM, unit=SourceType.AMPERE, pmu_offset=1)
        self.vl_measurement = Measurement(comm, f"VL{self._channel}", MeasurementType.PMU_RPM, unit=SourceType.VOLT, pmu_offset=4)
        self.il_measurement = Measurement(comm, f"IL{self._channel}", MeasurementType.PMU_RPM, unit=SourceType.AMPERE, pmu_offset=5)

        self.measurements: list[Measurement] = [self.vh_measurement, self.ih_measurement, self.vl_measurement, self.il_measurement]
        self._stepper_index: int = 0

        # Cached backing values for properties (hardware defaults after :PMU:INIT)
        self._activated: bool = False
        self._load: float = 1e6
        self._llec: bool = False
        self._retain_config: bool = False
        self._source_range: PMUSourceRange = PMUSourceRange.V10

        # Last pulse timing parameters (saved for inspection / display purposes)
        self.period: float = 1e-6
        self.width: float = 500e-9
        self.riset: float = 100e-9
        self.fallt: float = 100e-9
        self.delay: float = 0.0

        # Last pulse train voltage levels
        self.vbase: float = 0.0
        self.vamplitude: float = 0.0

        self.status = Status.READY

    # === Factory ===

    @classmethod
    def of(cls, board: Board) -> "PMU_RPM":
        """
        Create an PMU_RPM instance from a generic Board instance.

        Args:
            board (Board): The generic Board instance to convert to an PMU_RPM.

        Returns:
            PMU_RPM: An instance of the PMU_RPM class.
        """
        rpm = PMU_RPM(board.name, board._comm)
        rpm.status = board.status
        return rpm

    # === Methods ===

    def deactivate(self) -> None:
        self.activated = False

    def setMeasurePIV(self, acquire_high: bool, acquire_low: bool) -> None:
        """
        Configure which pulse I-V measurement levels are acquired for this channel.

        Args:
            acquire_high (bool): Acquire the high-pulse measurements (VH, IH);
            acquire_low (bool): Acquire the low-pulse measurements (VL, IL);

        Raises:
            ValueError: If both `acquire_high` and `acquire_low` are `False`.
        """
        if not acquire_high and not acquire_low:
            raise ValueError(
                "At least one of acquire_high or acquire_low must be True; "
                "the instrument would generate an error otherwise."
            )
        self._comm.write(
            f":PMU:MEASURE:PIV {self._channel}, {int(acquire_high)}, {int(acquire_low)}"
        )
        self._comm.checkForError()

    def setPulseTimes(self, period: float, width: float, riset: float, fallt: float, delay: float = 0.0) -> None:
        """
        Set the pulse timing parameters for this channel (PMU 10 V range).

        Constraints:
            - `period`: 60 ns to 1 s. Must be the same on all channels.
            - `width`: 40 ns to `period - 10 ns`; > `0.5 * (riset + fallt)`.
            - `riset`, `fallt`: 20 ns to 33 ms each; <= width.
            - `delay`: 0 (no delay) or ≥ 20 ns; < `period - width - 0.5 * (riset + fallt)`.
            - Minimum off-time: `period - delay - width - 0.5 * (riset + fallt)` > 40 ns.

        Args:
            period (float): Pulse period in seconds.
            width (float): Pulse high-level width in seconds.
            riset (float): Pulse rise time in seconds.
            fallt (float): Pulse fall time in seconds.
            delay (float): Pre-pulse delay in seconds. Defaults to 0 (no delay).

        Raises:
            ValueError: If any timing constraint is violated.
        """
        # --- range checks ---
        if not (60e-9 <= period <= 1.0):
            raise ValueError(f"period must be 60 ns – 1 s; got {period:.3e} s.")
        if not (20e-9 <= riset <= 33e-3):
            raise ValueError(f"riset must be 20 ns – 33 ms; got {riset:.3e} s.")
        if not (20e-9 <= fallt <= 33e-3):
            raise ValueError(f"fallt must be 20 ns – 33 ms; got {fallt:.3e} s.")
        if not (40e-9 <= width <= period - 10e-9):
            raise ValueError(
                f"width must be 40 ns – (period − 10 ns) = {period - 10e-9:.3e} s; "
                f"got {width:.3e} s."
            )
        # --- cross-parameter constraints ---
        if width <= 0.5 * (riset + fallt):
            raise ValueError(
                f"width ({width:.3e} s) must be greater than 0.5*(riset+fallt) "
                f"= {0.5*(riset+fallt):.3e} s."
            )
        if riset > width:
            raise ValueError(
                f"riset ({riset:.3e} s) cannot be longer than width ({width:.3e} s)."
            )

        max_delay = period - width - 0.5 * (riset + fallt)
        if delay >= max_delay:
            raise ValueError(
                f"delay ({delay:.3e} s) must be less than "
                f"period - width - 0.5*(riset+fallt) = {max_delay:.3e} s."
            )
        min_off = period - delay - width - 0.5 * (riset + fallt)
        if min_off <= 40e-9:
            raise ValueError(
                f"Minimum off-time = {min_off:.3e} s must be > 40 ns. "
                f"Reduce delay, width, or rise/fall times, or increase period."
            )

        # Save for later inspection
        self.period = period
        self.width  = width
        self.riset  = riset
        self.fallt  = fallt
        self.delay  = delay

        if delay == 0.0:
            self._comm.write(
                f":PMU:PULSE:TIMES {self._channel}, {period:g}, {width:g}, {riset:g}, {fallt:g}"
            )
        else:
            self._comm.write(
                f":PMU:PULSE:TIMES {self._channel}, {period:g}, {width:g}, "
                f"{riset:g}, {fallt:g}, {delay:g}"
            )
        self._comm.checkForError()

    def setPulseTrain(self, vbase: float, vamplitude: float) -> None:
        """
        Set the base and amplitude voltage levels for this channel's pulse train.

        Args:
            vbase (float): Base (low) voltage level in volts.
            vamplitude (float): Amplitude (high) voltage level in volts.

        Raises:
            ValueError: If the span exceeds 10 V.
        """
        if abs(vamplitude - vbase) > 10.0:
            raise ValueError(
                f"Voltage span |vamplitude - vbase| = {abs(vamplitude - vbase):.3g} V "
                f"exceeds the 10 V source range."
            )
        self.vbase      = vbase
        self.vamplitude = vamplitude
        self._comm.write(f":PMU:PULSE:TRAIN {self._channel}, {vbase:g}, {vamplitude:g}")
        self._comm.checkForError()

    def setPulseStep(
        self,
        mode: PMUPulseMode,
        start: float,
        stop: float,
        step: float,
        constant_v: float | None = None,
    ) -> None:
        """
        Configure the voltage step pattern for this channel.

        Args:
            mode (PMUPulseMode): Which step variant to use.
            start (float): Initial step voltage in volts.
            stop (float): Final step voltage in volts.
            step (float): Step size in volts; must not be 0.
            constant_v (float | None): Fixed base voltage (AMPLITUDE mode) or
                fixed amplitude (BASE mode).  Not used for DC mode.

        Raises:
            ValueError: If *step* is 0, or if *constant_v* is required but not
                provided.
        """
        if step == 0:
            raise ValueError("step must not be 0.")
        if mode != PMUPulseMode.DC and constant_v is None:
            raise ValueError(
                f"constant_v is required for mode {mode.value} "
                f"(it is the fixed {'base' if mode == PMUPulseMode.AMPLITUDE else 'amplitude'} voltage)."
            )

        if mode == PMUPulseMode.DC:
            self._comm.write(f":PMU:STEP:DC {self._channel}, {start:g}, {stop:g}, {step:g}")
        elif mode == PMUPulseMode.AMPLITUDE:
            self._comm.write(
                f":PMU:STEP:PULSE:AMPLITUDE {self._channel}, {start:g}, {stop:g}, {step:g}, {constant_v:g}"
            )
        else:  # BASE
            self._comm.write(
                f":PMU:STEP:PULSE:BASE {self._channel}, {start:g}, {stop:g}, {step:g}, {constant_v:g}"
            )
        self._comm.checkForError()

        # Update shape
        PMU_RPM.stepper_index += 1
        self._stepper_index = PMU_RPM.stepper_index

        num_steps = int(abs(stop - start) / step) + 1
        for measurement in self.measurements:
            measurement.steps = num_steps
            measurement.order = self._stepper_index
            if mode == PMUPulseMode.AMPLITUDE and measurement in [self.vh_measurement]:
                measurement.min_value = min(start, stop)
                measurement.max_value = max(start, stop)
            elif mode == PMUPulseMode.BASE and measurement in [self.vl_measurement]:
                measurement.min_value = min(start, stop)
                measurement.max_value = max(start, stop)
            elif mode == PMUPulseMode.DC and measurement in [self.vh_measurement, self.vl_measurement]:
                measurement.min_value = min(start, stop)
                measurement.max_value = max(start, stop)

    def setPulseSweep(
        self, mode: PMUPulseMode,
        start: float, stop: float, step: float,
        dual_sweep: bool = False, constant_v: float | None = None
    ) -> None:
        """
        Configure the voltage sweep pattern for this channel.

        Args:
            mode (PMUPulseMode): Choose to sweep amplitude, base or DC voltage.
            start (float): Initial sweep voltage in volts.
            stop (float): Final sweep voltage in volts.
            step (float): Step size in volts; must not be 0.
            dual_sweep (bool): Back and forth sweep (start -> stop -> start).
            constant_v (float | None): Fixed base voltage (AMPLITUDE mode) or fixed amplitude (BASE mode). Not used for DC mode.

        Raises:
            ValueError: If `step` is 0, or if `constant_v` is required but not provided.
        """
        if step == 0:
            raise ValueError("`step` must not be 0.")
        if mode != PMUPulseMode.DC and constant_v is None:
            raise ValueError(
                f"`constant_v` is required for mode {mode.value} "
                f"(it is the fixed {'base' if mode == PMUPulseMode.AMPLITUDE else 'amplitude'} voltage)."
            )

        ds: int = int(dual_sweep)
        if mode == PMUPulseMode.DC:
            self._comm.write(
                f":PMU:SWEEP:DC {self._channel}, {start:g}, {stop:g}, {step:g}, {ds}"
            )
        elif mode == PMUPulseMode.AMPLITUDE:
            self._comm.write(
                f":PMU:SWEEP:PULSE:AMPLITUDE {self._channel}, {start:g}, {stop:g}, {step:g}, {constant_v:g}, {ds}"
            )
        else:  # BASE
            self._comm.write(
                f":PMU:SWEEP:PULSE:BASE {self._channel}, {start:g}, {stop:g}, {step:g}, {constant_v:g}, {ds}"
            )
        self._comm.checkForError()

        # Update shape
        num_steps = int(abs(stop - start) / step) + 1
        if dual_sweep:
            num_steps = num_steps * 2 - 1

        for meas in self.measurements:
            meas.steps = num_steps
            meas.order = 0
            if mode == PMUPulseMode.AMPLITUDE and meas in [self.vh_measurement]:
                meas.min_value = min(start, stop)
                meas.max_value = max(start, stop)
            elif mode == PMUPulseMode.BASE and meas in [self.vl_measurement]:
                meas.min_value = min(start, stop)
                meas.max_value = max(start, stop)
            elif mode == PMUPulseMode.DC and meas in [self.vh_measurement, self.vl_measurement]:
                meas.min_value = min(start, stop)
                meas.max_value = max(start, stop)

    # === Getters and setters ===

    @property
    def channel(self) -> int:
        """Pulse-card channel number (1–8) derived from the board name. Read-only."""
        return self._channel

    @property
    def activated(self) -> bool:
        """Output enable state for this PMU channel."""
        return self._activated

    @activated.setter
    def activated(self, value: bool) -> None:
        self._comm.write(f":PMU:OUTPUT:STATE {self._channel}, {int(value)}")
        self._comm.checkForError()
        self._activated = value

    @property
    def load(self) -> float:
        """
        Device impedance (pulse load) for this channel, in ohms.

        Valid range: 1.0 Ohm to 10 MOhm.

        The instrument uses this value to compensate the PMU output levels for the
        device impedance relative to the 50 Ohm output impedance of the pulse card.  Use
        the `llec` property to let the instrument detect the device load automatically instead.
        """
        return self._load

    @load.setter
    def load(self, value: float) -> None:
        if not (1.0 <= value <= 1e7):
            raise ValueError(f"Load impedance must be between 1.0 Ω and 10 MΩ; got {value} Ω.")
        self._load = value
        self._comm.write(f":PMU:LOAD {self._channel}, {value:g}")
        self._comm.checkForError()

    @property
    def llec(self) -> bool:
        """Load-line effect compensation (LLEC) enable state for this channel.

        The PMU runs the pulse in several calibration iterations before the actual test to measure
        and compensate for the real DUT load. This improves accuracy but increases test time.
        """
        return self._llec

    @llec.setter
    def llec(self, value: bool) -> None:
        self._llec = value
        self._comm.write(f":PMU:LLEC:CONFIGURE {self._channel}, {int(value)}")
        self._comm.checkForError()


    @property
    def retain_config(self) -> bool:
        """Whether the PMU configuration for this channel is retained between runs."""
        return self._retain_config

    @retain_config.setter
    def retain_config(self, value: bool) -> None:
        self._retain_config = value
        self._comm.write(f":PMU:RETAIN:CONFIG {self._channel}, {int(value)}")
        self._comm.checkForError()

    @property
    def source_range(self) -> PMUSourceRange:
        """Voltage source (and measure) range for this channel."""
        return self._source_range

    @source_range.setter
    def source_range(self, value: PMUSourceRange) -> None:
        self._source_range = value
        self._comm.write(f":PMU:SOURCE:RANGE {self._channel}, {value.value}")
        self._comm.checkForError()
