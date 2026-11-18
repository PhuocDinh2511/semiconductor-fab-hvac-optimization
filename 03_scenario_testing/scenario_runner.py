"""Run and export the five shared Bay 1 scenarios."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bay1_simulation import run_all_scenarios_and_export, run_scenario_comparison, simulate_single_mode

__all__ = ["run_all_scenarios_and_export", "run_scenario_comparison", "simulate_single_mode"]

if __name__ == "__main__":
    run_all_scenarios_and_export()
