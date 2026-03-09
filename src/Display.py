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
    """

    def __init__(self, comm: Communications) -> None:
        """
        Initialize the Display controller.

        Args:
            comm (Communications): The communication object used to send commands.
        """
        self._comm = comm
        self._displayMode: DisplayMode = DisplayMode.GRAPH

    # === Getters / Setters ===
    @property
    def displayMode(self) -> DisplayMode:
        return self._displayMode

    @displayMode.setter
    def displayMode(self, mode: DisplayMode) -> None:
        self._comm.write("DM" + str(mode.value))
        self._comm.checkForError()
        self._displayMode = mode
