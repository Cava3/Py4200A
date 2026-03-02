"""
SMU.py - Python module defining the SMU class, an SMU type board equipped in the Keithley 4200A.
Author: Lucas LE DUDAL

This module defines the SMU class, which inherits from the Board class and represents a specific \
type of board (an SMU) equipped in the KI4200A. The SMU class provides methods and attributes specific \
to SMUs, such as voltage and current measurement capabilities.
"""
from .Board import Board
from ..consts import Status, BoardType

class SMU(Board):
    """
    This class represents a Source Measure Unit (SMU) board equipped in the Keithley 4200A.

    Attributes:
        name (str): The name of the SMU board (e.g., "SMU1", "SMU2")
        status (str): Current status of the SMU board (e.g., "Idle", "Measuring", "Error")
        type (BoardType): The type of the board, set to BoardType.SMU
        slot (int): The slot number where the SMU is installed in the instrument
        hp (bool): Indicates if the SMU is a high-power model (e.g. HPSMU1)

    """

    def __init__(self, name: str, hp: bool = False) -> None:
        """
        Initialize an SMU instance with the given name and set its type to BoardType.SMU.

        Args:
            name (str): The name of the SMU board (e.g., "SMU1", "SMU2").
        """
        self.status = Status.INITIALIZING
        self._name: str = name
        self.hp: bool = hp
        slot_str: str = name[-1]
        self._slot: int = int(slot_str) if slot_str.isdigit() else -1
        self.board_type: BoardType = BoardType.SMU
        self.status= Status.READY

    # === Factory ===

    @classmethod
    def of(cls, board: Board, hp: bool = False) -> "SMU":
        """
        Create an SMU instance from a generic Board instance.

        Args:
            board (Board): The generic Board instance to convert to an SMU.

        Returns:
            SMU: An instance of the SMU class.
        """
        smu = SMU(board.name, hp = hp)
        smu.status = board.status
        return smu

    # === Getters and setters ===
