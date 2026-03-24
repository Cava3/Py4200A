"""
realtime/RT_KI4200A.py - Real-time instrument controller for the Keithley 4200A.
Author: Lucas LE DUDAL
"""
from typing import TYPE_CHECKING
from ..instrcomms import Communications
from ..consts import IntegrationTime
from .RT_SMU import RT_SMU

if TYPE_CHECKING:
    from ..KI4200A import KI4200A


class RT_KI4200A:
    """
    Controls the Keithley 4200A in User Mode (US), enabling real-time
    source/measure operations without a standard sweep setup.

    Scans equipped SMU channels on construction and enters User Mode.
    Use re_enter() if another page is selected in between.
    """

    def __init__(self, comm: Communications) -> None:
        """
        Initialize RT_KI4200A, scan for SMU channels, and enter User Mode.

        Args:
            comm: Active Communications object connected to the instrument.
        """
        self._comm = comm
        self._integration_time: IntegrationTime = IntegrationTime.NORMAL
        self._resolution: int = 5
        self.l_smus: list[RT_SMU] = []
        self._scan()
        self.re_enter()

    @classmethod
    def from_ki4200a(cls, ki: "KI4200A") -> "RT_KI4200A":
        """
        Factory: build an RT_KI4200A from an existing KI4200A instance.

        Args:
            ki: A KI4200A instance with an active connection.

        Returns:
            RT_KI4200A sharing the same communication link.
        """
        return cls(ki.comms)

    # === Page management ===

    def re_enter(self) -> None:
        """US - (Re-)enter User Mode after another page command was issued."""
        self._write("US")

    # === Instrument-level US commands ===

    def reset(self) -> None:
        """
        Reset the instrument to its default state.
        Clears the buffer, clears errors, resets all instruments, and deactivates SMUs.
        """
        self._write("BC")
        self._write(":ERROR:LAST:CLEAR")
        self._write("*RST")
        for smu in self.l_smus:
            smu.deactivate()
        self._comm.checkForError()
        self.re_enter()

    # === Factory ===

    def get_smu(self, slot: int) -> RT_SMU:
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
        """Query the instrument for equipped boards and populate l_smus."""
        equipped: list[str] = self._comm.query("*OPT?").split(",")
        self._comm.checkForError()
        for name in equipped:
            name = name.strip()
            if "SMU" in name.upper() or "VS" in name.upper() or "VM" in name.upper():
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
