"""
Boards.py - Python module defining the Board generic class, which represents a module or board equipped \
in the Keithley 4200A Semiconductor Characterization System.
Author: Lucas LE DUDAL

This module defines the Board class, which serves as a base class for specific types of boards (e.g., \
SMUs, PMUs) that can be equipped in the KI4200A. The Board class provides common attributes and methods \
that can be inherited and extended by specific board classes, allowing for a structured and modular \
approach to representing the various components of the instrument.
"""
from ..results import Measurement
from ..consts import Status, BoardType
from ..instrcomms import Communications

class Board:
    """
    This class represents a generic board or module equipped in the Keithley 4200A.
    """

    def __init__(self, name: str, comm: Communications) -> None:
        """
        Initialize a Board instance.

        Args:
            name (str): The name of the board (e.g., "SMU1", "PMU2").
            comm (Communications): The communication object used to send commands.
        """
        self.status: Status = Status.INITIALIZING
        self._name: str = name
        self.board_type: BoardType = BoardType.NONE
        self._slot = 0
        self._comm = comm
        self.measurements: list[Measurement] = []
        self.status = Status.CONFIGURING
        self.detectType()
        self.status = Status.READY

    def detectType(self) -> None:
        """
        Detect the type of the board based on its name and set the type attribute accordingly.
        This method can be extended to include more specific detection logic based on the instrument's \
        response or configuration.
        """
        if "SMU" in self.name.upper() or "VS" in self.name.upper() or "VM" in self.name.upper():
            self.board_type = BoardType.SMU
        elif "CVU" in self.name.upper():
            self.board_type = BoardType.CVU
        elif "PMU" in self.name.upper() and "RPM" in self.name.upper():
            self.board_type = BoardType.PMU_RPM
        else:
            self.board_type = BoardType.NONE

    # === Private / Utils ===

    def _write(self, command: str) -> None:
        """
        AS A USER, PREFER USING THE FUNCTION FROM THE KI4200 CLASS

        Send a command to the instrument but doesn't read an answer.  
        Only for GPIB, as TCPIP always return a value, or "ACK".  
        For TCPIP, redirects to `query`.
        
        Args:
            command (str): The command to send.
        """
        if self._comm.con_type == 1:
            self._comm.write(command)
        else :
            self._query(command)


    def _query(self, command: str) -> str:
        """
        AS A USER, PREFER USING THE FUNCTION FROM THE KI4200 CLASS

        Send a command to the instrument and return the response.

        Args:
            command (str): The command to send to the instrument.
        Returns:
            str: The response from the instrument.
        """
        return self._comm.query(command)

    def __str__(self) -> str:
        """
        Returns the string representation of the board (its name).
        """
        return self.name
    
    def __eq__(self, other: object) -> bool:
        """
        Check equality based on the board's name.
        """
        return isinstance(other, Board) and self.name == other.name
    
    # === Getters and setters ===

    @property
    def name(self) -> str:
        """The board identifier as reported by the instrument (e.g. ``"SMU1"``). Read-only."""
        return self._name

    @name.setter
    def name(self, value: str):
        raise Exception("Name is read-only and cannot be changed after initialization.")

    @property
    def slot(self) -> int:
        """Physical slot number where the board is installed in the mainframe. Read-only."""
        return self._slot

    @slot.setter
    def slot(self, value: int):
        raise Exception("Slot is read-only and cannot be changed virtualy. Move the card physically.")
