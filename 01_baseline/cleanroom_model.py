"""Compatibility import for the shared Bay 1 plant."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bay1_model import CleanroomPlant
from bay1_scenarios import get_standard_mes_scenario

__all__ = ["CleanroomPlant", "get_standard_mes_scenario"]
