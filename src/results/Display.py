"""
Display.py - Python module defining the Display class to manage the Keithley 4200A display settings.
Author: Lucas LE DUDAL
"""
from ..instrcomms import Communications
from ..consts import DisplayMode
from .Measurement import Measurement
from ..consts import GraphPosition


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
        self._display_mode: DisplayMode = DisplayMode.GRAPH

    def setListMeasurements(self, l_measurements: list[str]):
        """
        Select the list of measurements to be displayed on KXCI in LIST mode.

        Args:
            l_measurements (list[str]): List of measurement names to display.
        """
        l_measurement_names = [f"'{measure_name}'" for measure_name in l_measurements]
        self._comm.write("SM")
        self._comm.write("LI " + ", ".join(l_measurement_names))
        self._comm.checkForError()

    def graphMeasurements(self, x: Measurement, y1: Measurement, y2: Measurement | None = None):
        """
        Configure the graph display to show the specified measurements on the X, Y1, and Y2 axes.

        Args:
            x (Measurement): The measurement to display on the X-axis. Measurement("T") can be used to display time on the X-axis.
            y1 (Measurement): The measurement to display on the Y1-axis.
            y2 (Measurement): The measurement to display on the Y2-axis.
        """
        self._comm.write("SM")

        if x.name == "T":
            self._comm.write(f"XT {x.min_value}, {x.max_value}")
        else:
            self._comm.write(x.getGraphCommand(GraphPosition.X))

        self._comm.write(y1.getGraphCommand(GraphPosition.Y1))

        if y2 is not None:
            self._comm.write(y2.getGraphCommand(GraphPosition.Y2))

        self._comm.checkForError()

    # === Getters / Setters ===
    @property
    def display_mode(self) -> DisplayMode:
        return self._display_mode

    @display_mode.setter
    def display_mode(self, mode: DisplayMode) -> None:
        self._comm.write("SM")
        self._comm.write("DM" + str(mode.value))
        self._comm.checkForError()
        self._display_mode = mode
