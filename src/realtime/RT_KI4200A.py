"""
realtime/RT_KI4200A.py - Real-time instrument controller for the Keithley 4200A.
Author: Lucas LE DUDAL
"""
from ..instrcomms import Communications
from ..consts import IntegrationTime, RPMMode
from .RT_SMU import RT_SMU
from .RT_PMU_RPM import RT_PMU_RPM


class RT_KI4200A:
    """
    Controls the Keithley 4200A in User Mode (US), enabling real-time
    source/measure operations without a standard sweep setup.

    Scans equipped SMU and RPM channels on construction, switches all RPMs to
    SMU mode so they pass voltage/current, then enters User Mode.
    Use reEnter() if another page is selected in between.
    """

    def __init__(self, instrument_resource_string: str) -> None:
        """
        Connect to the instrument, scan for SMU/RPM channels, configure RPMs, and enter User Mode.

        Args:
            instrument_resource_string: VISA resource string (e.g. "GPIB0::17::INSTR").
        """
        self._comm = Communications(instrument_resource_string)
        self._comm.connect()
        self._comm.write_termination = "\0"
        self._comm.read_termination = "\n"
        self._integration_time: IntegrationTime = IntegrationTime.NORMAL
        self._resolution: int = 5
        self.l_smus: list[RT_SMU] = []
        self.l_rpms: list[RT_PMU_RPM] = []
        self._scan()
        for rpm in self.l_rpms:
            rpm.set_mode(RPMMode.SMU)
        self.userMode()

    # === Page management ===

    def userMode(self) -> None:
        """US - (Re-)enter User Mode after another page command was issued."""
        self._write("US")

    # === Instrument-level US commands ===

    def reset(self) -> None:
        """
        Reset the instrument to its default state.
        Clears the buffer, clears errors, resets all instruments, deactivates SMUs,
        and restores RPMs to PMU mode.
        """
        self._write("BC")
        self._write(":ERROR:LAST:CLEAR")
        self._write("*RST")
        for smu in self.l_smus:
            smu.deactivate()
        for rpm in self.l_rpms:
            rpm.set_mode(RPMMode.SMU)
        self._comm.checkForError()
        self.userMode()

    def disconnect(self) -> None:
        """Close the connection to the instrument."""
        for rpm in self.l_rpms:
            rpm.set_mode(RPMMode.PMU)
        self._comm.disconnect()

    # === Factory ===

    def getSMU(self, slot: int) -> RT_SMU:
        """
        Get the RT_SMU instance for the given slot number.

        Args:
            slot: SMU slot number (1-8).

        Returns:
            RT_SMU: Real-time SMU controller for that channel.

        Raises:
            ValueError: If no SMU with that slot was found during scan.
        """
        for smu in self.l_smus:
            if smu.slot == slot:
                return smu
        raise ValueError(f"No SMU found at slot {slot}.")

    # === Private ===

    def _scan(self) -> None:
        """Query the instrument for equipped boards and populate l_smus and l_rpms."""
        equipped: list[str] = [n.strip() for n in self._comm.query("*OPT?").split(",")]
        self._comm.checkForError()

        # FIXME: KXCI bug — only the second RPM is returned; insert the first one manually.
        if "PMU1RPM1-2" in equipped and "PMU1RPM1-1" not in equipped:
            equipped.insert(equipped.index("PMU1RPM1-2"), "PMU1RPM1-1")

        for name in equipped:
            if "RPM" in name.upper():
                self.l_rpms.append(RT_PMU_RPM(name, self._comm))
            elif "SMU" in name.upper() or "VS" in name.upper() or "VM" in name.upper():
                slot_str = name[-1]
                if slot_str.isdigit():
                    self.l_smus.append(RT_SMU(int(slot_str), self._comm, hp="HP" in name.upper()))
        self.l_smus.sort(key=lambda s: s.slot)

    def _write(self, command: str) -> None:
        if self._comm.con_type == 1:
            self._comm.write(command)
        else:
            self._comm.query(command)

    # === Getters / Setters ===

    @property
    def integration_time(self) -> IntegrationTime:
        """Integration time used for each measurement point."""
        return self._integration_time

    @integration_time.setter
    def integration_time(self, value: IntegrationTime) -> None:
        self._integration_time = value
        self._write(f"IT {value.value}")
        self._comm.checkForError()

    @property
    def resolution(self) -> int:
        """Measurement resolution in significant digits (3-7)."""
        return self._resolution

    @resolution.setter
    def resolution(self, value: int) -> None:
        self._resolution = min(max(value, 3), 7)
        self._write(f"RS {self._resolution}")
        self._comm.checkForError()
