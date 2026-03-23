"""
CVU.py - Python module defining the CVU class, an CVU type board equipped in the Keithley 4200A.
Author: Lucas LE DUDAL

This module defines the CVU class, which inherits from the Board class and represents a specific \
type of board (a CVU) equipped in the KI4200A.
"""

from ..instrcomms import Communications
from .Board import Board
from ..consts import Status, BoardType

class CVU(Board): # TODO:   v
    """
    This class represents a Capacitance-Voltage Unit (CVU) board equipped in the Keithley 4200A.
    """

    def __init__(self, name: str, comm: Communications) -> None:
        """
        Initialize an CVU instance with the given name and set its type to BoardType.CVU.

        Args:
            name (str): The name of the CVU board (e.g., "CVU1", "CVU2").
            comm (Communications): The communication object used to send commands.
        """
        super().__init__(name, comm)
        self.status = Status.INITIALIZING
        self._name: str = name
        self.board_type: BoardType = BoardType.CVU
        self.status = Status.READY

    # === Factory ===

    @classmethod
    def of(cls, board: Board) -> "CVU":
        """
        Create an CVU instance from a generic Board instance.

        Args:
            board (Board): The generic Board instance to convert to an CVU.

        Returns:
            CVU: An instance of the CVU class.
        """
        cvu = CVU(board.name, board._comm)
        cvu.status = board.status
        return cvu

    # === Getters and setters ===
