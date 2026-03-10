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
        min_value (float): The minimum value for the measurement range or display.
        max_value (float): The maximum value for the measurement range or display.
        is_log_scale (bool): Indicates if the measurement should be handled/displayed in log scale.
    """

    def __init__(self, comm: Communications, name: str, min_value: float = 0.0, max_value: float = 0.0, is_log_scale: bool = False, unit: SourceType = SourceType.NONE) -> None:
        """
        Initialize a Measurement instance.

        Args:
            name (str): The name of the measurement.
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
        self.name = name
        self.min_value = min_value
        self.max_value = max_value
        self.is_log_scale = is_log_scale

    def getResultAt(self, index: int) -> float:
        """
        Fetch the measurement result at a specific index.

        Args:
            index (int): The index at which to fetch the measurement result.

        Returns:
            float: The measurement result at the specified index.
        """
        str_result: str = self._com.query(f"RD '{self.name}', {index}")
        self._com.checkForError()
        
        try:
            return float(str_result)
        except ValueError:
            raise ValueError(f'Invalid string for float conversion : {str_result}')


    def isResultReady(self, index: int) -> bool:
        """
        Check if the measurement result is ready at a specific index.

        Args:
            index (int): The index at which to check the measurement result.

        Returns:
            bool: True if the measurement result is ready, False otherwise.
        """
        return self.getResultAt(index) != 0.0


    def getAllResults(self) -> list[float]:
        """
        Fetch the measurement results from the instrument.

        Returns:
            list[float]: The list of measurement values retrieved from the instrument.
        """
        l_readings: list[float] = []
        index: int = 0
        while self.isResultReady(index):
            l_readings.append(self.getResultAt(index))
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
