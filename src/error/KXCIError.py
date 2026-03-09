"""
KXCIError.py - Custom exception class for Keithley External Control Interface (KXCI) errors.
Author: Lucas LE DUDAL
"""

class KXCIError(Exception):
    """
    Exception raised for errors rreturned by KXCI commands.

    Attributes:
        message (str): Explanation of the error.
        error_code (str, optional): The specific error code returned by the instrument. NI
    """

    def __init__(self, message: str, error_code: str = "") -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.error_code != "":
            return f"[KXCI Error {self.error_code}]: {self.message}"
        return f"[KXCI Error]: {self.message}"
