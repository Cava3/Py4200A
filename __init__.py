"""
pyKI4200A - Python interface for Keithley 4200A Semiconductor Characterization System
Author: Lucas LE DUDAL

This library provides a high-level interface to control and communicate with the Keithley 4200A system,
allowing users to perform measurements, set up test configurations, and retrieve data in a user-friendly manner.
"""

from .src.KI4200A import KI4200A    # type: ignore
from .src import consts             # type: ignore
from .src import boards             # type: ignore