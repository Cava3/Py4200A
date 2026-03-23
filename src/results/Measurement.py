"""
Measurement.py - Python module defining the Measurement class to represent a specific measurement in the Keithley 4200A.
Author: Lucas LE DUDAL
"""
from ..consts import GraphPosition, SourceType
from ..error import KXCILimitationError
from ..instrcomms import Communications


class Measurement:
    """
    This class represents a measurement configuration and its associated data.

    Attributes:
        name (str): The name of the measurement.
        steps (int): The number of measurement steps.
        order (int): Sweeping order of this measurement's source axis.  ``-1``
            means not yet configured (cannot be used as a parameter).  ``0``
            for a Sweep source (innermost loop); equal to the SMU's
            ``stepper_index`` for a Step source (outermost loops, in
            descending order).
        min_value (float): The minimum value for the measurement range or display.
        max_value (float): The maximum value for the measurement range or display.
        is_log_scale (bool): Indicates if the measurement should be handled/displayed in log scale.
    """

    def __init__(self, comm: Communications, name: str, steps: int = -1, min_value: float = 0.0, max_value: float = 0.0, is_log_scale: bool = False, unit: SourceType = SourceType.NONE) -> None:
        """
        Initialize a Measurement instance.

        Args:
            name (str): The name of the measurement.
            steps (int): The number of measurement steps.
            min_value (float): The minimum value.
            max_value (float): The maximum value.
            is_log_scale (bool): True for logarithmic scale, False for linear.
            unit (SourceType): The unit of the measurement.
        """
        self._name: str = ""
        self._min_value: float = 0
        self._max_value: float = 0
        self._com: Communications = comm
        self.unit: SourceType = unit
        self.steps: int = steps
        self.order: int = -1
        self.name = name
        self.min_value = min_value
        self.max_value = max_value
        self.is_log_scale = is_log_scale

    def getResultAt(self, index: int) -> str:
        """
        Fetch the measurement result at a specific index.

        Args:
            index (int): The index at which to fetch the measurement result.

        Returns:
            str: The raw measurement result at the specified index.
        """
        str_result: str = self._com.query(f"RD '{self.name}', {index}")
        self._com.checkForError()

        return str_result

    def isResultValid(self, value: str) -> bool:
        """
        Check if a value is a valid measurement.

        Args:
            value (str) : The value for which to check validity

        Returns:
            bool: True if the measurement value is valid, False otherwise.
        """
        try:
            float(value)
        except ValueError:
            return False

        return float(value) != 0


    def getResultSerie(self) -> list[float]:
        """
        Fetch exactly the first ``steps`` measurement results from the instrument.

        Returns:
            list[float]: The list of the first ``steps`` measurement values retrieved from the instrument.
        """
        l_readings: list[float] = []
        for index in range(1, self.steps + 1):
            value: str = self.getResultAt(index)
            l_readings.append(float(value))

        return l_readings

    def getAllResults(self) -> list[float]:
        """
        Fetch the measurement results from the instrument.

        Returns:
            list[float]: The list of measurement values retrieved from the instrument.
        """
        l_readings: list[float] = []
        index: int = 1
        value: str = self.getResultAt(index)
        index+=1
        while self.isResultValid(value):
            l_readings.append(float(value))
            value = self.getResultAt(index)
            index += 1

        return l_readings

    def getGraphCommand(self, axis: GraphPosition) -> str:
        """
        Get the graph command for displaying the measurement on the specified graph axis.

        Args:
            axis (GraphPosition): The axis on which to display the measurement.

        Returns:
            str: The command string to configure the graph display for this measurement.
        """
        command = f"{axis.value} '{self.name}', {int(self.is_log_scale)+1}, {self.min_value}, {self.max_value}"
        return command


    def __str__(self) -> str:
        return f"Measurement(name='{self.name}', range=[{self.min_value}, {self.max_value}])"

    # === Getters and setters ===
    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, value: str) -> None:
        if not value.isalnum() or not value[0].isalpha():
            raise KXCILimitationError("Measurement name must be alphanumeric and start with a letter")

        self._name = value.upper()

    @property
    def min_value(self) -> float:
        return self._min_value
    
    @min_value.setter
    def min_value(self, value: float) -> None:
        minmax: tuple[int, int] = (-9999, 9999) if self.unit == SourceType.VOLT else (-999, 999)
        self._min_value = min(max(value, minmax[0]), minmax[1])

    @property
    def max_value(self) -> float:
        return self._max_value
    
    @max_value.setter
    def max_value(self, value: float) -> None:
        minmax: tuple[int, int] = (-9999, 9999) if self.unit == SourceType.VOLT else (-999, 999)
        self._max_value = min(max(value, minmax[0]), minmax[1])
