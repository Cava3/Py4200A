"""
CVU.py - Python module defining the CVU class, an CVU type board equipped in the Keithley 4200A.
Author: Lucas LE DUDAL

This module defines the CVU class, which inherits from the Board class and represents a specific \
type of board (an CVU) equipped in the KI4200A. The CVU class provides methods and attributes specific \
to CVUs, such as [].
""" # TODO:      ^
from .Board import Board
from ..consts import Status, BoardType

class CVU(Board): # TODO:   v
    """
    This class represents a [] (CVU) board equipped in the Keithley 4200A.

    Attributes:
        name (str): The name of the CVU board (e.g., "CVU1", "CVU2")
        status (str): Current status of the CVU board (e.g., "Idle", "Measuring", "Error")
        type (BoardType): The type of the board, set to BoardType.CVU

    """

    def __init__(self, name: str) -> None:
        """
        Initialize an CVU instance with the given name and set its type to BoardType.CVU.

        Args:
            name (str): The name of the CVU board (e.g., "CVU1", "CVU2").
        """
        self.status = Status.INITIALIZING
        self._name: str = name
        self.board_type: BoardType = BoardType.CVU
        self.status= Status.READY

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
        cvu = CVU(board.name)
        cvu.status = board.status
        return cvu

    # === Getters and setters ===
