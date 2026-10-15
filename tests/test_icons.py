"""Consistency of icons.json with the entity translations."""

from __future__ import annotations

import json
from pathlib import Path

COMPONENT = Path(__file__).parents[1] / "custom_components" / "bwt_aqa_perla"


def test_icon_keys_exist_in_entity_translations() -> None:
    icons = json.loads((COMPONENT / "icons.json").read_text())["entity"]
    names = json.loads((COMPONENT / "strings.json").read_text())["entity"]
    for platform, entities in icons.items():
        assert set(entities) <= set(names[platform]), platform
