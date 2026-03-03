"""
PMU_RPM.py - Python module defining the PMU_RPM class, an PMU_RPM type board equipped in the Keithley 4200A.
Author: Lucas LE DUDAL

This module defines the PMU_RPM class, which inherits from the Board class and represents a specific \
type of board (an PMU_RPM) equipped in the KI4200A. The PMU_RPM class provides methods and attributes\
specific to PMU_RPMs, such as [].
""" # TODO:                   ^
from .Board import Board
from ..consts import Status, BoardType

class PMU_RPM(Board):
    """
    This class represents a Power Management Unit - Remote Pulse Measure (PMU_RPM) board equipped in the Keithley 4200A.

    Attributes:
        name (str): The name of the PMU_RPM board (e.g., "CVU1", "CVU2")
        status (str): Current status of the PMU_RPM board (e.g., "Idle", "Measuring", "Error")
        type (BoardType): The type of the board, set to BoardType.PMU_RPM

    """

    def __init__(self, name: str) -> None:
        """
        Initialize an PMU_RPM instance with the given name and set its type to BoardType.PMU_RPM.

        Args:
            name (str): The name of the PMU_RPM board (e.g., "PMU1RPM1-1", "PMU1RPM1-2").
        """
        self.status = Status.INITIALIZING
        self._name: str = name
        self.board_type: BoardType = BoardType.PMU_RPM
        self.status= Status.READY
        s_slot = name[-1] + name[-3]
        self._slot = int(s_slot) if s_slot.isnumeric() else 0

    # === Factory ===

    @classmethod
    def of(cls, board: Board) -> "PMU_RPM":
        """
        Create an PMU_RPM instance from a generic Board instance.

        Args:
            board (Board): The generic Board instance to convert to an PMU_RPM.

        Returns:
            PMU_RPM: An instance of the PMU_RPM class.
        """
        cvu = PMU_RPM(board.name)
        cvu.status = board.status
        return cvu

    # === Getters and setters ===
