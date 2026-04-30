"""
Measurement.py - Python module defining the Measurement class to represent a specific measurement in the Keithley 4200A.
Author: Lucas LE DUDAL
"""
from ..consts import GraphPosition, MeasurementType, SourceType
from ..error import KXCILimitationError
from ..instrcomms import Communications


class Measurement:
    """
    This class represents a measurement configuration and its associated data.
    """

    def __init__(self, comm: Communications, name: str, measurement_type: MeasurementType = MeasurementType.SMU, steps: int = -1, min_value: float = 0.0, max_value: float = 0.0, is_log_scale: bool = False, unit: SourceType = SourceType.NONE, pmu_offset: int = 0, do_channel_ref: "Measurement | None" = None, pmu_rv: str = "") -> None:
        """
        Initialize a Measurement instance.

        Args:
            comm (Communications): The communication object used to query results.
            name (str): The name of the measurement.
            measurement_type (MeasurementType): Type of measurement between SMU or PMU_RPM.
            steps (int): The number of measurement steps.
            min_value (float): The minimum value.
            max_value (float): The maximum value.
            is_log_scale (bool): True for logarithmic scale, False for linear.
            unit (SourceType): The unit of the measurement.
            pmu_offset (int): Fallback column index when pmu_rv is not set.
            pmu_rv (str): requestedValues token for :PMU:DATA:GET (e.g. "VH", "TL").
                          When set the query requests this column explicitly so the
                          result is always at index 0, independent of acquire_high/low.
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
        self.pmu_offset: int = pmu_offset
        self.pmu_rv: str = pmu_rv
        self._do_channel_ref: "Measurement | None" = do_channel_ref
        self.name = name
        self.min_value = min_value
        self.max_value = max_value
        self.is_log_scale = is_log_scale

    def getResultAt(self, index: int) -> str:
        """
        Fetch the measurement result at a specific index.

        Args:
            index (int): The index at which to fetch the measurement result.

        Returns:
            str: The raw measurement result at the specified index.
        """
        if self.measurement_type == MeasurementType.PMU_RPM:
            rv_suffix = f", {self.pmu_rv}" if self.pmu_rv else ""
            raw = self._com.query(f":PMU:DATA:GET {self._channel}, {index - 1}, 1{rv_suffix}")
            self._com.checkForError()
            if raw:
                point = raw.strip().split(";")[0]
                if point:
                    values = point.split(",")
                    col = 0 if self.pmu_rv else self.pmu_offset
                    if len(values) > col:
                        return values[col]
            return "0.0"

        if self.measurement_type == MeasurementType.SMU_TIME:
            all_res = self.getAllResults()
            return str(all_res[index - 1]) if 0 < index <= len(all_res) else "0.0"

        str_result: str = self._com.query(f"RD '{self.name}', {index}")

        return str_result



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
        Fetch one value per step of this measurement, skipping inner-loop values.

        Args:
            precedent_dimensions: Measurements whose loops are nested inside this one.
                                  Their `steps` are multiplied together to form the stride.

        Returns:
            list[float]: `steps` values, one per unique output level of this measurement.
        """
        stride: int = 1
        if precedent_dimensions:
            for m in precedent_dimensions:
                stride *= m.steps

        if self.measurement_type in (MeasurementType.PMU_RPM, MeasurementType.SMU_TIME):
            all_res = self.getAllResults()
            results: list[float] = []
            for i in range(self.steps):
                idx = stride * i
                if idx < len(all_res):
                    results.append(all_res[idx])
                else:
                    results.append(0.0)
            return results

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
        if self.measurement_type == MeasurementType.PMU_RPM:
            total = int(self._com.query(f":PMU:DATA:COUNT? {self._channel}"))
            self._com.checkForError()
            if total == 0:
                return []

            BLOCK = 2048
            col = 0 if self.pmu_rv else self.pmu_offset
            rv_suffix = f", {self.pmu_rv}" if self.pmu_rv else ""
            l_readings: list[float] = []
            start = 0
            while start < total:
                raw_data = self._com.query(
                    f":PMU:DATA:GET {self._channel}, {start}, {min(BLOCK, total - start)}{rv_suffix}"
                )
                self._com.checkForError()
                if not raw_data:
                    break
                for point in raw_data.strip().split(";"):
                    if not point:
                        continue
                    values = point.split(",")
                    if len(values) > col:
                        val = values[col]
                        if self.isResultValid(val):
                            l_readings.append(float(val))
                start += BLOCK
            self._com.checkForError()
            return l_readings

        elif self.measurement_type == MeasurementType.SMU_TIME:
            channel = self._do_channel_ref.name if self._do_channel_ref else self._name
            raw = self._com.query(f"DO '{channel}T'")
            self._com.checkForError()
            if not raw:
                return []
            l_readings = []
            for token in raw.strip().split(","):
                token = token.strip()
                if not token:
                    continue
                # Strip status prefix if present (e.g. "N 1.23E-03" → "1.23E-03")
                if token[0].isalpha():
                    parts = token.split()
                    token = parts[1] if len(parts) > 1 else token[1:]
                try:
                    val = float(token)
                    if val != 0.0:
                        l_readings.append(val)
                except ValueError:
                    pass
            return l_readings

        elif self.measurement_type == MeasurementType.SMU:
            l_readings: list[float] = []
            index: int = 1
            value: str = self.getResultAt(index)
            index+=1
            while self.isResultValid(value):
                l_readings.append(float(value))
                value = self.getResultAt(index)
                index += 1
            self._com.checkForError()
            return l_readings

        return []

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
        """
        Measurement label used in KXCI commands (always uppercased).
        
        Constraints:
            Must be alphanumeric
            Must be uppercase (will be converted if not)
            Must start with a letter
            Must not exceed 6 characters
        """
        return self._name
    
    @name.setter
    def name(self, value: str) -> None:
        if not value.isalnum() or not value[0].isalpha():
            raise KXCILimitationError("Measurement name must be alphanumeric and start with a letter")
        if len(value) > 6:
            raise KXCILimitationError("Measurement name must be less than 6 characters")

        self._name = value.upper()
        # For PMU, the channel is the last digit of the name. No reason to rename it anyway.
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
