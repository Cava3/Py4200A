"""
Boards.py - Python module defining the Board generic class, which represents a module or board equipped \
in the Keithley 4200A Semiconductor Characterization System.
Author: Lucas LE DUDAL

This module defines the Board class, which serves as a base class for specific types of boards (e.g., \
SMUs, PMUs) that can be equipped in the KI4200A. The Board class provides common attributes and methods \
that can be inherited and extended by specific board classes, allowing for a structured and modular \
approach to representing the various components of the instrument.
"""
from ..consts import Status, BoardType

class Board:
    """
    This class represents a generic board or module equipped in the Keithley 4200A.

    Attributes:
        alias (str): user-defined alias name
        board_type (BoardType): The type of board, detected from it's name
        name (str): The name of the board (e.g., "SMU1", "PMU2").
        status (str): Current status of the board (e.g., "Idle", "Measuring", "Error").
    """

    def __init__(self, name: str) -> None:
        """
        Initialize a Board instance with the given name and slot number.
        Args:
            name (str): The name of the board (e.g., "SMU1", "PMU2").
            slot (int): The slot number where the board is installed in the instrument.
        """
        self.status: Status = Status.INITIALIZING
        self._name: str = name
        self._alias: str = name
        self.board_type: BoardType = BoardType.NONE

        self.status = Status.CONFIGURING
        self.detect_type()
        self.status = Status.READY

    def detect_type(self) -> None:
        """
        Detect the type of the board based on its name and set the type attribute accordingly.
        This method can be extended to include more specific detection logic based on the instrument's \
        response or configuration.
        """ # TODO: PMU1RPM1-2
        if "SMU" in self.name.upper():
            self.board_type = BoardType.SMU
        elif "RPM" in self.name.upper():
            self.board_type = BoardType.RPM
        elif "PMU" in self.name.upper():
            self.board_type = BoardType.PMU
        elif "CVU" in self.name.upper():
            self.board_type = BoardType.CVU
        else:
            self.board_type = BoardType.NONE

    def __str__(self) -> str:
        return self.name
    
    # === Getters and setters ===

    @property
    def alias(self) -> str:
        return self._alias
    
    @alias.setter
    def alias(self, value: str) -> None:
        # TODO: SEND "DE" COMMAND
        self._alias = value

    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, value: str):
        raise Exception("Name is read-only and cannot be changed after initialization.")