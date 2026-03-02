"""
    Copyright 2023 Tektronix, Inc.
    See www.tek.com/sample-license for licensing terms.
"""

import pyvisa as visa


class Communications:
    """
    This class offers the consumer a collection of wrapper menthods that
    leverage PyVisa calls and attempts to condense collections of methods
    therein while also adding in a means for echoing command calls to the
    terminal if the appropriate internal attribute is set to True.

    Note that this is a work in progress and by no means a work of
    perfection. Please feel free to copy, reuse, or enhance to your own
    liking and feel free to leave suggestions for improvement. Thanks!
    """

    def __init__(self, instrument_resource_string: str):
        self._instrument_resource_string: str = instrument_resource_string
        self._resource_manager: visa.ResourceManager | None = None
        self._instrument_object: visa.resources.MessageBasedResource
        self._timeout: int = 5_000
        self._echo_cmds: bool = False
        self._version: float = 1.1
        self.con_type: int = -1 # connection type. -1 = not connected, 0 = TCPIP, 1 = GPIB

        try:
            if self._resource_manager is None:
                # Try the system (IVI) backend first
                self._resource_manager = visa.ResourceManager("@py")
        except visa.VisaIOWarning as visawarning:
            print(f"{visawarning}")

    def connect(self, instrument_resource_string: str | None = None, timeout: int | None = None):
        """
        Open an instance of an instrument object for remote communication.

        Args:
            timeout (int): Time in milliseconds to wait before the \
                communication transaction with the target instrument\
                    is considered failed (timed out).

        Returns:
            None
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

            if issubclass(type(t_resource), visa.resources.MessageBasedResource):
                self._instrument_object = t_resource # type: ignore
                self.con_type = int(issubclass(type(t_resource), visa.resources.GPIBInstrument))
            else :
                raise Exception("Resource is not message-based")

            if timeout is None:
                self._instrument_object.timeout = self._timeout
            else:
                self._instrument_object.timeout = timeout
                self._timeout = timeout

            # Check for the SOCKET as part of the instrument ID string and set
            # the following accordingly...
            if "SOCKET" in self._instrument_resource_string:
                self._instrument_object.write_termination = "\n"
                self._instrument_object.read_termination = "\n"
                self._instrument_object.send_end = True

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

    def disconnect(self):
        """
        Close an instance of an instrument object.

        Args:
            None

        Returns:
            None
        """
        try:
            self._instrument_object.close()
            self.con_type = -1
        except visa.VisaIOError as visaerr:
            print(f"{visaerr}")
        return

    def write(self, command: str):
        """
        Issue controlling commands to the target instrument.

        Args:
            command (str): The command issued to the instrument to make it\
                perform some action or service.

        Returns:
            None
        """
        try:
            if self._echo_cmds is True:
                print(command)
            self._instrument_object.write(command)
        except visa.VisaIOError as visaerr:
            print(f"{visaerr}")
        return

    def read(self) -> str:
        """
        Used to read commands from the instrument.

        Args:
            None

        Returns:
            (str): The requested information returned from the target
            instrument.
        """
        return self._instrument_object.read()

    def query(self, command: str) -> str:
        """
        Used to send commands to the instrument  and obtain an information
        string from the instrument. Note that the information received will
        depend on the command sent and will be in string format.

        Args:
            command (str): The command issued to the instrument to make it
            perform some action or service.

        Returns:
            (str): The requested information returned from the target
            instrument.
        """
        response = ""
        try:
            if self._echo_cmds is True:
                print(command)
            response = self._instrument_object.query(command).rstrip()
        except visa.VisaIOError as visaerr:
            print(visaerr)

        return response

    # === Getters and setters ===

    @property
    def write_termination(self) -> str:
        return self._instrument_object.write_termination
    
    @write_termination.setter
    def write_termination(self, value: str) -> None:
        self._instrument_object.write_termination = value

    @property
    def read_termination(self) -> str:
        return str(self._instrument_object.read_termination)
    
    @read_termination.setter
    def read_termination(self, value: str) -> None:
        self._instrument_object.read_termination = value