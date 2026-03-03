"""
SMU.py - Python module defining the SMU class, an SMU type board equipped in the Keithley 4200A.
Author: Lucas LE DUDAL

This module defines the SMU class, which inherits from the Board class and represents a specific \
type of board (an SMU) equipped in the KI4200A. The SMU class provides methods and attributes specific \
to SMUs, such as voltage and current measurement capabilities.
"""
from .Board import Board
from ..consts import Status, BoardType, SourceType, SourceFunction
from ..instrcomms import Communications

class SMU(Board):
    """
    This class represents a Source Measure Unit (SMU) board equipped in the Keithley 4200A.

    Attributes:
        name (str): The name of the SMU board (e.g., "SMU1", "SMU2")
        status (str): Current status of the SMU board (e.g., "Idle", "Measuring", "Error")
        type (BoardType): The type of the board, set to BoardType.SMU
        slot (int): The slot number where the SMU is installed in the instrument
        hp (bool): Indicates if the SMU is a high-power model (e.g. HPSMU1)

        voltageMeasureName (str): The name of the voltage measurement
        currentMEasureName (str): The name of the current measurement
        sourceType (consts.SourceType): The type of source (VOLT, AMPERE, or COMMON)
        sourceFunction (consts.SourceFunction): The function to apply to the source (SWEEP, STEP, CONSTANT)
    """

    def __init__(self, name: str, comm: Communications, hp: bool = False) -> None:
        """
        Initialize an SMU instance with the given name and set its type to BoardType.SMU.

        Args:
            name (str): The name of the SMU board (e.g., "SMU1", "SMU2").
        """
        self.status = Status.INITIALIZING
        self._name: str = name
        self.hp: bool = hp
        slot_str: str = name[-1]
        self._comm = comm
        self._slot: int = int(slot_str) if slot_str.isdigit() else -1
        self.board_type: BoardType = BoardType.SMU

        self._voltageMeasureName: str = self.name+"V"
        self._currentMeasureName: str = self.name+"I"
        self._sourceType: SourceType = SourceType.NONE
        self._sourceFunction: SourceFunction = SourceFunction.NONE
        self.status= Status.READY

    def deactivate(self):
        """
        A function to deactivate (reset/power off) the SMU.
        """
        self._write("DE")
        self._write("CH"+str(self.slot))

    def setAsVoltmeter(self, voltageMeasureName: str = "") -> None:
        """
        Sets the current SMU to voltmeter only (no source, no ground)
        """
        # Store the measurement name
        if voltageMeasureName != "":
            self.voltageMeasureName = voltageMeasureName

        self._write("VM"+str(self.slot)+" "+self.voltageMeasureName)
        return
    
    def setAsSource(self):
        self._setDefinition()

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
        smu = SMU(board.name, comm=board._comm, hp = hp)
        smu.status = board.status
        return smu

    # === Private / Utils ===

    def _isDefinitionOk(self) -> bool:
        """
        Allows to check if the SMU definition is ready and okay.

        Returns:
            bool: True if data is complete, False if data is incomplete
        """
        return \
            self.voltageMeasureName != ""\
        and self.currentMeasureName != ""\
        and self.sourceType != SourceType.NONE\
        and (self.sourceFunction != SourceFunction.NONE or self.sourceType == SourceType.COMMON)
        
    def _setDefinition(self) -> None:
        """
        Sends the DE command to define the SMU settings.

        Raises:
            AttributeError: If the SMU settings are not properly defined. sourceType and sourceFunction\
            have to be set, and currentMeasureName and voltageMeasureName cannot be empty.
        """
        if not self._isDefinitionOk():
            raise AttributeError("SMU definition is incomplete. Please set all required attributes :\
                                  voltageMeasureName, currentMeasureName, sourceType, and sourceFunction\
                                  (if sourceType is not COMMON).")

        # Source type "COMMON" doesn't support source functions
        if self.sourceType == SourceType.COMMON:
            self.sourceFunction = SourceFunction.CONSTANT

        # Generate and send the command
        command: str = "CH"+str(self.slot)+" "+self.voltageMeasureName+" "+self.currentMeasureName+" "+str(self.sourceType.value)+" "+str(self.sourceFunction.value)
        self._write(command)
        return


    # === Getters and setters ===

    @property
    def voltageMeasureName(self) -> str:
        return self._voltageMeasureName
    
    @voltageMeasureName.setter
    def voltageMeasureName(self, value: str) -> None:
        self._voltageMeasureName = value

        if self._isDefinitionOk():
            self._setDefinition()

    @property
    def currentMeasureName(self) -> str:
        return self._currentMeasureName

    @currentMeasureName.setter
    def currentMeasureName(self, value: str) -> None:
        self._currentMeasureName = value

        if self._isDefinitionOk():
            self._setDefinition()

    @property
    def sourceType(self) -> SourceType:
        return self._sourceType
    
    @sourceType.setter
    def sourceType(self, value: SourceType) -> None:
        self._sourceType = value

        if self._isDefinitionOk():
            self._setDefinition()

    @property
    def sourceFunction(self) -> SourceFunction:
        return self._sourceFunction
    
    @sourceFunction.setter
    def sourceFunction(self, value: SourceFunction) -> None:
        self._sourceFunction = value

        if self._isDefinitionOk():
            self._setDefinition()
