"""
    Copyright 2023 Tektronix, Inc.
    See www.tek.com/sample-license for licensing terms.
"""

import pyvisa as visa
from .error import KXCIConsoleError

class Communications:
    """
    This class offers the consumer a collection of wrapper menthods that leverage PyVisa calls and attempts
    to condense collections of methods therein while also adding in a means for echoing command calls
    to the terminal if the appropriate internal attribute is set to True.

    Note that this is a work in progress and by no means a work of perfection. Please feel free to copy,
    reuse, or enhance to your own liking and feel free to leave suggestions for improvement. Thanks!
    """

    def __init__(self, instrument_resource_string: str) -> None:
        """
        Initialize the Communications class.

        Args:
            instrument_resource_string (str): The VISA resource string for the instrument.
        """
        self._instrument_resource_string: str = instrument_resource_string
        self._resource_manager: visa.ResourceManager | None = None
        self.instrument_object: visa.resources.MessageBasedResource
        self._timeout: int = 5_000
        self._echo_cmds: bool = False
        self._version: float = 1.1
        self.con_type: int = -1 # connection type. -1 = not connected, 0 = TCPIP, 1 = GPIB

        self._backend: str = ""
        try:
            self._resource_manager = visa.ResourceManager()  # system VISA (NI-VISA, Keysight, …)
            self._backend = "default"
        except Exception:
            try:
                self._resource_manager = visa.ResourceManager("@py")  # pure-Python fallback
                self._backend = "@py"
            except Exception as e:
                raise RuntimeError(
                    "No VISA backend found. Install NI-VISA (Windows/Mac) "
                    "or pyvisa-py: pip install py4200A[visa-py]"
                ) from e

    def connect(self, instrument_resource_string: str | None = None, timeout: int | None = None) -> None:
        """
        Open an instance of an instrument object for remote communication.

        Args:
            instrument_resource_string (str | None): The VISA resource string. If None, uses the one from init.
            timeout (int | None): Time in milliseconds to wait before timeouts.
        """
        try:
            if self._resource_manager is None:
                raise RuntimeError(
                    "No ResourceManager available. Backend may have failed to load."
                )

            if instrument_resource_string is not None:
                self._instrument_resource_string = instrument_resource_string


            t_resource: visa.resources.Resource = self._resource_manager.open_resource(
                self._instrument_resource_string
            )

            if isinstance(t_resource, visa.resources.MessageBasedResource):
                self.instrument_object = t_resource # type: ignore
                self.con_type = int(isinstance(t_resource, visa.resources.GPIBInstrument))
            else :
                raise Exception("Resource is not message-based")

            if timeout is None:
                self.instrument_object.timeout = self._timeout
            else:
                self.instrument_object.timeout = timeout
                self._timeout = timeout

            # Check for the SOCKET as part of the instrument ID string and set
            # the following accordingly...
            if "SOCKET" in self._instrument_resource_string:
                self.instrument_object.write_termination = "\n"
                self.instrument_object.read_termination = "\n"
                self.instrument_object.send_end = True

        except visa.VisaIOError as visaerr:
            # Provide an actionable error with environment details
            hint = (
                "Possible causes: vendor VISA (NI‑VISA) not installed, or the vendor's GPIB driver/plugin "
                "is missing.\nInstall NI‑VISA or use a TCPIP resource. For pyvisa-py + linux-gpib, install linux-gpib."
            )
            msg = (
                f"VisaIOError opening '{self._instrument_resource_string}': {visaerr}\n"
                f"Backend={getattr(self, '_backend', None)}\n"
                f"{hint}"
            )
            raise RuntimeError(msg) from visaerr
        return

    def disconnect(self) -> None:
        """
        Close an instance of an instrument object.
        """
        if not hasattr(self, "instrument_object"):
            return
        try:
            self.instrument_object.close()
            self.con_type = -1
        except visa.VisaIOError as visaerr:
            print(f"{visaerr}")
        return

    def write(self, command: str) -> None:
        """
        Issue controlling commands to the target instrument.

        Args:
            command (str): The command issued to the instrument to make it perform some action or service.
        """
        try:
            if self._echo_cmds is True:
                print(command)
            self.instrument_object.write(command)
        except visa.VisaIOError as visaerr:
            print(f"{visaerr}")
        return

    def read(self) -> str:
        """
        Used to read results from the instrument.

        Returns:
            (str): The requested information returned from the target instrument.
        """
        return self.instrument_object.read()

    def query(self, command: str) -> str:
        """
        Used to send commands to the instrument  and obtain an information string from the instrument.
        Note that the information received will depend on the command sent and will be in string format.

        Args:
            command (str): The command issued to the instrument to make it perform some action or service.

        Returns:
            (str): The requested information returned from the target instrument.
        """
        response = ""
        try:
            if self._echo_cmds is True:
                print(command)
            response = self.instrument_object.query(command).rstrip()
        except visa.VisaIOError as visaerr:
            print(visaerr)

        return response

    def hasError(self) -> bool:
        """
        Used to query the instrument for any errors that may have occurred during the last command or query.

        Returns:
            (bool): True if an error is present, False if no error is present.
        """
        return self.query(":ERROR:LAST:GET") not in ("", "\n")

    def getError(self) -> str:
        """
        Used to query the instrument for any errors that may have occurred during the last command or query.

        Returns:
            (str): The error message returned from the instrument, or an empty string if no error is present.
        """
        return self.query(":ERROR:LAST:GET")

    def clearError(self) -> None:
        """
        Used to clear any errors that may have occurred during the last command or query.
        """
        self.write(":ERROR:LAST:CLEAR")

    def checkForError(self) -> None:
        """
        Used to check for any errors that may have occurred during the last command or query and raise an exception if an error is present.
        """
        if self.hasError():
            error_message = self.getError()
            self.clearError()
            raise KXCIConsoleError(message=error_message)

    # === Getters and setters ===

    @property
    def write_termination(self) -> str:
        return self.instrument_object.write_termination
    
    @write_termination.setter
    def write_termination(self, value: str) -> None:
        self.instrument_object.write_termination = value

    @property
    def read_termination(self) -> str:
        return str(self.instrument_object.read_termination)
    
    @read_termination.setter
    def read_termination(self, value: str) -> None:
        self.instrument_object.read_termination = value

    @property
    def timeout(self) -> int:
        return self._timeout
