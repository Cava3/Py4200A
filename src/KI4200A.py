"""
KI4200A.py - Python interface for Keithley 4200A Semiconductor Characterization System
Author: Lucas LE DUDAL

This module defines the KI4200A class, which provides methods to control the Keithley 4200A.
The class uses the Communications class from the instrcomms module to handle low-level communication, \
and provides user with high-level OOP to interact with the instrument in a more intuitive way.
"""

from .instrcomms import Communications
from .boards.Board import Board
from .boards import *
from .consts import Status, BoardType
from pyvisa.resources.gpib import GPIBInstrument

class KI4200A:
    """
    This class represents the Keithley 4200A Semiconductor Characterization System.

    Attributes:
        id (dict[str, str]): identifying informations of the instrument (result of the `*IDN?` query)
        l_equipment (list[Board]): List of equipped modules in the instrument.
        read_termination (str): The termination character(s) used when reading responses from the instrument
        status (Status): Current status of the instrument (e.g., "Initializing", "Connected", "Configuring").
        write_termination (str): The termination character(s) used when writing commands to the instrument.
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
        
        #Private
        self._comms: Communications
        self._l_equipped: list[str]
        

        # Initialization process
        self.status = Status.INITIALIZING
        self._comms = Communications(instrument_resource_string)
        self._instrument_resource_string = instrument_resource_string

        self.status = Status.CONNECTING
        self._comms.connect()

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

        # FIXME: There is a bug from KXCI where it doesn't return my RPM1-1 even though it returns \
        # FIXME: the second one. The first one is also displayed on KCon, so definitely a KXCI issue.
        # FIXME: Can be removed if fixed in more recent versions of KXCI
        if "PMU1RPM1-2" in self._l_equipped and "PMU1RPM1-1" not in self._l_equipped:
            self._l_equipped.insert(self._l_equipped.index("PMU1RPM1-2"), "PMU1RPM1-1")

        # List and convert the boards
        l_boards: list[Board] = [Board(name=board_name, comm=self._comms) for board_name in self._l_equipped]
        self.l_equipment = [self._type_board(board) for board in l_boards]


    def reset(self) -> None:
        """
        Reset the instrument to its default state.
        """
        self.write("BC") # Clear buffer
        self.write(":ERROR:LAST:CLEAR") # Clear last error
        self.write("*RST") # Reset instruments
        self.status = Status.READY

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

    def waitForDataReady(self, timout: int = 25_000) -> None:
        """
        Wait until the instrument has completed its current operation and is ready for the next command.
        This can be used after issuing a command that takes time to execute, to ensure that the instrument is\
        ready before sending the next command.
        """
        if isinstance(self._comms.instrument_object, GPIBInstrument):
            # For GPIB, use the event manager
            self._comms.instrument_object.wait_for_srq(timeout=timout)
        else:
            # For TCPIP, repeated requests until
            while int(self.query("SP")) not in [0, 1]:
                pass

    # === Private ===

    def _type_board(self, b: Board) -> Board :
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


        return b

    def __del__(self) -> None:
        """
        Destructor to ensure proper disconnection from the instrument when the KI4200A object is deleted.
        """
        self.disconnect()


    # === Getters and setters ===

    @property
    def write_termination(self) -> str:
        return self._comms.write_termination
    
    @write_termination.setter
    def write_termination(self, value: str) -> None:
        self._comms.write_termination = value

    @property
    def read_termination(self) -> str:
        return self._comms.read_termination
    
    @read_termination.setter
    def read_termination(self, value: str) -> None:
        self._comms.read_termination = value
