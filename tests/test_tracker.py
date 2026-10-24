"""Tests for partial-failure value tracking."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

PACKAGE = "bwt_tracker_pkg"
PACKAGE_PATH = Path(__file__).parents[1] / "custom_components" / "bwt_aqa_perla"
sys.modules[PACKAGE] = types.ModuleType(PACKAGE)
sys.modules[PACKAGE].__path__ = [str(PACKAGE_PATH)]
for _name in ("protocol", "tracker"):
    _spec = importlib.util.spec_from_file_location(
        f"{PACKAGE}.{_name}", PACKAGE_PATH / f"{_name}.py"
    )
    _module = importlib.util.module_from_spec(_spec)
    sys.modules[_spec.name] = _module
    _spec.loader.exec_module(_module)
tracker = sys.modules[f"{PACKAGE}.tracker"]


def test_missing_value_keeps_last_value_until_max_misses() -> None:
    store = tracker.ValueTracker(max_misses=3)
    store.update(["a", "b"], {"a": 1, "b": 2})
    assert store.update(["a", "b"], {"a": 1}) == {"a": 1, "b": 2}
    assert store.update(["a", "b"], {"a": 1}) == {"a": 1, "b": 2}
    assert store.update(["a", "b"], {"a": 1}) == {"a": 1}


def test_value_recovers_and_resets_miss_counter() -> None:
    store = tracker.ValueTracker(max_misses=2)
    store.update(["a"], {"a": 1})
    store.update(["a"], {})
    store.update(["a"], {"a": 5})
    assert store.update(["a"], {}) == {"a": 5}


def test_never_seen_value_stays_absent() -> None:
    store = tracker.ValueTracker()
    assert store.update(["a", "b"], {"a": 1}) == {"a": 1}


def test_values_not_requested_are_untouched() -> None:
    store = tracker.ValueTracker(max_misses=1)
    store.update(["a", "b"], {"a": 1, "b": 2})
    assert store.update(["a"], {"a": 3}) == {"a": 3, "b": 2}


def test_software_version_is_split() -> None:
    store = tracker.ValueTracker()
    result = store.update(
        ["software_version"], {"software_version": "Version: 3.94#155"}
    )
    assert result["software_version_power_electronics"] == "3.94"
    assert result["software_version_control_panel"] == "155"


def test_remaining_capacity_percent_is_derived() -> None:
    result = tracker.derive_values(
        {
            "nominal_capacity_column_1": 800,
            "remaining_capacity_column_1": 600,
            "nominal_capacity_column_2": 0,
            "remaining_capacity_column_2": 0,
        }
    )
    assert result["remaining_capacity_percent_column_1"] == 75.0
    assert "remaining_capacity_percent_column_2" not in result


def test_regenerating_column_follows_bit_7_during_regeneration_steps() -> None:
    assert (
        tracker.derive_values({"regeneration_step": 0x82})["regenerating_column"]
        == "column_2"
    )
    assert (
        tracker.derive_values({"regeneration_step": 0x02})["regenerating_column"]
        == "column_1"
    )


def test_regenerating_column_is_none_in_operation_and_t_steps() -> None:
    for raw in (0, 17, 145, 18, 146):
        assert (
            tracker.derive_values({"regeneration_step": raw})["regenerating_column"]
            == "none"
        )
