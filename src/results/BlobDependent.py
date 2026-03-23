"""
BlobDependent.py - Python module defining the BlobDependent class to store
N-dimensional data arrays with named, typed parameter axes, analogous to the
MATLAB Dependent class used in K4200 measurement workflows.
Author: Lucas LE DUDAL
"""

from __future__ import annotations

import numpy as np


class BlobDependent:
    """
    Stores an N-dimensional NumPy array with named parameter axes.

    Each dimension of the data array is associated with a named parameter and
    a corresponding 1-D array of coordinate values, following the same
    convention as the MATLAB ``Dependent`` class:

    * The *k*-th key of ``parameters`` corresponds to the *k*-th axis of
      ``data``.
    * The length of each coordinate array must match the size of its axis.

    Attributes:
        label (str): Human-readable label for the stored quantity
            (e.g. ``"Drain current [A]"``).
        log (str): Free-form log string (measurement notes, timestamps, …).

    Example:
        >>> import numpy as np
        >>> dep = BlobDependent(
        ...     data=np.random.rand(3, 5),
        ...     parameters={
        ...         "frequency_Hz": np.linspace(1e9, 3e9, 3),
        ...         "voltage_V":    np.linspace(-0.1, 0.1, 5),
        ...     },
        ...     label="Transconductance [S]",
        ... )
        >>> dep.value.shape
        (3, 5)
        >>> dep.dependency
        ['frequency_Hz', 'voltage_V']
    """

    def __init__(
        self,
        data: np.ndarray,
        parameters: dict[str, np.ndarray],
        label: str = "",
        log: str = "",
    ) -> None:
        """
        Initialise a :class:`BlobDependent` instance.

        Args:
            data (np.ndarray): The N-dimensional data array.  Its shape must
                satisfy ``data.shape[k] == len(parameters[k-th key])`` for
                every axis *k*.
            parameters (dict[str, np.ndarray]): Ordered mapping of parameter
                names to their 1-D coordinate arrays.  Insertion order defines
                the axis correspondence (guaranteed by Python ≥ 3.7).
            label (str): Optional human-readable label for the stored quantity.
            log (str): Optional free-form log string.

        Raises:
            ValueError: If the number of parameters does not match
                ``data.ndim``, or if a coordinate array's length does not
                match the corresponding data axis size.

        Example:
            >>> import numpy as np
            >>> dep = BlobDependent(
            ...     data=np.zeros((4, 6)),
            ...     parameters={
            ...         "vg_V": np.linspace(-1, 1, 4),
            ...         "vd_V": np.linspace(0, 2, 6),
            ...     },
            ...     label="Id [A]",
            ...     log="2026-03-23 room temperature",
            ... )
        """
        data = np.asarray(data)

        if len(parameters) != data.ndim:
            raise ValueError(
                f"Number of parameters ({len(parameters)}) must match "
                f"data.ndim ({data.ndim})."
            )

        validated: dict[str, np.ndarray] = {}
        for k, (name, coords) in enumerate(parameters.items()):
            coords_arr = np.asarray(coords, dtype=float)
            if coords_arr.ndim != 1:
                raise ValueError(
                    f"Coordinate array for parameter '{name}' must be 1-D; "
                    f"got shape {coords_arr.shape}."
                )
            if len(coords_arr) != data.shape[k]:
                raise ValueError(
                    f"Coordinate array for parameter '{name}' has length "
                    f"{len(coords_arr)}, but data axis {k} has size "
                    f"{data.shape[k]}."
                )
            validated[name] = coords_arr

        self._data: np.ndarray = data
        self._parameters: dict[str, np.ndarray] = validated
        self.label: str = label
        self.log: str = log

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def value(self) -> np.ndarray:
        """The raw N-dimensional data array."""
        return self._data

    @property
    def parameters(self) -> dict[str, np.ndarray]:
        """
        Ordered mapping from parameter name to its 1-D coordinate array.

        The *k*-th entry corresponds to the *k*-th axis of :attr:`value`.
        """
        return self._parameters

    @property
    def dependency(self) -> list[str]:
        """Ordered list of parameter (axis) names."""
        return list(self._parameters.keys())

    @property
    def shape(self) -> tuple[int, ...]:
        """Shape of the data array, identical to ``value.shape``."""
        return self._data.shape

    @property
    def ndim(self) -> int:
        """Number of dimensions of the data array, identical to ``value.ndim``."""
        return self._data.ndim

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        dims = ", ".join(
            f"{name}({len(coords)})"
            for name, coords in self._parameters.items()
        )
        return (
            f"BlobDependent({dims}, "
            f"label={self.label!r}, "
            f"dtype={self._data.dtype})"
        )

    def __str__(self) -> str:
        return self.__repr__()
