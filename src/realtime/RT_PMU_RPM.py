"""
realtime/RT_PMU_RPM.py - Real-time RPM controller for the Keithley 4200A.
Author: Lucas LE DUDAL
"""
from ..instrcomms import Communications
from ..consts import RPMMode


class RT_PMU_RPM:
    """
    Controls a single RPM (Remote Preamplifier/Switch Module) attached to a PMU
    in the Keithley 4200A.

    The RPM must be switched to SMU mode before it will pass voltage or current
    from an SMU channel. This is done automatically by RT_KI4200A on construction.
    """

    def __init__(self, name: str, comm: Communications) -> None:
        """
        Args:
            name: RPM board name as returned by *OPT? (e.g. "PMU1RPM1-1").
            comm: Active Communications object connected to the instrument.
        """
        self._name = name
        self._comm = comm
        # Extract PMU slot and RPM index from name, e.g. "PMU1RPM1-2" → pmu=1, rpm=2
        self._pmu_num: str = name[-3]
        self._rpm_num: str = name[-1]

    def set_mode(self, mode: RPMMode) -> None:
        """
        Configure the RPM switching mode.

        Args:
            mode: Target RPMMode (SMU, PMU, CV_2W, CV_4W).
        """
        cmd = f":PMU:RPM:CONFIGURE PMU{self._pmu_num}-{self._rpm_num}, {mode.value}"
        if self._comm.con_type == 1:
            self._comm.write(cmd)
        else:
            self._comm.query(cmd)
        self._comm.checkForError()

    @property
    def name(self) -> str:
        """Board name as reported by the instrument."""
        return self._name
