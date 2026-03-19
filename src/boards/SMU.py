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
from ..results import Measurement
from ..error import KXCILimitationError

class SMU(Board):
    """
    This class represents a Source Measure Unit (SMU) board equipped in the Keithley 4200A.

    Attributes:
        name (str): The name of the SMU board (e.g., "SMU1", "SMU2")
        status (str): Current status of the SMU board (e.g., "Idle", "Measuring", "Error")
        slot (int): The slot number where the SMU is installed in the instrument
        hp (bool): Indicates if the SMU is a high-power model (e.g. HPSMU1)
        smu_type (SMUMode): The specific mode of the SMU (e.g., VM, VS, or SMU)
        measurements (list[Measurement]): List of measurements associated with this SMU (e.g., voltage, current)
        delay_before_measure_during_sweep (float): The delay before measuring during a sweep
        hold_before_sweep_during_step (float): The delay before sweeping during a step
        wait_time_after_constant_before_stepping (float): The delay after a constant before stepping
        power_off_after_test (bool): Indicates if the SMU should be powered off after a test

        voltageMeasurement (Measurement): The voltage measurement
        currentMeasurement (Measurement): The current measurement
        sourceType (consts.SourceType): The type of source (VOLT, AMPERE, or COMMON)
        sourceFunction (consts.SourceFunction): The function to apply to the source (SWEEP, STEP, CONSTANT)
    """

    stepper_index: int = 0

    # === Creation ===
    def __init__(self, name: str, comm: Communications) -> None:
        """
        Initialize an SMU instance with the given name and set its type to BoardType.SMU.

        Args:
            name (str): The name of the SMU board (e.g., "SMU1", "SMU2").
        """
        super().__init__(name, comm)
        # General usage
        self.status = Status.INITIALIZING
        self.hp: bool = "HP" in name.upper()
        slot_str: str = name[-1]
        self._slot: int = int(slot_str) if slot_str.isdigit() else 0
        self.board_type: BoardType = BoardType.SMU

        # Channel definition
        self.status = Status.CONFIGURING
        self._smu_type: SMUMode = SMUMode.VM if "VM" in name.upper() else SMUMode.VS if "VS" in name.upper() else SMUMode.SMU
        self.voltage_measurement: Measurement = Measurement(comm, self.name+"V", unit=SourceType.VOLT)
        self.current_measurement: Measurement = Measurement(comm, self.name+"I", unit=SourceType.AMPERE)
        self.source_type: SourceType = SourceType.NONE
        self.source_function: SourceFunction = SourceFunction.NONE
        self._poweroff_after_test: bool = True
        self.measurements: list[Measurement] = [self.voltage_measurement, self.current_measurement]
        self._stepper_index: int = 0

        #Source setup
        self._compliance: float = 0.0
        
        self._constant_value: float = 0.0

        self._func_start: float = 0.0
        self._func_stop: float = 0.0
        self._funcStep: float = 0.0
        self.sweep_type: SweepType = SweepType.LINEAR
        self._num_steps: int = 0
        self._delay_before_measure_during_sweep: float = 0.0
        self._hold_before_sweep_during_step: float = 0.0
        self._wait_time_after_constant_before_stepping: float = 0.0

        self.status = Status.READY

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
    def deactivate(self) -> None:
        """
        A function to deactivate (reset/power off) the SMU.

        Raises:
            KXCIConsoleError: If the instrument returns an error after sending the command.
        """
        self.smu_type = SMUMode.SMU
        self._write("DE")
        self._write("CH"+str(self.slot))

        self._comm.checkForError()

    def setupVoltmeter(self, voltage_measure_name: str = "") -> None:
        """
        Sets the current SMU to voltmeter only (no source, no ground)

        Args:
            voltage_measure_name (str): Name of the voltage measurement for later access. Defaults to self.voltage_measurement.name

        Raises:
            AttributeError: If the SMU settings are not properly defined. currentMeasureName cannot be empty.
            KXCIConsoleError: If the instrument returns an error after sending the command.
        """
        # Store the measurement name
        self.voltage_measurement.name = voltage_measure_name if voltage_measure_name != "" else self.voltage_measurement.name

        # Attribute checking
        if not self._isDefinitionOk(SMUMode.VM):
            raise AttributeError("VM definition is incomplete. Please set all required attributes :\
                                  voltageMeasureName")

        # Generate and send the commands
        self.smu_type = SMUMode.VM
        self._write("DE")
        self._write("VM" + str(self.slot) + ", '" + self.voltage_measurement.name + "'")

        self._comm.checkForError()
    
    def setupVoltageSource(self, voltage_measure_name: str = "", source_function: SourceFunction = SourceFunction.NONE) -> None:
        """
        Sets the current SMU to voltage source (no current source or measurement)

        Args:
            voltage_measure_name (str): Name of the voltage measurement for later access. Defaults to self.voltage_measurement.name
            source_function (SourceFunction): The source functions to use (sweep, step, constant). Defaults to self.source_function
        
        Raises:
            AttributeError: If the SMU settings are not properly defined. current_measure_name and sourceFunction are required.
            KXCIConsoleError: If the instrument returns an error after sending the command.
        """

        # Attribute saving
        self.voltage_measurement.name = voltage_measure_name if voltage_measure_name != "" else self.voltage_measurement.name
        self.source_function = source_function if source_function != SourceFunction.NONE else self.source_function

        # Attribute checking
        if not self._isDefinitionOk(SMUMode.VS):
            raise AttributeError("VS definition is incomplete. Please set all required attributes :\
                                  voltage_measure_name, and source_function.")

        # Generate and send the commands
        self.smu_type = SMUMode.VS
        self.source_type = SourceType.VOLT
        self._write("DE")
        self._write("VS" + str(self.slot) + ", '" + self.voltage_measurement.name + "', " + str(self.source_function.value))

        self._comm.checkForError()

        # Stepper index
        SMU.stepper_index += 1
        self._stepper_index = SMU.stepper_index
    
    def setupSMU(self, voltage_measure_name: str = "", current_measure_name: str = "", source_type: SourceType = SourceType.NONE, source_function: SourceFunction = SourceFunction.NONE) -> None:
        """
        Sends the DE command to define the SMU settings.

        Args:
            voltage_measure_name (str): Name of the voltage measurement for later access. Defaults to self.voltage_measurement.name
            current_measure_name (str): Name of the current measurement for later access. Defaults to self.current_measurement.name
            source_type (SourceType): The type of source (current or voltage). Defaults to self.source_type
            source_function (SourceFunction): The source functions to use (sweep, step, constant). Defaults to self.source_function

        Raises:
            AttributeError: If the SMU settings are not properly defined. All attributes are required for SMU type.
            KXCIConsoleError: If the instrument returns an error after sending the command.
        """
        # Attribute saving
        self.voltage_measurement.name = voltage_measure_name if voltage_measure_name != "" else self.voltage_measurement.name
        self.current_measurement.name = current_measure_name if current_measure_name != "" else self.current_measurement.name
        self.source_type = source_type if source_type != SourceType.NONE else self.source_type
        self.source_function = source_function if source_function != SourceFunction.NONE else self.source_function

        # Attribute checking
        if not self._isDefinitionOk(SMUMode.SMU):
            raise AttributeError("SMU definition is incomplete. Please set all required attributes :\
                                  voltage_measure_name, current_measure_name, source_type, and source_function.")

        # Source type "COMMON" doesn't support source functions
        if self.source_type == SourceType.COMMON:
            self.source_function = SourceFunction.CONSTANT

        # Generate and send the commands
        self.smu_type = SMUMode.SMU
        command: str = "CH" + str(self.slot) + ", '" + self.voltage_measurement.name + "', '" + self.current_measurement.name +\
                       "', " + str(self.source_type.value) + ", " + str(self.source_function.value)
        self._write("DE")
        self._write(command)

        self._comm.checkForError()

    # Source setup
    def setConstantSourceValue(self, value: float = 0.0, compliance: float = 0.0) -> None:
        """
        Sets the source value of the SMU to a constant value. The source value can be either current
        or voltage depending on the sourceType attribute.

        Args:
            value (float): The value to set for the source. Defaults to 0.0.
            compliance (float): The compliance value to set for the source. Defaults to self.compliance.

        Raises:
            AttributeError: If the SMU settings are not properly defined (SMUmode and sourceFunction).
            KXCIConsoleError: If the instrument returns an error after sending the command.
        """
        self._write("SS")
        # No source for VM type
        if self.smu_type == SMUMode.VM:
            raise AttributeError("VM type SMU cannot source current nor voltage")
        
        # VS has a special command
        if self.smu_type == SMUMode.VS and self.source_function == SourceFunction.CONSTANT:
            self.constant_value = value if value != 0.0 else self.constant_value
            self._write("SC" + str(self.slot) + ", " + str(self.constant_value))

        # For SMU, the command depends on the sourceFunction and sourceType
        elif self.source_function == SourceFunction.CONSTANT and self.source_type in [SourceType.AMPERE, SourceType.VOLT]:
            prefix: str = "VC" if self.source_type == SourceType.VOLT else "IC"

            # Save attributes
            self.constant_value = value if value != 0.0 else self.constant_value
            self.compliance = compliance if compliance != 0.0 else self.compliance

            self._write(prefix + str(self.slot) + ", " + str(self.constant_value) + ", " + str(self.compliance))

        # For other source functions
        else:
            raise AttributeError("For source functions other than CONSTANT, please use sweepValues or stepValues.")

        self._comm.checkForError()


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
            KXCIConsoleError: If the instrument returns an error after sending the command.
        """
        # Attribute checking
        if self.smu_type == SMUMode.VM or (self.smu_type == SMUMode.VS and self.source_type != SourceType.VOLT):
            raise AttributeError("SMU type and source unit are not compatible.")
        if self.source_function != SourceFunction.SWEEP:
            raise AttributeError("Source function must be set to SWEEP to use this method.")
        if self.source_type not in [SourceType.AMPERE, SourceType.VOLT]:
            raise AttributeError("Source type must be set to AMPERE or VOLT to use this method.")
        if step == 0.0 or start == stop:
            raise AttributeError("Step value cannot be 0 and start and stop values cannot be the same for a sweep function.")
        if int(abs(stop - start) / step) > 1024:
            raise KXCILimitationError("The number of steps in a sweep cannot exceed 1024. Please adjust the step value or the start/stop values.")

        # Save attributes
        self.func_start = start if start != 0.0 else self.func_start
        self.func_stop = stop if stop != 0.0 else self.func_stop
        self.func_step = step if step != 0.0 else self.func_step
        self.compliance = compliance if compliance != 0.0 else self.compliance
        self.sweep_type = sweepType

        # Generate command
        prefix: str = "VR" if self.source_type == SourceType.VOLT else "IR"
        command: str = prefix + str(self.sweep_type.value) + ", " + str(self.func_start) + ", " + str(self.func_stop)
        if self.sweep_type == SweepType.LINEAR:
            command += ", " + str(self.func_step) + ", " + str(self.compliance)

        self._write("SS")
        self._write(command)

        self._comm.checkForError()

        # Update measurements
        if self.source_type == SourceType.VOLT:
            self.voltage_measurement.min_value = min(self.func_start, self.func_stop)
            self.voltage_measurement.max_value = max(self.func_start, self.func_stop)
            self.current_measurement.min_value = -abs(self.compliance)
            self.current_measurement.max_value = abs(self.compliance)
        elif self.source_type == SourceType.AMPERE:
            self.current_measurement.min_value = min(self.func_start, self.func_stop)
            self.current_measurement.max_value = max(self.func_start, self.func_stop)
            self.voltage_measurement.min_value = -abs(self.compliance)
            self.voltage_measurement.max_value = abs(self.compliance)


    def setStepFunction2(self, start: float = 0.0, step: float = 0.0, num_steps: int = 0, compliance: float = 0.0) -> None:
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
            KXCIConsoleError: If the instrument returns an error after sending the command.
        """
        # Attribute checking
        if self.smu_type == SMUMode.VM or (self.smu_type == SMUMode.VS and self.source_type != SourceType.VOLT):
            raise AttributeError("SMU type and source unit are not compatible.")
        elif self.source_function != SourceFunction.STEP:
            raise AttributeError("Source function must be set to STEP to use this method.")
        elif self.source_type not in [SourceType.AMPERE, SourceType.VOLT]:
            raise AttributeError("Source type must be set to AMPERE or VOLT to use this method.")

        # Save attributes
        self.func_start = start if start != 0.0 else self.func_start
        self.func_step = step if step != 0.0 else self.func_step
        self.compliance = compliance if compliance != 0.0 else self.compliance
        self.num_steps = num_steps if num_steps != 0 else self.num_steps

        # Generate command
        prefix: str = "VP" if self.source_type == SourceType.VOLT else "IP"
        command: str = f"{prefix} {self.func_start}, {self.func_step}, {self.num_steps}, {self.compliance}, {self.stepper_index}"

        self._write("SS")
        self._write(command)

        self._comm.checkForError()

        # Update measurements
        if self.source_type == SourceType.VOLT:
            self.voltage_measurement.min_value = min(self.func_start, self.func_start + self.func_step * self.num_steps)
            self.voltage_measurement.max_value = max(self.func_start, self.func_start + self.func_step * self.num_steps)
            self.current_measurement.min_value = -abs(self.compliance)
            self.current_measurement.max_value = abs(self.compliance)
        elif self.source_type == SourceType.AMPERE:
            self.current_measurement.min_value = min(self.func_start, self.func_start + self.func_step * self.num_steps)
            self.current_measurement.max_value = max(self.func_start, self.func_start + self.func_step * self.num_steps)
            self.voltage_measurement.min_value = -abs(self.compliance)
            self.voltage_measurement.max_value = abs(self.compliance)

    def setStepFunction(self, start: float = 0.0, stop: float = 0.0, step: float = 0.0, compliance: float = 0.0) -> None:
        """
        Sets the source function of the SMU to a step function. The source can be either current
        or voltage depending on the sourceType attribute.
        Similar to setStepFunction, but with a defined stop value instead of number of steps.
        Uses the setStepFunction2 method to set the function, after calculating the number of steps from the stop value.

        Args:
            start (float): The starting value of the step function. Defaults to 0.0.
            stop (float): The stopping value of the step function. Defaults to 0.0.
            step (float): The amount of units to step. Defaults to 0.0.
            compliance (float): The compliance value to set for the source. Defaults to self.compliance.

        Raises:
            AttributeError: If the SMU settings are not properly defined.
            KXCIConsoleError: If the instrument returns an error after sending the command.
        """
        num_step = int(abs(stop - start) / step) if step != 0 else 0
        self.setStepFunction2(start = start, step = step, num_steps = num_step, compliance = compliance)

    def setListSweep(self, values: list[float], compliance: float = 0.0, master: bool = False) -> None:
        """
        Sets the source function of the SMU to a list sweep function. The source can be either current
        or voltage depending on the sourceType attribute.

        Args:
            list (list[float]): The list of values to sweep through.
            compliance (float): The compliance value to set for the source. Defaults to self.compliance.

        Raises:
            AttributeError: If the SMU settings are not properly defined.
            KXCILimitationError: If the list is empty or too long.
            KXCIConsoleError: If the instrument returns an error after sending the command.
        """
        # Attribute checking
        if self.smu_type == SMUMode.VM or (self.smu_type == SMUMode.VS and self.source_type != SourceType.VOLT):
            raise AttributeError("SMU type and source unit are not compatible.")
        elif self.source_function != SourceFunction.SWEEP:
            raise AttributeError("Source function must be set to SWEEP to use this method.")
        elif self.source_type not in [SourceType.AMPERE, SourceType.VOLT]:
            raise AttributeError("Source type must be set to AMPERE or VOLT to use this method.")
        elif len(values) == 0 or len(values) > 4096:
            raise KXCILimitationError("Values list must contain between 1 and 4096 values.")

        # Save attributes
        self.compliance = compliance if compliance != 0.0 else self.compliance

        # Generate command
        prefix: str = "VL" if self.smu_type == SMUMode.VS else "IL"
        list_str: str = ", ".join([str(x) for x in values])
        command: str = prefix + str(self.slot) + ", " + str(int(master)) + ", " + str(self.compliance) + ", " + list_str

        self._write("SS")
        self._write(command)

        self._comm.checkForError()

    # === Private / Utils ===

    def _isDefinitionOk(self, type_of_smu: SMUMode) -> bool:
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
            self.voltage_measurement.name != "" and\
            (self.source_function != SourceFunction.NONE or type_of_smu == SMUMode.VM) and\
            (self.current_measurement.name != "" or type_of_smu != SMUMode.SMU) and\
            (self.source_type != SourceType.NONE or type_of_smu != SMUMode.SMU)

    # === Getters/Setters ===

    @property
    def smu_type(self) -> SMUMode:
        return self._smu_type
    
    @smu_type.setter
    def smu_type(self, value: SMUMode):
        if self._smu_type == value:
            return

        self._write("MP " + str(self.slot) + ", " + value.name + str(self.slot))
        self._comm.checkForError()
        self._smu_type = value

    @property
    def constant_value(self) -> float:
        return self._constant_value
    
    @constant_value.setter
    def constant_value(self, value: float):
        if self.source_function != SourceFunction.CONSTANT:
            raise AttributeError("Source function must be set to CONSTANT to use this attribute.")

        minmax: tuple[float, float] = (-210.0, 210.0) if self.source_type == SourceType.VOLT else (-0.105, 0.105) if not self.hp else (-1.05, 1.05)
        self._constant_value = min(max(value, minmax[0]), minmax[1])

    @property
    def compliance(self) -> float:
        return self._compliance

    @compliance.setter
    def compliance(self, value: float):
        minmax: tuple[float, float] = (-210.0, 210.0) if self.source_type == SourceType.AMPERE else (-0.105, 0.105) if not self.hp else (-1.05, 1.05)
        self._compliance = min(max(value, minmax[0]), minmax[1])

    @property
    def power_off_after_test(self) -> bool:
        return self._poweroff_after_test

    @power_off_after_test.setter
    def power_off_after_test(self, value: bool):
        self._write("SS")
        self._write("ST " + str(self.slot) + ", " + str(int(value)))
        self._comm.checkForError()
        self._poweroff_after_test = value

    @property
    def func_start(self) -> float:
        return self._func_start

    @func_start.setter
    def func_start(self, value: float):
        minmax: tuple[float, float] = (-210.0, 210.0) if self.source_type == SourceType.VOLT else (-1.05, 1.05) if self.hp else (-0.105, 0.105)
        self._func_start = min(max(value, minmax[0]), minmax[1])

    @property
    def func_stop(self) -> float:
        return self._func_stop
    
    @func_stop.setter
    def func_stop(self, value: float):
        minmax: tuple[float, float] = (-210.0, 210.0) if self.source_type == SourceType.VOLT else (-1.05, 1.05) if self.hp else (-0.105, 0.105)
        self._func_stop = min(max(value, minmax[0]), minmax[1])

    @property
    def num_steps(self) -> int:
        return self._num_steps
    
    @num_steps.setter
    def num_steps(self, value: int):
        self._num_steps = min(max(value, 0), 32)

    @property
    def delay_before_measure_during_sweep(self) -> float:
        return self._delay_before_measure_during_sweep

    @delay_before_measure_during_sweep.setter
    def delay_before_measure_during_sweep(self, value: float):
        self._delay_before_measure_during_sweep = min(max(value, 0.0), 6.553)
        self._write(f"DT {self._delay_before_measure_during_sweep}")
        self._comm.checkForError()

    @property
    def hold_before_sweep_during_step(self) -> float:
        return self._hold_before_sweep_during_step

    @hold_before_sweep_during_step.setter
    def hold_before_sweep_during_step(self, value: float):
        self._hold_before_sweep_during_step = min(max(value, 0.0), 655.3)
        self._write(f"HT {self._hold_before_sweep_during_step}")
        self._comm.checkForError()

    @property
    def wait_time_after_constant_before_stepping(self) -> float:
        return self._wait_time_after_constant_before_stepping

    @wait_time_after_constant_before_stepping.setter
    def wait_time_after_constant_before_stepping(self, value: float):
        self._wait_time_after_constant_before_stepping = min(max(value, 0.0), 100.0)
        self._write(f"WT {self._wait_time_after_constant_before_stepping}")
        self._comm.checkForError()
