"""
SMU.py - Python module defining the SMU class, an SMU type board equipped in the Keithley 4200A.
Author: Lucas LE DUDAL

This module defines the SMU class, which inherits from the Board class and represents a specific \
type of board (an SMU) equipped in the KI4200A. The SMU class provides methods and attributes specific \
to SMUs, such as voltage and current measurement capabilities.
"""
from .Board import Board
from ..consts import Status, BoardType, SourceType, SourceFunction, SMUMode, SweepType
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

    # === Creation ===
    def __init__(self, name: str, comm: Communications) -> None:
        """
        Initialize an SMU instance with the given name and set its type to BoardType.SMU.

        Args:
            name (str): The name of the SMU board (e.g., "SMU1", "SMU2").
        """
        # General usage
        self.status = Status.INITIALIZING
        self._name: str = name
        self.hp: bool = "HP" in name.upper()
        slot_str: str = name[-1]
        self._comm = comm
        self._slot: int = int(slot_str) if slot_str.isdigit() else -1
        self.board_type: BoardType = BoardType.SMU
        self._poweroff_after_test: bool = True

        # Channel definition
        self._smuType: SMUMode = SMUMode.VM if "SMU" in name.upper() else SMUMode.VS if "VS" in name.upper() else SMUMode.SMU
        self.voltageMeasureName: str = self.name+"V"
        self.currentMeasureName: str = self.name+"I"
        self.sourceType: SourceType = SourceType.NONE
        self.sourceFunction: SourceFunction = SourceFunction.NONE

        #Source setup
        self._compliance: float = 0.0
        
        self._constantValue: float = 0.0

        self._funcStart: float = 0.0
        self._funcStop: float = 0.0
        self._funcStep: float = 0.0
        self.sweepType: SweepType = SweepType.LINEAR
        self._numSteps: int = 0

        self.status= Status.READY

    # === Factory ===


    @classmethod
    def of(cls, board: Board) -> "SMU":
        """
        Create an SMU instance from a generic Board instance.

        Args:
            board (Board): The generic Board instance to convert to an SMU.

        Returns:
            SMU: An instance of the SMU class.
        """
        smu = SMU(board.name, comm=board._comm)
        smu.status = board.status
        return smu

    # === Public ===
    # Channel definition
    def deactivate(self):
        """
        A function to deactivate (reset/power off) the SMU.

        Raises:
            ValueError: If the instrument returns an error after sending the command.
        """
        self.smuType = SMUMode.SMU
        self._write("DE")
        self._write("CH"+str(self.slot))

        if self._comm.hasError():
            print(self._comm.getError())
            self._comm.clearError()
            raise ValueError("Deactivation failed. Please check the settings and try again.")

    def setupVoltmeter(self, voltageMeasureName: str = "") -> None:
        """
        Sets the current SMU to voltmeter only (no source, no ground)

        Args:
            voltageMeasureName (str): Name of the voltage measurement for later access. Defaults to self.voltageMeasureName

        Raises:
            AttributeError: If the SMU settings are not properly defined. currentMeasureName cannot be empty.
            ValueError: If the instrument returns an error after sending the command.
        """
        # Store the measurement name
        self.voltageMeasureName = voltageMeasureName if voltageMeasureName != "" else self.voltageMeasureName

        # Attribute checking
        if not self._isDefinitionOk(SMUMode.SMU):
            raise AttributeError("VM definition is incomplete. Please set all required attributes :\
                                  voltageMeasureName")

        # Generate and send the commands
        self.smuType = SMUMode.VM
        self._write("DE")
        self._write("VM" + str(self.slot) + ", '" + self.voltageMeasureName + "'")

        if self._comm.hasError():
            print(self._comm.getError())
            self._comm.clearError()
            raise ValueError("Voltmeter setup failed. Please check the settings and try again.")
    
    def setupVoltageSource(self, voltageMeasureName: str = "", sourceFunction: SourceFunction = SourceFunction.NONE) -> None:
        """
        Sets the current SMU to voltage source (no current source or measurement)

        Args:
            voltageMeasureName (str): Name of the voltage measurement for later access. Defaults to self.voltageMeasureName
            sourceFunction (SourceFunction): The source functions to use (sweep, step, constant). Defaults to self.sourceFunction
        
        Raises:
            AttributeError: If the SMU settings are not properly defined. currentMeasureName and sourceFunction are required.
            ValueError: If the instrument returns an error after sending the command.
        """
        # Attribute saving
        self.voltageMeasureName = voltageMeasureName if voltageMeasureName != "" else self.voltageMeasureName
        self.sourceFunction = sourceFunction if sourceFunction != SourceFunction.NONE else self.sourceFunction

        # Attribute checking
        if not self._isDefinitionOk(SMUMode.SMU):
            raise AttributeError("VS definition is incomplete. Please set all required attributes :\
                                  voltageMeasureName, and sourceFunction.")

        # Generate and send the commands
        self.smuType = SMUMode.VS
        self._write("DE")
        self._write("VS" + str(self.slot) + ", '" + self.voltageMeasureName + "', " + str(self.sourceFunction.value))

        if self._comm.hasError():
            print(self._comm.getError())
            self._comm.clearError()
            raise ValueError("Voltage source setup failed. Please check the settings and try again.")
    
    def setupSMU(self, voltageMeasureName: str = "", currentMeasureName: str = "", sourceType: SourceType = SourceType.NONE, sourceFunction: SourceFunction = SourceFunction.NONE) -> None:
        """
        Sends the DE command to define the SMU settings.

        Args:
            voltageMeasureName (str): Name of the voltage measurement for later access. Defaults to self.voltageMeasureName
            currentMeasureName (str): Name of the current measurement for later access. Defaults to self.currentMeasureName
            sourceType (SourceType): The type of source (current or voltage). Defaults to self.sourceType
            sourceFunction (SourceFunction): The source functions to use (sweep, step, constant). Defaults to self.sourceFunction

        Raises:
            AttributeError: If the SMU settings are not properly defined. All attributes are required for SMU type.
            ValueError: If the instrument returns an error after sending the command.
        """
        # Attribute saving
        self.voltageMeasureName = voltageMeasureName if voltageMeasureName != "" else self.voltageMeasureName
        self.currentMeasureName = currentMeasureName if currentMeasureName != "" else self.currentMeasureName
        self.sourceType = sourceType if sourceType != SourceType.NONE else self.sourceType
        self.sourceFunction = sourceFunction if sourceFunction != SourceFunction.NONE else self.sourceFunction

        # Attribute checking
        if not self._isDefinitionOk(SMUMode.SMU):
            raise AttributeError("SMU definition is incomplete. Please set all required attributes :\
                                  voltageMeasureName, currentMeasureName, sourceType, and sourceFunction.")

        # Source type "COMMON" doesn't support source functions
        if self.sourceType == SourceType.COMMON:
            self.sourceFunction = SourceFunction.CONSTANT

        # Generate and send the commands
        self.smuType = SMUMode.SMU
        command: str = "CH" + str(self.slot) + ", '" + self.voltageMeasureName + "', '" + self.currentMeasureName +\
                       "', " + str(self.sourceType.value) + ", " + str(self.sourceFunction.value)
        self._write("DE")
        self._write(command)

        if self._comm.hasError():
            print(self._comm.getError())
            self._comm.clearError()
            raise ValueError("SMU setup failed. Please check the settings and try again.")

    # Source setup
    def setConstantSourceValue(self, value: float = 0.0, compliance: float = 0.0) -> None:
        """
        Sets the source value of the SMU to a constant value. The source value can be either current
        or voltage depending on the sourceType attribute.

        Args:
            value (float): The value to set for the source. Defaults to self.currentValue or self.voltageValue.
            compliance (float): The compliance value to set for the source. Defaults to self.compliance.

        Raises:
            AttributeError: If the SMU settings are not properly defined (SMUmode and sourceFunction).
            ValueError: If the instrument returns an error after sending the command.
        """
        self._write("DE")
        # No source for VM type
        if self.smuType == SMUMode.VM:
            raise AttributeError("VM type SMU cannot source current nor voltage")
        
        # VS has a special command
        elif self.smuType == SMUMode.VS and self.sourceFunction == SourceFunction.CONSTANT:
            self.voltageValue = value if value != 0.0 else self.voltageValue
            self._write("CS" + str(self.slot) + ", " + str(self.voltageValue))

        # For SMU, the command depends on the sourceFunction and sourceType
        elif self.sourceFunction == SourceFunction.CONSTANT and self.sourceType in [SourceType.AMPERE, SourceType.VOLT]:
            prefix: str = "VC" if self.sourceType == SourceType.VOLT else "IC"

            # Save attributes + minmax them
            if self.sourceType == SourceType.VOLT:
                self.voltageValue = value if value != 0.0 else self.voltageValue
                value = self.voltageValue
                self.compliance = compliance if compliance != 0.0 else self.compliance
                compliance = self.compliance
            else:
                self.currentValue = value if value != 0.0 else self.currentValue
                value = self.currentValue
                self.compliance = compliance if compliance != 0.0 else self.compliance
                compliance = self.compliance

            self._write(prefix + str(self.slot) + ", " + str(value) + ", " + str(compliance))

        # For other source functions
        else:
            raise AttributeError("For source functions other than CONSTANT, please use sweepValues or stepValues.")

        if self._comm.hasError():
            print(self._comm.getError())
            self._comm.clearError()
            raise ValueError("Setting constant source value failed.")


    def setSweepFunction(self, sweepType: SweepType = SweepType.LINEAR, start: float = 0.0, stop: float = 0.0, step: float = 0.0, compliance: float = 0.0) -> None:
        """
        Sets the source function of the SMU to a sweep function. The source can be either current
        or voltage depending on the sourceType attribute.

        Args:
            sweepType (SweepType): The type of sweep to perform (linear, log10, log25, log50). Defaults to SweepType.LINEAR.
            start (float): The starting value of the sweep. Defaults to 0.0.
            stop (float): The stopping value of the sweep. Defaults to 0.0.
            step (float): The step value of the sweep. Defaults to 0.0.
            compliance (float): The compliance value to set for the source. Defaults to self.compliance.

        Raises:
            AttributeError: If the SMU settings are not properly defined.
            ValueError: If the instrument returns an error after sending the command.
        """
        # Attribute checking
        if self.smuType == SMUMode.VM or (self.smuType == SMUMode.VS and self.sourceType != SourceType.VOLT):
            raise AttributeError("SMU type and source unit are not compatible.")
        elif self.sourceFunction != SourceFunction.SWEEP:
            raise AttributeError("Source function must be set to SWEEP to use this method.")
        elif self.sourceType not in [SourceType.AMPERE, SourceType.VOLT]:
            raise AttributeError("Source type must be set to AMPERE or VOLT to use this method.")

        # Save attributes
        self.funcStart = start if start != 0.0 else self.funcStart
        self.funcStop = stop if stop != 0.0 else self.funcStop
        self.funcStep = step if step != 0.0 else self.funcStep
        self.compliance = compliance if compliance != 0.0 else self.compliance
        self.sweepType = sweepType

        # Generate command
        prefix: str = "VR" if self.smuType == SMUMode.VS else "IR"
        command: str = prefix + str(self.sweepType.value) + ", " + str(self.funcStart) + ", " +\
              str(self.funcStop) + ", " + str(self.funcStep) + ", " + str(self.compliance)

        self._write("DE")
        self._write(command)

        if self._comm.hasError():
            print(self._comm.getError())
            self._comm.clearError()
            raise ValueError("Setting sweep function failed.")

    def setStepFunction2(self, start: float = 0.0, step: float = 0.0, numSteps: int = 0, compliance: float = 0.0) -> None:
        """
        Sets the source function of the SMU to a step function. The source can be either current
        or voltage depending on the sourceType attribute.

        Args:
            start (float): The starting value of the step function. Defaults to 0.0.
            step (float): The step value of the step function. Defaults to 0.0.
            numSteps (int): The number of steps to perform. Defaults to 0. Max 32.
            compliance (float): The compliance value to set for the source. Defaults to self.compliance.

        Raises:
            AttributeError: If the SMU settings are not properly defined.
            ValueError: If the instrument returns an error after sending the command.
        """
        # Attribute checking
        if self.smuType == SMUMode.VM or (self.smuType == SMUMode.VS and self.sourceType != SourceType.VOLT):
            raise AttributeError("SMU type and source unit are not compatible.")
        elif self.sourceFunction != SourceFunction.STEP:
            raise AttributeError("Source function must be set to STEP to use this method.")
        elif self.sourceType not in [SourceType.AMPERE, SourceType.VOLT]:
            raise AttributeError("Source type must be set to AMPERE or VOLT to use this method.")

        # Save attributes
        self.funcStart = start if start != 0.0 else self.funcStart
        self.funcStep = step if step != 0.0 else self.funcStep
        self.compliance = compliance if compliance != 0.0 else self.compliance
        self.numSteps = numSteps if numSteps != 0 else self.numSteps

        # Generate command
        prefix: str = "VP" if self.smuType == SMUMode.VS else "IP"
        command: str = prefix + str(self.slot) + ", " + str(self.funcStart) + ", " +\
              str(self.funcStep) + ", " + str(numSteps) + ", " + str(self.compliance)

        self._write("DE")
        self._write(command)

        if self._comm.hasError():
            print(self._comm.getError())
            self._comm.clearError()
            raise ValueError("Setting step function failed.")

    def setStepFunction(self, start: float = 0.0, stop: float = 0.0, step: int = 0, compliance: float = 0.0) -> None:
        """
        Sets the source function of the SMU to a step function. The source can be either current
        or voltage depending on the sourceType attribute.
        Similar to setStepFunction, but with a defined stop value instead of number of steps.
        Uses the setStepFunction2 method to set the function, after calculating the number of steps from the stop value.

        Args:
            start (float): The starting value of the step function. Defaults to 0.0.
            stop (float): The stopping value of the step function. Defaults to 0.0.
            step (int): The amount of units to step. Defaults to 0.
            compliance (float): The compliance value to set for the source. Defaults to self.compliance.

        Raises:
            AttributeError: If the SMU settings are not properly defined.
            ValueError: If the instrument returns an error after sending the command.
        """
        numStep = int(abs(stop - start) / step) if step != 0 else 0
        self.setStepFunction2(start = start, step = step, numSteps = numStep, compliance = compliance)

    # TODO: Lists

    # === Private / Utils ===

    def _isDefinitionOk(self, type: SMUMode = SMUMode.SMU) -> bool:
        """
        Allows to check if the attribute is okay for given SMU type.

        Returns:
            bool: True if data is complete, False if data is incomplete
        """
        # voltageMeasureName is mandatory for all types
        # sourceFunction is not mandatory for VM
        # currentMeasureName is mandatory for SMU
        # sourceType is mandatory for SMU
        return \
            self.voltageMeasureName != "" and\
            (self.sourceFunction != SourceFunction.NONE or self.smuType == SMUMode.VM) and\
            (self.currentMeasureName != "" or self.smuType != SMUMode.SMU) and\
            (self.sourceType != SourceType.NONE or self.smuType != SMUMode.SMU)


    # === Getters/Setters ===

    @property
    def smuType(self) -> SMUMode:
        return self._smuType
    
    @smuType.setter
    def smuType(self, value: SMUMode):
        if self._smuType == value:
            return

        self._write("MP " + str(self.slot) + ", " + value.name + str(self.slot))

        if self._comm.hasError():
            print(self._comm.getError())
            self._comm.clearError()
            raise ValueError("Type changing failed : make sure 'channel number' = 'slot number' in KCon")

        self._smuType = value

    @property
    def constantValue(self) -> float:
        return self._constantValue
    
    @constantValue.setter
    def constantValue(self, value: float):
        if self.sourceFunction != SourceFunction.CONSTANT:
            raise AttributeError("Source function must be set to CONSTANT to use this attribute.")

        minmax: tuple[float, float] = (-210.0, 210.0) if self.sourceType == SourceType.VOLT else (-0.105, 0.105) if not self.hp else (-1.05, 1.05)
        self._constantValue = min(max(value, minmax[0]), minmax[1])

    @property
    def compliance(self) -> float:
        return self._compliance

    @compliance.setter
    def compliance(self, value: float):
        minmax: tuple[float, float] = (-210.0, 210.0) if self.sourceType == SourceType.VOLT else (-0.105, 0.105) if not self.hp else (-1.05, 1.05)
        self._compliance = min(max(value, minmax[0]), minmax[1])

    @property
    def poweroffAfterTest(self) -> bool:
        return self._poweroff_after_test

    @poweroffAfterTest.setter
    def poweroffAfterTest(self, value: bool):
        self._write("ST " + str(self.slot) + ", " + str(int(value)))

        if self._comm.hasError():
            print(self._comm.getError())
            self._comm.clearError()
            raise ValueError("Poweroff after test setting failed to set.")

        self._poweroff_after_test = value

    @property
    def funcStart(self) -> float:
        return self._funcStart

    @funcStart.setter
    def funcStart(self, value: float):
        minmax: tuple[float, float] = (-210.0, 210.0) if self.sourceType == SourceType.VOLT else (-1.05, 1.05) if self.hp else (-0.105, 0.105)
        self._funcStart = min(max(value, minmax[0]), minmax[1])

    @property
    def funcStop(self) -> float:
        return self._funcStop
    
    @funcStop.setter
    def funcStop(self, value: float):
        minmax: tuple[float, float] = (-210.0, 210.0) if self.sourceType == SourceType.VOLT else (-1.05, 1.05) if self.hp else (-0.105, 0.105)
        self._funcStop = min(max(value, minmax[0]), minmax[1])

    @property
    def numSteps(self) -> int:
        return self._numSteps
    
    @numSteps.setter
    def numSteps(self, value: int):
        self._numSteps = min(max(value, 0), 32)
