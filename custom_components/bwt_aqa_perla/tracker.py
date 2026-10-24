"""Merge partial poll results and expire values that stop being reported."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from .protocol import normalize_regeneration_step, split_software_version

MAX_MISSES = 3

# Steps 1-10 are the regeneration proper; higher ones are the T-steps.
REGENERATION_LAST_STEP = 10

type Value = int | float | str


class ValueTracker:
    """Keep the last known values across partially failing polls."""

    def __init__(self, max_misses: int = MAX_MISSES) -> None:
        """Initialize an empty tracker."""

        self._max_misses = max_misses
        self._misses: dict[str, int] = {}
        self.values: dict[str, Value] = {}

    def update(
        self, requested: Iterable[str], received: Mapping[str, Value]
    ) -> dict[str, Value]:
        """Apply one poll round and return the resulting full value set.

        A requested value that is missing keeps its previous value until it
        has been missed `max_misses` times in a row, then it is dropped.
        """

        for key in requested:
            if key in received:
                self.values[key] = received[key]
                self._misses[key] = 0
            elif key in self.values:
                self._misses[key] = self._misses.get(key, 0) + 1
                if self._misses[key] >= self._max_misses:
                    del self.values[key]
                    del self._misses[key]
        return derive_values(self.values)


def derive_values(values: Mapping[str, Value]) -> dict[str, Value]:
    """Return values extended by keys computed from other values."""

    result = dict(values)
    version = values.get("software_version")
    if isinstance(version, str):
        electronics, control_panel = split_software_version(version)
        result["software_version_power_electronics"] = electronics
        if control_panel is not None:
            result["software_version_control_panel"] = control_panel
    step = values.get("regeneration_step")
    if isinstance(step, int):
        # Bit 7 names the column during a real regeneration step (1-10); it
        # alternates between successive regenerations and, in the T-steps
        # that run every few hours, carries a different meaning.
        if 1 <= normalize_regeneration_step(step) <= REGENERATION_LAST_STEP:
            result["regenerating_column"] = "column_2" if step & 0x80 else "column_1"
        else:
            result["regenerating_column"] = "none"
    for column in (1, 2):
        nominal = values.get(f"nominal_capacity_column_{column}")
        remaining = values.get(f"remaining_capacity_column_{column}")
        if (
            isinstance(nominal, int | float)
            and isinstance(remaining, int | float)
            and nominal > 0
        ):
            result[f"remaining_capacity_percent_column_{column}"] = round(
                remaining / nominal * 100, 1
            )
    return result
