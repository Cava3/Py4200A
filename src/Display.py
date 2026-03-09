"""
Display.py - Python module defining the Display class to manage the Keithley 4200A display settings.
Author: Lucas LE DUDAL
"""

from .instrcomms import Communications
from.consts import DisplayMode

class Display:
    """
    This class provides methods to control the display of the Keithley 4200A,
    such as clearing the screen, displaying messages, or controlling the backlight.

    Attributes:
        displayMode (DisplayMode): The display mode on KXCI.

    """

    def __init__(self, comm: Communications) -> None:
        """
        Initialize the Display controller.

        Args:
            comm (Communications): The communication object used to send commands.
        """
        self._comm = comm
        self._displayMode: DisplayMode = DisplayMode.GRAPH

    def setListMeasurements(self, l_measurements: list[str]):
        """
        Select the list of measurements to be displayed on KXCI in LIST mode.

        Args:
            l_measurements (list[str]): List of measurement names to display.
        """
        l_mNames = [f"'{measureName}'" for measureName in l_measurements]
        self._comm.write("SM")
        self._comm.write("LI " + ", ".join(l_mNames))
        self._comm.checkForError()

    #TODO: Real management of measurements

    # === Getters / Setters ===
    @property
    def displayMode(self) -> DisplayMode:
        return self._displayMode

    @displayMode.setter
    def displayMode(self, mode: DisplayMode) -> None:
        self._comm.write("SM")
        self._comm.write("DM" + str(mode.value))
        self._comm.checkForError()
        self._displayMode = mode
