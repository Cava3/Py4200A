"""
PMU_RPM.py - Python module defining the PMU_RPM class, an PMU_RPM type board equipped in the Keithley 4200A.
Author: Lucas LE DUDAL

This module defines the PMU_RPM class, which inherits from the Board class and represents a specific \
type of board (an PMU_RPM) equipped in the KI4200A. The PMU_RPM class provides methods and attributes\
specific to PMU_RPMs.
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

        # Cached backing values for properties (hardware defaults after :PMU:INIT)
        self._output_state: bool = False
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

    def setMeasurePIV(self, acquire_high: bool, acquire_low: bool) -> None:
        """
        Configure which pulse I-V measurement levels are acquired for this channel.

        Sends ``:PMU:MEASURE:PIV <ch>, <AcquireHigh>, <AcquireLow>``.  At least
        one of *acquire_high* or *acquire_low* must be ``True``; if both are
        ``False`` the instrument generates an error and acquires all measurements.

        This method is only meaningful when ``:PMU:MEASURE:MODE`` is set to a
        spot-mean mode (``SPOT_MEAN_DISCRETE`` or ``SPOT_MEAN_AVERAGE``).

        Args:
            acquire_high (bool): ``True`` to acquire the high-pulse measurements
                (VH, IH, TH, SH); ``False`` to skip them.
            acquire_low (bool): ``True`` to acquire the low-pulse measurements
                (VL, IL, TL, SL); ``False`` to skip them.

        Raises:
            ValueError: If both *acquire_high* and *acquire_low* are ``False``.
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
        """Set the pulse timing parameters for this channel (PMU 10 V range).

        Sends ``:PMU:PULSE:TIMES <ch>, period, width, riset, fallt[, delay]``.
        The timing values are saved on the object for later inspection (e.g. to
        draw a pulse diagram).

        The following constraints apply for the PMU 10 V range and are enforced
        before sending the command:

        * ``period``: 60 ns to 1 s.
        * ``width``: 40 ns to ``period − 10 ns``; must also be greater than
          ``0.5 × (riset + fallt)``; rise time cannot exceed width.
        * ``riset``, ``fallt``: 20 ns to 33 ms each.
        * ``delay``: 0 (no delay) or ≥ 20 ns; must be less than
          ``period − width − 0.5 × (riset + fallt)``.
        * Minimum off-time: ``period − delay − width − 0.5 × (riset + fallt)`` > 40 ns.

        Note: ``period`` must be the same on all PMU channels; the most-recently
        sent period value is used by the instrument for all channels.

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
                f"period − width − 0.5*(riset+fallt) = {max_delay:.3e} s."
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
        """Set the base and amplitude voltage levels for this channel's pulse train.

        Sends ``:PMU:PULSE:TRAIN <ch>, vbase, vamplitude``.
        The voltage levels are saved on the object for later inspection.

        On the 10 V source range the total span ``|vamplitude − vbase|`` must
        not exceed 10 V.

        Args:
            vbase (float): Base (low) voltage level in volts.
            vamplitude (float): Amplitude (high) voltage level in volts.

        Raises:
            ValueError: If the span exceeds 10 V.
        """
        if abs(vamplitude - vbase) > 10.0:
            raise ValueError(
                f"Voltage span |vamplitude − vbase| = {abs(vamplitude - vbase):.3g} V "
                f"exceeds the 10 V source range."
            )
        self.vbase      = vbase
        self.vamplitude = vamplitude
        self._comm.write(f":PMU:PULSE:TRAIN {self._channel}, {vbase:g}, {vamplitude:g}")
        self._comm.checkForError()

    # === Getters and setters ===

    @property
    def channel(self) -> int:
        """Pulse-card channel number (1–8) derived from the board name. Read-only."""
        return self._channel

    @property
    def output_state(self) -> bool:
        """Output enable state for this PMU channel.

        * ``False`` (off) — output is disabled immediately upon assignment.
        * ``True`` (on) — output is enabled; takes effect when ``:PMU:EXECUTE`` is sent.

        Always set this back to ``False`` after a test completes.
        Sends ``:PMU:OUTPUT:STATE <ch>, <0|1>`` to the instrument.
        """
        return self._output_state

    @output_state.setter
    def output_state(self, value: bool) -> None:
        self._output_state = value
        self._comm.write(f":PMU:OUTPUT:STATE {self._channel}, {int(value)}")
        self._comm.checkForError()

    @property
    def load(self) -> float:
        """DUT impedance (pulse load) for this channel, in ohms.

        Valid range: 1.0 Ω to 10 MΩ (1e7 Ω). Default after ``:PMU:INIT``: 1 MΩ (1e6 Ω).

        The instrument uses this value to compensate the PMU output levels for the
        DUT impedance relative to the 50 Ω output impedance of the pulse card.  Use
        ``:PMU:LLEC:CONFIGURE`` (the :attr:`llec` property) to let the instrument
        detect the DUT load automatically instead.

        Sends ``:PMU:LOAD <ch>, <load>`` to the instrument.
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

        When ``True``, the PMU runs the pulse in several calibration iterations
        before the actual test to measure and compensate for the real DUT load.
        This improves accuracy but increases test time.

        Default after ``:PMU:INIT``: ``False`` (disabled).
        Sends ``:PMU:LLEC:CONFIGURE <ch>, <0|1>`` to the instrument.
        """
        return self._llec

    @llec.setter
    def llec(self, value: bool) -> None:
        self._llec = value
        self._comm.write(f":PMU:LLEC:CONFIGURE {self._channel}, {int(value)}")
        self._comm.checkForError()


    @property
    def retain_config(self) -> bool:
        """Whether the PMU configuration for this channel is retained between runs.

        When ``True``, the programmed settings are preserved so that
        ``:PMU:EXECUTE`` can be sent multiple times without resending all
        configuration commands.
        When ``False`` (default), the configuration is reset after each
        ``:PMU:EXECUTE``.

        Default after ``:PMU:INIT``: ``False``.
        Sends ``:PMU:RETAIN:CONFIG <ch>, <0|1>`` to the instrument.
        """
        return self._retain_config

    @retain_config.setter
    def retain_config(self, value: bool) -> None:
        self._retain_config = value
        self._comm.write(f":PMU:RETAIN:CONFIG {self._channel}, {int(value)}")
        self._comm.checkForError()

    @property
    def source_range(self) -> PMUSourceRange:
        """Voltage source (and measure) range for this channel.

        * ``PMUSourceRange.V10`` — 10 V low-voltage range (default after ``:PMU:INIT``).
        * ``PMUSourceRange.V40`` — 40 V high-voltage range.

        The range takes effect when ``:PMU:EXECUTE`` is sent.  All pulse
        voltage parameters (base, amplitude, start, stop) must lie within
        the selected span.
        Sends ``:PMU:SOURCE:RANGE <ch>, <10|40>`` to the instrument.
        """
        return self._source_range

    @source_range.setter
    def source_range(self, value: PMUSourceRange) -> None:
        self._source_range = value
        self._comm.write(f":PMU:SOURCE:RANGE {self._channel}, {value.value}")
        self._comm.checkForError()

    def setPulseStep(
        self,
        mode: PMUPulseMode,
        start: float,
        stop: float,
        step: float,
        constant_v: float | None = None,
    ) -> None:
        """Configure the voltage step pattern for this channel.

        Dispatches to one of three SCPI commands depending on *mode*:

        * ``AMPLITUDE`` — ``:PMU:STEP:PULSE:AMPLITUDE <ch>, start, stop, step, vbase``
          Steps the pulse high level; *constant_v* sets the fixed base voltage.
        * ``BASE`` — ``:PMU:STEP:PULSE:BASE <ch>, start, stop, step, vamplitude``
          Steps the pulse low level; *constant_v* sets the fixed amplitude.
        * ``DC`` — ``:PMU:STEP:DC <ch>, start, stop, step``
          Steps a DC voltage level; *constant_v* is not used.

        For ``AMPLITUDE`` and ``BASE`` modes a sweep must be configured on
        another PMU channel before this command is sent.  Voltage bounds are
        validated by the instrument at ``:PMU:EXECUTE`` time and reported via
        ``checkForError``.

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

    def setPulseSweep(
        self,
        mode: PMUPulseMode,
        start: float,
        stop: float,
        step: float,
        dual_sweep: bool = False,
        constant_v: float | None = None,
    ) -> None:
        """Configure the voltage sweep pattern for this channel.

        Dispatches to one of three SCPI commands depending on *mode*:

        * ``AMPLITUDE`` — ``:PMU:SWEEP:PULSE:AMPLITUDE <ch>, start, stop, step, vbase, dualSweep``
          Sweeps the pulse high level; *constant_v* sets the fixed base voltage.
        * ``BASE`` — ``:PMU:SWEEP:PULSE:BASE <ch>, start, stop, step, vamplitude, dualSweep``
          Sweeps the pulse low level; *constant_v* sets the fixed amplitude.
        * ``DC`` — ``:PMU:SWEEP:DC <ch>, start, stop, step, dualSweep``
          Sweeps a DC voltage level; *constant_v* is not used.

        When *dual_sweep* is ``True`` the instrument sweeps start→stop then
        stop→start.  If sweeping multiple channels, all must have the same
        number of steps.  Voltage bounds are validated at ``:PMU:EXECUTE`` time.

        Args:
            mode (PMUPulseMode): Which sweep variant to use.
            start (float): Initial sweep voltage in volts.
            stop (float): Final sweep voltage in volts.
            step (float): Step size in volts; must not be 0.
            dual_sweep (bool): ``True`` to enable dual (return) sweep.
                Defaults to ``False``.
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

        ds = int(dual_sweep)
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
