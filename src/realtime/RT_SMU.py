"""
realtime/RT_SMU.py - Real-time SMU channel controller for the Keithley 4200A.
Author: Lucas LE DUDAL
"""
from ..instrcomms import Communications
from .consts import parse_value, CurrentSourceRange, VoltageSourceRange


class RT_SMU:
    """
    Controls a single SMU channel of the Keithley 4200A in User Mode (US).

    Provides direct real-time source and measure operations: configure the SMU
    as a voltage or current source (DV/DI), trigger point measurements (TV/TI),
    adjust ranges (RV/RI/RG), and autocalibrate (AC).

    User Mode must be active (US sent) before using any method. If created via
    RT_KI4200A.get_smu(), this is guaranteed. If constructed directly, call
    RT_KI4200A.re_enter() first.
    """

    def __init__(self, slot: int, comm: Communications, hp: bool = False) -> None:
        """
        Args:
            slot: SMU slot number (1-8).
            comm: Active Communications object connected to the instrument.
            hp: True for a 4210/4211-SMU (HP), which raises the current limit to ±1.05 A.
        """
        self._slot = slot
        self._comm = comm
        self.hp: bool = hp

    # === Channel management ===

    def deactivate(self) -> None:
        """Reset this SMU channel definition via the DE page (CH command)."""
        self._write(f"DV{self._slot}")
        self._comm.checkForError()

    # === Source setup ===

    def setCurrentOutput(self, output: float, compliance: float, range_code: CurrentSourceRange = CurrentSourceRange.AUTORANGE) -> None:
        """
        DI - Configure this SMU as a current source.

        Args:
            range_code: Current range (see CurrentSourceRange).
            output: Output current in amperes (-0.105 to +0.105 A; ±1.05 for HP SMU).
            compliance: Voltage compliance in volts (-210.0 to +210.0 V).
        """
        i_limit: tuple[float, float] = (-1.05, 1.05) if self.hp else (-0.105, 0.105)
        output = min(max(output, i_limit[0]), i_limit[1])
        self._write(f"DI {self._slot}, {range_code.value}, {output}, {compliance}")
        self._comm.checkForError()

    def setVoltageOutput(self, output: float, compliance: float, range_code: VoltageSourceRange = VoltageSourceRange.AUTORANGE) -> None:
        """
        DV - Configure this SMU as a voltage source.

        Args:
            range_code: Voltage range (see VoltageSourceRange).
            output: Output voltage in volts (-210.0 to +210.0 V).
            compliance: Current compliance in amperes (-0.105 to +0.105 A; ±1.05 for HP SMU).
        """
        i_limit: tuple[float, float] = (-1.05, 1.05) if self.hp else (-0.105, 0.105)
        output = min(max(output, -200.0), 200.0)
        compliance = min(max(compliance, i_limit[0]), i_limit[1])
        self._write(f"DV {self._slot}, {range_code.value}, {output}, {compliance}")
        self._comm.checkForError()

    def setVoltageOutputForVS(self, voltage: float) -> None:
        """
        DS - Update the output voltage of this VS-mode channel immediately.

        Args:
            voltage: Target voltage in volts. Clamped to [-200.0, +200.0] V.
        """
        voltage = min(max(voltage, -200.0), 200.0)
        self._write(f"DS {self._slot}, {voltage}")
        self._comm.checkForError()

    # === Measurement triggers ===

    def measure_current(self) -> float:
        """
        TI - Trigger an immediate current measurement on this channel.

        Returns:
            float: Measured current in amperes.
        """
        response = self._comm.query(f"TI {self._slot}")
        return parse_value(response)

    def measure_voltage(self) -> float:
        """
        TV - Trigger an immediate voltage measurement on this channel.

        Returns:
            float: Measured voltage in volts.
        """
        response = self._comm.query(f"TV {self._slot}")
        return parse_value(response)

    # === Range and calibration ===

    def set_current_range(self, range_amps: float, compliance: float) -> None:
        """
        RI - Switch this SMU to a specific current measurement range immediately.

        Args:
            range_amps: Target current range in amperes.
            compliance: Current compliance in amperes.
        """
        self._write(f"RI {self._slot}, {range_amps}, {compliance}")
        self._comm.checkForError()

    def set_voltage_range(self, range_volts: float, compliance: float) -> None:
        """
        RV - Switch this SMU to a specific voltage measurement range immediately.

        Args:
            range_volts: Target voltage range in volts (-210.0 to +210.0).
            compliance: Voltage compliance in volts (-210.0 to +210.0).
        """
        self._write(f"RV {self._slot}, {range_volts}, {compliance}")
        self._comm.checkForError()

    def set_lowest_current_range(self, range_amps: float) -> None:
        """
        RG - Set the lowest current range used during autoranging on this SMU.

        Args:
            range_amps: Minimum range in amperes (e.g. 1e-9 for 1 nA floor).
        """
        self._write(f"RG {self._slot}, {range_amps}")
        self._comm.checkForError()

    # === Data retrieval ===

    def get_timestamp_data(self, channel_name: str) -> float:
        """
        DO - Retrieve timestamp data associated with a named channel.

        Args:
            channel_name: User-defined channel name as set in DE/CH.

        Returns:
            float: The timestamp or associated scalar value.
        """
        response = self._comm.query(f"DO '{channel_name}'")
        return parse_value(response)

    # === Private ===

    def _write(self, command: str) -> None:
        if self._comm.con_type == 1:
            self._comm.write(command)
        else:
            self._comm.query(command)

    # === Properties ===

    @property
    def slot(self) -> int:
        """The SMU slot number (1-8)."""
        return self._slot
