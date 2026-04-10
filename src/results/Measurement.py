"""
Measurement.py - Python module defining the Measurement class to represent a specific measurement in the Keithley 4200A.
Author: Lucas LE DUDAL
"""
from ..consts import GraphPosition, MeasurementType, PMURequestedValue, SourceType
from ..error import KXCILimitationError
from ..instrcomms import Communications


class Measurement:
    """
    This class represents a measurement configuration and its associated data.
    """

    def __init__(self, comm: Communications, name: str, measurement_type: MeasurementType = MeasurementType.SMU, steps: int = -1, min_value: float = 0.0, max_value: float = 0.0, is_log_scale: bool = False, unit: SourceType = SourceType.NONE) -> None:
        """
        Initialize a Measurement instance.

        Args:
            comm (Communications): The communication object used to query results.
            name (str): The name of the measurement.
            measurement_type (MeasurementType): Whether this measurement belongs to an SMU
                (data read via ``RD``) or a PMU_RPM channel (data read via
                ``:PMU:DATA:COUNT?`` / ``:PMU:DATA:GET``). Defaults to
                ``MeasurementType.SMU`` for backward compatibility.
            steps (int): The number of measurement steps.
            min_value (float): The minimum value.
            max_value (float): The maximum value.
            is_log_scale (bool): True for logarithmic scale, False for linear.
            unit (SourceType): The unit of the measurement.
        """
        self._name: str = ""
        self._channel: int = 0
        self._min_value: float = 0
        self._max_value: float = 0
        self._com: Communications = comm
        self.unit: SourceType = unit
        self.steps: int = steps
        self.order: int = -1
        self.measurement_type: MeasurementType = measurement_type
        self.name = name
        self.min_value = min_value
        self.max_value = max_value
        self.is_log_scale = is_log_scale

    def getResultAt(self, index: int) -> str:
        """
        Fetch the SMU measurement result at a specific index.

        This method only applies to ``MeasurementType.SMU`` measurements.  For
        PMU_RPM channels, use :meth:`getPointCount` and :meth:`getData` instead.

        Args:
            index (int): The index at which to fetch the measurement result.

        Returns:
            str: The raw measurement result at the specified index.
        """
        str_result: str = self._com.query(f"RD '{self.name}', {index}")
        self._com.checkForError()

        return str_result

    def getPointCount(self) -> int:
        """
        Return the number of data points currently stored in the PMU data buffer
        for this channel.

        Sends the ``:PMU:DATA:COUNT? <ch>`` command, where *ch* is the channel
        number derived from the last character of the measurement name
        (e.g. the name ``"pmu1-rpm1-2"`` yields channel ``2``).

        This method is only meaningful for ``MeasurementType.PMU_RPM``
        measurements.  It may be called while a test is in progress or after
        completion.

        Returns:
            int: Number of readings stored in the buffer for this channel.
        """
        response: str = self._com.query(f":PMU:DATA:COUNT? {self._channel}")
        self._com.checkForError()
        return int(response)

    def getData(
        self,
        start_index: int | None = None,
        num_points: int | None = None,
        requested_values: list[PMURequestedValue] | None = None,
    ) -> list[list[str]]:
        """
        Retrieve measurement data from the PMU data buffer for this channel.

        Sends the ``:PMU:DATA:GET`` command and returns the parsed result.
        The PMU buffer holds up to 65 536 points per channel; the instrument
        returns at most 2 048 points per call.  For larger datasets, call this
        method repeatedly with an increasing *start_index* and concatenate the
        results.

        Args:
            start_index (int | None): Zero-based index of the first point to
                retrieve.  When omitted, the instrument starts at index 0.
            num_points (int | None): Number of points to return (1 – 2048).
                When omitted (together with *start_index* already specified),
                all available points from *start_index* to the end of the buffer
                are returned (up to 2048).  When *start_index* is also omitted,
                all available points are returned.
            requested_values (list[PMURequestedValue] | None): Ordered list of
                value tokens to include in each data point.  Tokens are defined
                by :class:`~py4200A.consts.PMURequestedValue`.

                *Waveform-capture mode*: ``V``, ``I``, ``T``, ``S``.

                *Spot-mean / Pulse I-V mode*: ``VH``, ``IH``, ``TH``, ``SH``,
                ``VL``, ``IL``, ``TL``, ``SL``.

                When ``None``, the instrument returns all available values for
                the active measurement mode.

        Returns:
            list[list[str]]: A list of data points.  Each data point is itself
            a list of string tokens in the order defined by *requested_values*
            (or by the instrument's default order when *requested_values* is
            ``None``).  Data points are separated by semicolons in the raw
            response; tokens within a data point are comma-separated.

        Example::

            # Channel 1, first 2048 points, voltage + status only
            data = meas.getData(
                start_index=0,
                num_points=2048,
                requested_values=[PMURequestedValue.V, PMURequestedValue.S],
            )
            voltages = [float(point[0]) for point in data]
        """
        command: str = f":PMU:DATA:GET {self._channel}"

        if start_index is not None:
            command += f", {start_index}"
            if num_points is not None:
                command += f", {num_points}"
                if requested_values is not None:
                    tokens = ", ".join(rv.value for rv in requested_values)
                    command += f", {tokens}"

        raw: str = self._com.query(command)
        self._com.checkForError()

        if not raw:
            return []

        points: list[list[str]] = [
            point.split(",") for point in raw.split(";")
        ]
        return points

    def isResultValid(self, value: str) -> bool:
        """
        Check if a value is a valid measurement.

        Args:
            value (str) : The value for which to check validity

        Returns:
            bool: True if the measurement value is valid, False otherwise.
        """
        try:
            float(value)
        except ValueError:
            return False

        return float(value) != 0


    def getResultSerie(self, precedent_dimensions: list["Measurement"] | None = None) -> list[float]:
        """
        Fetch one value per step of this measurement, skipping over repeated inner-loop values.

        In the KXCI buffer, an outer (step) source repeats each of its values once for every
        point of its inner dimensions. ``precedent_dimensions`` describes those inner measurements
        so the correct stride can be computed.

        Examples:
            - Sweep (innermost, no inner dims): ``getResultSerie()`` → first ``steps`` values.
            - Step with one inner sweep of 20 pts: ``getResultSerie([20])`` → values at buffer indices 1, 152, 303, …

        Args:
            precedent_dimensions: Measurements whose loops are nested *inside* this one.
                                  Their ``steps`` are multiplied together to form the stride.
                                  Defaults to ``None`` (stride = 1).

        Returns:
            list[float]: ``steps`` values, one per unique output level of this measurement.
        """
        stride: int = 1
        if precedent_dimensions:
            for m in precedent_dimensions:
                stride *= m.steps

        results: list[float] = []
        for i in range(self.steps):
            results.append(float(self.getResultAt(1 + stride * i)))

        return results


    def getAllResults(self) -> list[float]:
        """
        Fetch the measurement results from the instrument.

        Returns:
            list[float]: The list of measurement values retrieved from the instrument.
        """
        l_readings: list[float] = []
        index: int = 1
        value: str = self.getResultAt(index)
        index+=1
        while self.isResultValid(value):
            l_readings.append(float(value))
            value = self.getResultAt(index)
            index += 1

        return l_readings

    def getGraphCommand(self, axis: GraphPosition) -> str:
        """
        Get the graph command for displaying the measurement on the specified graph axis.

        Args:
            axis (GraphPosition): The axis on which to display the measurement.

        Returns:
            str: The command string to configure the graph display for this measurement.
        """
        command = f"{axis.value} '{self.name}', {int(self.is_log_scale)+1}, {self.min_value}, {self.max_value}"
        return command


    def __str__(self) -> str:
        return f"Measurement(name='{self.name}', range=[{self.min_value}, {self.max_value}])"

    # === Getters and setters ===
    @property
    def name(self) -> str:
        """Alphanumeric measurement label used in KXCI commands (always uppercased)."""
        return self._name
    
    @name.setter
    def name(self, value: str) -> None:
        if not value.isalnum() or not value[0].isalpha():
            raise KXCILimitationError("Measurement name must be alphanumeric and start with a letter")

        self._name = value.upper()
        # Derive the PMU channel number from the last character of the raw name.
        # For PMU channel names such as "pmu1-rpm1-2", the channel is the last
        # digit.  For plain alphanumeric names (SMU measurements) we fall back
        # to 0 so that the attribute is always present.
        self._channel: int = int(value[-1]) if value[-1].isdigit() else 0

    @property
    def min_value(self) -> float:
        """Lower bound of the measurement display range. Clamped to hardware limits."""
        return self._min_value
    
    @min_value.setter
    def min_value(self, value: float) -> None:
        minmax: tuple[int, int] = (-9999, 9999) if self.unit == SourceType.VOLT else (-999, 999)
        self._min_value = min(max(value, minmax[0]), minmax[1])

    @property
    def max_value(self) -> float:
        """Upper bound of the measurement display range. Clamped to hardware limits."""
        return self._max_value
    
    @max_value.setter
    def max_value(self, value: float) -> None:
        minmax: tuple[int, int] = (-9999, 9999) if self.unit == SourceType.VOLT else (-999, 999)
        self._max_value = min(max(value, minmax[0]), minmax[1])
