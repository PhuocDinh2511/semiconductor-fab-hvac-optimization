"""Historical interface for reproducing Bay 1's version 3 PINN experiments."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bay1_control import PLCSafetyChecker
from bay1_pinn import CleanroomPINN as ThermalPINN


class CleanroomPINN(ThermalPINN):
    def predict(self, u_mau, u_ffu, current_state, q_mes_kw, particle_gen_rate, dt_sec=60.0):
        disturbance = PLCSafetyChecker.disturbance_from_sensors(current_state, q_mes_kw, particle_gen_rate)
        return self.predict_transition(u_mau, u_ffu, current_state, disturbance, dt_sec)


__all__ = ["CleanroomPINN"]
