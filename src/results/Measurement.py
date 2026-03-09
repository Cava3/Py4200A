"""
Measurement.py - Python module defining the Measurement class to represent a specific measurement in the Keithley 4200A.
Author: Lucas LE DUDAL
"""
from ..consts import GraphPosition

class Measurement:
    """
    This class represents a measurement configuration and its associated data.

    Attributes:
        name (str): The name of the measurement.
        min_value (float): The minimum value for the measurement range or display.
        max_value (float): The maximum value for the measurement range or display.
        is_log_scale (bool): Indicates if the measurement should be handled/displayed in log scale.
    """

    def __init__(self, name: str, min_value: float = 0.0, max_value: float = 0.0, is_log_scale: bool = False) -> None:
        """
        Initialize a Measurement instance.

        Args:
            name (str): The name of the measurement.
            min_value (float): The minimum value. # TODO: Minmaxing
            max_value (float): The maximum value.
            is_log_scale (bool): True for logarithmic scale, False for linear.
        """
        self.name = name
        self.min_value = min_value
        self.max_value = max_value
        self.is_log_scale = is_log_scale

    def fetch_results(self) -> list[float]:
        """
        Fetch the measurement results from the instrument.
        
        Note: This method is not yet implemented. #TODO
        """
        raise NotImplementedError("The fetch_results method is not yet implemented.")
    
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
