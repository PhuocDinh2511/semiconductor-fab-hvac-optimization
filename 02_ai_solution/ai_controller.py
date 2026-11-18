"""
AI-CDCV Integrated Cleanroom HVAC Controller
Architecture:
1. Fast Imitation Policy (Learned offline from Physics-Constrained MPC):
   - Real-time online setpoint generation in < 0.1 ms (O(1) latency).
   - Completely replaces fragile online iterative optimization solvers (SLSQP).
2. PINN Multi-Physics Transition Engine (CleanroomPINN):
   - Evaluates forward state transitions adhering strictly to First Law of Thermodynamics
     and mass-conservation ODEs.
3. GPR Uncertainty & Out-of-Distribution Monitor (CleanroomGPR):
   - Computes predictive residual variance (sigma^2) and kernel support.
   - Flags out-of-distribution operating anomalies or sensor drifts.
4. PLC Safety Gatekeeper & Fail-Safe Interlock (PLCSafetyChecker):
   - Industrial deterministic verification of operational bounds, ramp-rate limits (4%/min),
     positive pressure (dP >= 15 Pa), ISO Class 3 particulate limits, and SEMI F21 AMC levels.
   - Activates conservative physical fail-safe fallback whenever GPR or PINN flags uncertainty.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bay1_control import AIEnergyOptimizer, PLCSafetyChecker
from bay1_policy import DirectFanController
from bay1_pinn import CleanroomPINN
from bay1_gpr import CleanroomGPR
from bay1_model import CleanroomPlant, CONTROL


class AICDCVController(DirectFanController):
    """
    Unified 4-Tier Hybrid Controller:
    - Fast Policy (MPC imitation)
    - PINN (Thermal & physical state transitions)
    - GPR (Uncertainty Quantification)
    - PLC (Safety Interlock)
    """
    def __init__(self, plant_model=None, *, use_gpr=True, use_pinn=True):
        plant = plant_model if plant_model is not None else CleanroomPlant()
        super().__init__(plant, use_gpr=use_gpr, use_pinn=use_pinn)
        self.mpc_teacher = AIEnergyOptimizer(plant, use_gpr=use_gpr)

    def optimize_setpoints(self, sensor_data, q_mes_kw, particle_gen_rate, network_connected=True, *,
                           now_s=0.0, dt_sec=CONTROL["control_period_s"], forecast=()):
        """
        High-speed drop-in replacement for legacy optimize_setpoints:
        Executes fast policy inference (< 0.1 ms) instead of slow iterative online solvers,
        validated by PINN physics forecasts and GPR residual uncertainty checks.
        """
        return self.command_setpoints(
            sensor_data, q_mes_kw, particle_gen_rate, network_connected=network_connected,
            now_s=now_s, dt_sec=dt_sec, forecast=forecast
        )


__all__ = [
    "AICDCVController",
    "DirectFanController",
    "AIEnergyOptimizer",
    "PLCSafetyChecker",
    "CleanroomPINN",
    "CleanroomGPR"
]
