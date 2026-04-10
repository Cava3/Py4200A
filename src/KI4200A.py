"""
KI4200A.py - Python interface for Keithley 4200A Semiconductor Characterization System
Author: Lucas LE DUDAL

This module defines the KI4200A class, which provides methods to control the Keithley 4200A.
The class uses the Communications class from the instrcomms module to handle low-level communication, \
and provides user with high-level OOP to interact with the instrument in a more intuitive way.
"""
from .results import Display, Measurement
from .results.BlobDependent import BlobDependent
from .instrcomms import Communications
from .boards.Board import Board
from .boards import *
from .consts import Status, BoardType, RPMMode, IntegrationTime, PMUMeasureMode
from pyvisa.resources.gpib import GPIBInstrument
import time as t
import numpy as np

class KI4200A:
    """
    This class represents the Keithley 4200A Semiconductor Characterization System.
    """

    def __init__(self, instrument_resource_string: str) -> None:
        """
        Initialize a KI4200A instance and establish communication with the instrument.
        The initialization process includes setting up communication parameters, scanning for equipped\
        modules, and preparing the instrument for use.

        Args:
            instrument_resource_string (str): The VISA resource string that identifies the instrument\
                (e.g., "GPIB0::24::INSTR" or "TCPIP0::<IP_ADDRESS>::INSTR").
        """
        # Attributes declaration
        #Public
        self.id: dict[str, str]
        self.status: Status             # KI4200A's current task or state
        self.l_equipment: list[Board]   # List of board objects equipped in the instrument
        self.l_smus: list[SMU]          # List of SMU boards equipped in the instrument in slot order
        self.display: Display           # Display controller for managing the instrument's display
        self.all_measurements: list[Measurement] # List of all measurements configured on the instrument
        
        #Private
        self._comms: Communications
        self._l_equipped: list[str]
        self._exit_on_compliance: bool = False
        self._integration_time: IntegrationTime = IntegrationTime.NORMAL
        self._test_mode: RPMMode = RPMMode.PMU
        self._pmu_measure_mode: PMUMeasureMode = PMUMeasureMode.SPOT_MEAN_DISCRETE
        self._pmu_burst_count: int = 1
        self._pmu_sample_rate: int = 200_000_000
        

        # Initialization process
        self.status = Status.INITIALIZING
        self._comms = Communications(instrument_resource_string)
        self._instrument_resource_string = instrument_resource_string

        self.status = Status.CONNECTING
        self._comms.connect()
        self.display = Display(self._comms)

        self.status = Status.CONFIGURING
        self.write_termination = "\0"
        self.read_termination = "\n"

        self.status = Status.SCANNING
        self.l_equipment=[]
        self.id = {
            "Brand": "",
            "Model": "",
            "Serial Number": "",
            "Software Version": ""    
        }
        self.scan()
        self.all_measurements = [measurement for board in self.l_equipment for measurement in board.measurements]
        self.l_smus = [board for board in self.l_equipment if board.board_type == BoardType.SMU and isinstance(board, SMU)]
        self.l_smus.sort(key=lambda smu: smu.slot)

        self.status = Status.READY_NOT_RESET

    def scan(self) -> None:
        """
        Scan the instrument for :
         - Identity of the instrument to populate the id attribute with Brand, Model, SN and SW version
         - Equipped modules and populate the l_equipment attribute with Board objects.
        """
        # Get the IDN
        idn: list[str] = self.query("*IDN?").split(",")
        self.id["Brand"], self.id["Model"], self.id["Serial Number"], self.id["Software Version"] = idn[:4]

        self._l_equipped = self.query("*OPT?").split(",")
        self._comms.checkForError()

        # FIXME: There is a bug from KXCI where it doesn't return my RPM1-1 even though it returns
        # FIXME: the second one. The first one is also displayed on KCon, so definitely a KXCI issue.
        # FIXME: Can be removed if fixed in more recent versions of KXCI
        # FIXME: Update : RPM is configurable with commands, so it proves thats just a KXCI response problem.
        if "PMU1RPM1-2" in self._l_equipped and "PMU1RPM1-1" not in self._l_equipped:
            self._l_equipped.insert(self._l_equipped.index("PMU1RPM1-2"), "PMU1RPM1-1")

        # List and convert the boards
        l_boards: list[Board] = [Board(name=board_name, comm=self._comms) for board_name in self._l_equipped]
        self.l_equipment = [self._typeBoard(board) for board in l_boards]
        

    def reset(self) -> None:
        """
        Reset the instrument to its default state.
        """
        self.write("BC") # Clear buffer
        self.write(":ERROR:LAST:CLEAR") # Clear last error
        self.write("*RST") # Reset instruments

        for smu in self.l_smus:
            smu.deactivate()

        # Reset RPMs
        self.test_mode = RPMMode.PMU


        self._comms.checkForError()

        self.status = Status.READY

    def getSMU(self, slot: int) -> SMU:
        """
        Get the RT_SMU instance for the given slot number.

        Args:
            slot: SMU slot number (1-8).

        Returns:
            RT_SMU: Real-time SMU controller for that channel.

        Raises:
            ValueError: If no SMU with that slot was found during scan.
        """
        for smu in self.l_smus:
            if smu.slot == slot:
                return smu
        raise ValueError(f"No SMU found at slot {slot}.")


    def getError(self) -> str:
        """
        Query the instrument for any error messages and return the response.

        Returns:
            str: The error message from the instrument, or "No error" if there are no errors.
        """
        error = self.query(":ERROR:LAST:GET")
        return error

    def write(self, command: str) -> None:
        """
        Send a command to the instrument but doesn't read an answer.  
        Only for GPIB, as TCPIP always return a value, or "ACK".  
        For TCPIP, redirects to `query`
        """
        if self._comms.con_type == 1:
            self._comms.write(command)
        else :
            self.query(command)


    def query(self, command: str) -> str:
        """
        Send a command to the instrument and return the response.

        Args:
            command (str): The command to send to the instrument.
        Returns:
            str: The response from the instrument.
        """
        return self._comms.query(command)


    def disconnect(self) -> None:
        """
        Disconnect from the instrument and release any resources.
        """
        self._comms.disconnect()
        self.status = Status.DISCONNECTED

    def reconnect(self) -> None:
        """
        Reconnects to the instrument when disconnected.
        """
        self.__init__(self._instrument_resource_string)

    def runTest(self, clear_buffer: bool = True) -> None:
        """
        Starts the test sequence on the instrument.

        In SMU mode, triggers the SMU test via ME.
        In PMU mode, executes the PMU pulse test via :PMU:EXECUTE.

        Args:
            clear_buffer (bool): Whether to clear the result buffer before running. Defaults to True.
                                 Only applies to SMU mode.
        """
        if self.test_mode == RPMMode.SMU:
            self.write("MD")
            self.write("ME1" if clear_buffer else "ME3")
        elif self.test_mode == RPMMode.PMU:
            self.write(":PMU:EXECUTE")

    def abortTest(self) -> None:
        """
        Aborts the test sequence on the instrument.
        """
        if self.test_mode == RPMMode.SMU:
            self.write("MD")
            self.write("ME4")
        else:
            self.write(":PMU:ABORT")

    def initPMU(self) -> None:
        """
        Initialize the PMU in standard pulse mode.

        Sends ``:PMU:INIT 0``, which resets both channels of the pulse card to
        their default settings for standard pulse mode, clears the data buffer,
        and deletes all Segment Arb sequences.

        This must be called before any other PMU configuration command.  To
        reset *all* cards in the system at once, use :meth:`reset` instead
        (which sends ``*RST``).
        """
        self.write(":PMU:INIT 0")
        self._comms.checkForError()

    def waitForDataReady(self) -> None:
        """
        Wait until the instrument has completed its current operation and is ready for the next command.
        This can be used after issuing a command that takes time to execute, to ensure that the instrument is\
        ready before sending the next command.
        """
        if isinstance(self._comms.instrument_object, GPIBInstrument):
            if self._comms.backend == "@py":
                # FIXME: PyVisa-py doesn't implement wait_for_srq.
                # Workaround: poll a command unavailable during execution.
                t_start = 0
                while t.time() >= t_start + self._comms.timeout/1000:
                    t_start = t.time()
                    self.query("*OPT?")
                self.write(":ERROR:LAST:CLEAR")
            else:
                self._comms.instrument_object.wait_for_srq()

        else:
            # For TCPIP, repeated requests until
            while True:
                response: str = self.query("SP")
                if response.isnumeric() and int(response) in [0, 1]:
                    break

    def makeDependentFrom(self, data: Measurement, params: list[Measurement]) -> BlobDependent:
        """
        Build a :class:`BlobDependent` from a data measurement and a list of parameter measurements.

        Each parameter measurement contributes one axis to the result.  Its ``steps`` attribute defines
        the length of that axis and its :meth:`~Measurement.getResultSerie` values become the coordinate array.  
        The data measurement is fetched as a flat series and reshaped into the N-D array whose shape is
        ``(params[0].steps, params[1].steps, …)`` after sorting the Measurements by order.

        Args:
            data (Measurement): The measurement that contains the raw result data.
            params (list[Measurement]): Parameter measurements in any order. Will be sorted to correctly shape results.

        Returns:
            BlobDependent: The structured N-dimensional result, labelled with
            the data measurement name.

        Raises:
            ValueError: If ``data.steps`` does not equal the product of all
                parameter ``steps``.

        Example:
            >>> dep = ki.makeDependentFrom(id_measurement, [vg_measurement, vd_measurement])
        """
        invalid: list[str] = [
            p.name for p in params if p.order < 0 or p.steps <= 0
        ]
        if invalid:
            raise ValueError(
                f"The following measurements are not configured as valid "
                f"sweep parameters (order < 0 or steps <= 0): {invalid}."
            )

        # Highest stepper_index first (outermost loop → axis 0),
        # sweep (order=0) last (innermost loop → last axis).
        sorted_params: list[Measurement] = sorted(params, key=lambda p: p.order, reverse=True)

        shape: tuple[int, ...] = tuple(p.steps for p in sorted_params)
        amount_of_data: int = 1
        for s in shape:
            amount_of_data *= s

        raw_data: list[float] = data.getAllResults()

        if len(raw_data) != amount_of_data:
            raise ValueError(
                f"data length ({len(raw_data)}) must equal the product of all parameter steps ({amount_of_data})."
            )

        parameters: dict[str, np.ndarray] = {
            p.name: np.array(p.getResultSerie(sorted_params[i + 1:] or None))
            for i, p in enumerate(sorted_params)
        }

        return BlobDependent(
            data=np.array(raw_data).reshape(shape),
            parameters=parameters,
            label=data.name,
        )


    # === Private ===

    def _typeBoard(self, b: Board) -> Board :
        """
        A function to auto-type a board. Called upon board detection

        Args:
            b (Board): the Board to be converted
        
        Returns:
            Board: A board converted (if possible) to corresponding subclass
        """

        if b.board_type == BoardType.SMU :
            return SMU.of(b)
        elif b.board_type == BoardType.CVU :
            return CVU.of(b)
        elif b.board_type == BoardType.PMU_RPM :
            return PMU_RPM.of(b)

        return b

    def __del__(self) -> None:
        """
        Destructor to ensure proper disconnection from the instrument when the KI4200A object is deleted.
        """
        self.disconnect()


    # === Getters and setters ===

    @property
    def comms(self) -> Communications:
        """The underlying Communications object for this instrument."""
        return self._comms

    @property
    def write_termination(self) -> str:
        """The termination character(s) appended to every command written to the instrument."""
        return self._comms.write_termination

    @write_termination.setter
    def write_termination(self, value: str) -> None:
        self._comms.write_termination = value

    @property
    def read_termination(self) -> str:
        """The termination character(s) expected at the end of every response from the instrument."""
        return self._comms.read_termination

    @read_termination.setter
    def read_termination(self, value: str) -> None:
        self._comms.read_termination = value

    @property
    def exit_on_compliance(self) -> bool:
        """If ``True``, the sweep stops as soon as a compliance limit is hit."""
        return self._exit_on_compliance

    @exit_on_compliance.setter
    def exit_on_compliance(self, value: bool):
        self._exit_on_compliance = value
        self.write("US")
        self.write(f"EC {int(value)}")
        self._comms.checkForError()

    @property
    def integration_time(self) -> IntegrationTime:
        """Integration time used for each measurement point."""
        return self._integration_time

    @integration_time.setter
    def integration_time(self, value: IntegrationTime):
        self._integration_time = value
        self.write("US")
        self.write(f"IT {value.value}")
        self._comms.checkForError()

    @property
    def test_mode(self) -> RPMMode:
        """The current RPM mode used when running a test. Defaults to SMU."""
        return self._test_mode

    @test_mode.setter
    def test_mode(self, value: RPMMode) -> None:
        self._test_mode = value
        rpms: list[PMU_RPM] = [rpm for rpm in self.l_equipment if isinstance(rpm, PMU_RPM)]
        for rpm in rpms:
            self.write(f":PMU:RPM:CONFIGURE PMU{rpm.name[-3]}-{rpm.name[-1]}, {value.value}")
        self._comms.checkForError()

    @property
    def pmu_measure_mode(self) -> PMUMeasureMode:
        """Measurement mode for all PMU channels, sent via ``:PMU:MEASURE:MODE``.

        Selects what data the PMU captures and returns:

        * ``NONE`` (0) — no measurements.
        * ``SPOT_MEAN_DISCRETE`` (1) — averaged V/I per pulse (default).
        * ``WAVEFORM_DISCRETE`` (2) — full time-sampled waveform per pulse.
        * ``SPOT_MEAN_AVERAGE`` (3) — spot mean averaged across all burst pulses.
        * ``WAVEFORM_AVERAGE`` (4) — waveform averaged across all burst pulses.

        Setting this property immediately sends the command to the instrument.
        """
        return self._pmu_measure_mode

    @pmu_measure_mode.setter
    def pmu_measure_mode(self, value: PMUMeasureMode) -> None:
        self._pmu_measure_mode = value
        self.write(f":PMU:MEASURE:MODE {value.value}")
        self._comms.checkForError()

    @property
    def pulse_burst_count(self) -> int:
        """Total number of pulses output per test across all active PMU channels.

        Used in average and discrete measurement modes:

        * ``SPOT_MEAN_DISCRETE`` — generates *burstCount* data points per channel.
        * ``WAVEFORM_DISCRETE`` — generates *burstCount × waveform_points* data points.
        * ``SPOT_MEAN_AVERAGE`` — always generates 1 averaged data point.
        * ``WAVEFORM_AVERAGE`` — generates *waveform_points* averaged data points.

        Valid range: 1 to 10 000. Default after ``:PMU:INIT``: 1.
        Sends ``:PMU:PULSE:BURST:COUNT <n>`` to the instrument.
        """
        return self._pmu_burst_count

    @pulse_burst_count.setter
    def pulse_burst_count(self, value: int) -> None:
        if not (1 <= value <= 10_000):
            raise ValueError(f"Burst count must be between 1 and 10 000; got {value}.")
        self._pmu_burst_count = value
        self.write(f":PMU:PULSE:BURST:COUNT {value}")
        self._comms.checkForError()

    @property
    def pmu_sample_rate(self) -> int:
        """PMU waveform capture sample rate in samples per second.

        Valid range: 1 000 to 200 000 000 Sa/s (1 kSa/s to 200 MSa/s).
        The value is sent as an integer.
        Default after ``:PMU:INIT``: 200 MSa/s.

        The instrument may silently adjust the rate if it would produce more than
        65\ 536 data points, or if it is slower than required by the shortest
        measurement interval.
        Sends ``:PMU:SAMPLE:RATE <rate>`` to the instrument.
        """
        return self._pmu_sample_rate

    @pmu_sample_rate.setter
    def pmu_sample_rate(self, value: int) -> None:
        if not (1_000 <= value <= 200_000_000):
            raise ValueError(
                f"Sample rate must be between 1 000 and 200 000 000 Sa/s; got {value}."
            )
        self._pmu_sample_rate = value
        self.write(f":PMU:SAMPLE:RATE {value}")
        self._comms.checkForError()
