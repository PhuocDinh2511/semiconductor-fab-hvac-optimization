"""Run 24-Hour Simulation for Baseline (Fixed-Speed Traditional Operation)"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bay1_plots import run_daily_mode


def run_baseline_sim():
    print("=" * 76)
    print("  LAUNCHING 24-HOUR BASELINE CLEANROOM SIMULATION (01_BASELINE)")
    print("  Fixed Speed Fans: 95% MAU / 100% FFU (Traditional Standard Operation)")
    print("=" * 76)
    trace, kpis = run_daily_mode("baseline")
    print("\n[✓] SIMULATION COMPLETED SUCCESSFULLY!")
    print(f"    - Fan Electric Energy:              {kpis['total_energy_kwh']:.2f} kWh")
    print(f"    - Out-of-spec violation minutes:    {kpis['violation_minutes']:.0f} min")
    print("=" * 76)
    return trace, kpis


if __name__ == "__main__":
    run_baseline_sim()
