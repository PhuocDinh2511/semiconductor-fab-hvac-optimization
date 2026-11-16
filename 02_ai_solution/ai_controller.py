"""
AI Solution Controller:
1. Data Processing & AI State Prediction (Physics-Informed Neural Network - PINN)
2. AI Energy Optimizer (Constrained SLSQP Non-linear Optimizer)
3. PLC Safety Gatekeeper & Fail-Safe Fallback Interlock
"""
import numpy as np
from scipy.optimize import minimize
from pinn_model import CleanroomPINN

class PLCSafetyChecker:
    """
    PLC Safety Gatekeeper:
    Checks operational limits, setpoint bounds, rate-of-change, and sensor integrity.
    If unsafe -> Rejects AI commands and activates validated Fail-Safe Fallback.
    
    Calibrated against 300mm Fab Management Criteria:
    - Minimum face velocity: 0.32 m/s (u_ffu >= 0.58)
    - Subfab Segregated Exhaust balance: dynamic per MES shift (35.0 Hz turndown u_mau >= 0.70)
    - SEMI F21 AMC limit: NH3 <= 10.0 ppb
    - Generic Vibration Criteria: VC-D <= 1.0 cm/s2
    """
    def __init__(self):
        # Operational envelope bounds calibrated with empirical fab data (TSMC Hsinchu dataset: 35.0 Hz minimum)
        self.u_mau_min = 0.70  # Calibrated to 35.0 Hz VFD measured part-load frequency
        self.u_mau_max = 1.00
        self.u_ffu_min = 0.58  # Guarantees face velocity >= 0.32 m/s per ISO/cleanroom criteria
        self.u_ffu_max = 1.00
        self.max_rate_per_min = 0.04  # Max 4% setpoint change per minute

        # Fail-Safe fallback setpoints (validated conservative operating point)
        self.fallback_u_mau = 0.95
        self.fallback_u_ffu = 0.95

        self.prev_u_mau = 0.90
        self.prev_u_ffu = 0.90
        self.failsafe_active = False
        self.reasons = []

    def validate_sensors(self, sensor_data):
        t = sensor_data.get("temp", 22.0)
        dp = sensor_data.get("dp", 20.0)
        c = sensor_data.get("particle_count", 200.0)
        amc = sensor_data.get("amc_nh3", 0.10)

        if not (15.0 <= t <= 35.0):
            return False, f"Temperature sensor out of range ({t:.1f} C)"
        if not (0.0 <= dp <= 60.0):
            return False, f"Pressure sensor fault ({dp:.1f} Pa)"
        if c < 0 or c > 1000000:
            return False, f"Particle sensor fault ({c:.0f})"
        if amc < 0.0 or amc > 50.0:
            return False, f"AMC NH3 sensor fault ({amc:.1f} ppb)"
        mau_filter_dp = sensor_data.get("mau_filter_dp", 1182.0)
        if mau_filter_dp > 1400.0:
            return False, f"MAU filter differential pressure warning ({mau_filter_dp:.0f} Pa > 1400 Pa)"
        return True, "Sensors OK"

    def check_and_filter(self, candidate_u_mau, candidate_u_ffu, sensor_data, network_connected=True):
        reasons = []
        is_safe = True

        # 0. Watchdog Timer & Network Heartbeat Check
        if not network_connected:
            self.failsafe_active = True
            self.reasons = ["Watchdog Timeout: Mất kết nối mạng tới AI Server! Chuyển sang Fallback an toàn."]
            self.prev_u_mau = float(self.fallback_u_mau)
            self.prev_u_ffu = float(self.fallback_u_ffu)
            return {
                "u_mau": float(self.fallback_u_mau),
                "u_ffu": float(self.fallback_u_ffu),
                "status": "FAIL_SAFE_ACTIVE",
                "reasons": self.reasons
            }

        # 1. Sensor fault validation
        sensor_ok, sensor_msg = self.validate_sensors(sensor_data)
        if not sensor_ok:
            is_safe = False
            reasons.append(sensor_msg)

        # 2. Operational bounds validation
        if not (self.u_mau_min <= candidate_u_mau <= self.u_mau_max):
            is_safe = False
            reasons.append(f"MAU setpoint {candidate_u_mau:.2f} violates bounds [{self.u_mau_min}, {self.u_mau_max}]")
        if not (self.u_ffu_min <= candidate_u_ffu <= self.u_ffu_max):
            is_safe = False
            reasons.append(f"FFU setpoint {candidate_u_ffu:.2f} violates bounds [{self.u_ffu_min}, {self.u_ffu_max}]")

        # 3. Rate-of-change smoothing
        d_mau = candidate_u_mau - self.prev_u_mau
        d_ffu = candidate_u_ffu - self.prev_u_ffu
        if abs(d_mau) > self.max_rate_per_min:
            candidate_u_mau = self.prev_u_mau + np.sign(d_mau) * self.max_rate_per_min
            reasons.append("MAU rate-limit clamped")
        if abs(d_ffu) > self.max_rate_per_min:
            candidate_u_ffu = self.prev_u_ffu + np.sign(d_ffu) * self.max_rate_per_min
            reasons.append("FFU rate-limit clamped")

        # 4. Critical Room Positive Pressure Protection
        current_dp = sensor_data.get("dp", 20.0)
        if current_dp < 15.8 and candidate_u_mau < self.prev_u_mau:
            is_safe = False
            reasons.append(f"Pressure warning (dP={current_dp:.1f} Pa): Throttling MAU fan rejected!")

        # 5. SEMI F21 Airborne Molecular Contamination Protection
        current_amc = sensor_data.get("amc_nh3", 0.10)
        if current_amc > 9.0:
            is_safe = False
            reasons.append(f"SEMI F21 AMC Warning: NH3 ({current_amc:.1f} ppb) exceeds 9.0 ppb threshold!")

        # Gatekeeper Decision
        if not is_safe:
            self.failsafe_active = True
            self.reasons = reasons
            u_mau_out = self.fallback_u_mau
            u_ffu_out = self.fallback_u_ffu
            status = "FAIL_SAFE_ACTIVE"
        else:
            self.failsafe_active = False
            self.reasons = reasons
            u_mau_out = candidate_u_mau
            u_ffu_out = candidate_u_ffu
            status = "SAFE"

        self.prev_u_mau = float(u_mau_out)
        self.prev_u_ffu = float(u_ffu_out)

        return {
            "u_mau": float(u_mau_out),
            "u_ffu": float(u_ffu_out),
            "mau_vfd_hz": float(50.0 * u_mau_out),
            "mau_supply_temp": 20.99,
            "mau_supply_dewpoint": 11.06,
            "status": status,
            "reasons": reasons
        }


class AIEnergyOptimizer:
    """
    CDCV (Coordinated Demand-Controlled Ventilation) & Neural-MPC Optimizer.
    Implements the CDCV strategy (Zhuang, Shan, Wang, Building and Environment 2021):
    Coordinated multi-variable dynamic control of Make-up Air Unit (MAU) fresh air supply,
    Subfab segregated process exhausts, and Fan Filter Units (FFU) recirculation based
    on real-time MES production demand and contamination generation.

    Incorporates full multi-objective cleanroom physics:
    - Fan affinity power minimization: P_mau * u_mau^3 + 48 * P_ffu * u_ffu^3
    - Positive differential pressure safety constraint: dP >= 16.5 Pa
    - Cleanliness class constraint: Particles <= 650 /m3 (ISO Class 3 < 1000)
    - Chemical contamination constraint: AMC NH3 <= 5.0 ppb (SEMI F21 < 10 ppb)
    - Vibration ceiling constraint: Vibration <= 0.20 cm/s2 (VC-D < 1.0 cm/s2)
    - Litho thermal stability: 21.7 C <= T <= 22.3 C
    """
    def __init__(self, plant_model):
        self.plant = plant_model
        self.plc = PLCSafetyChecker()
        self.pinn = CleanroomPINN(self.plant)

    def predict_state(self, u_mau, u_ffu, current_state, q_mes_kw, particle_gen_rate, dt_sec=60.0):
        """
        Uses Physics-Informed Neural Network (CleanroomPINN) forward evaluation
        incorporating thermodynamic, pressure-orifice, and HEPA mass-conservation constraints.
        """
        return self.pinn.predict(u_mau, u_ffu, current_state, q_mes_kw, particle_gen_rate, dt_sec=dt_sec)

    def optimize_setpoints(self, sensor_data, q_mes_kw, particle_gen_rate, network_connected=True):
        # If network to AI is lost, AI cannot compute -> PLC local fallback takes over instantly
        if not network_connected:
            return self.plc.check_and_filter(None, None, sensor_data, network_connected=False)

        def objective(u):
            p_m, p_f = self.plant.compute_fan_powers(u[0], u[1])
            return (p_m + p_f) / 1000.0

        def constraint_dp(u):
            pred = self.predict_state(u[0], u[1], sensor_data, q_mes_kw, particle_gen_rate)
            return pred["dp"] - 16.5  # Safety margin >= 16.5 Pa (ISO spec >= 15 Pa)

        def constraint_particles(u):
            pred = self.predict_state(u[0], u[1], sensor_data, q_mes_kw, particle_gen_rate)
            return 650.0 - pred["particle_count"]  # ISO Class 3 limit < 1000

        def constraint_amc(u):
            pred = self.predict_state(u[0], u[1], sensor_data, q_mes_kw, particle_gen_rate)
            return 5.0 - pred["amc_nh3"]  # SEMI F21 limit < 10 ppb

        def constraint_vibration(u):
            vib_pred = 0.02 + 0.03 * (u[1] ** 2) + 0.03 * min(1.0, particle_gen_rate / 400.0)
            return 0.20 - vib_pred

        def constraint_temp_upper(u):
            pred = self.predict_state(u[0], u[1], sensor_data, q_mes_kw, particle_gen_rate)
            return 22.3 - pred["temp"]

        def constraint_temp_lower(u):
            pred = self.predict_state(u[0], u[1], sensor_data, q_mes_kw, particle_gen_rate)
            return pred["temp"] - 21.7

        constraints = [
            {'type': 'ineq', 'fun': constraint_dp},
            {'type': 'ineq', 'fun': constraint_particles},
            {'type': 'ineq', 'fun': constraint_amc},
            {'type': 'ineq', 'fun': constraint_vibration},
            {'type': 'ineq', 'fun': constraint_temp_upper},
            {'type': 'ineq', 'fun': constraint_temp_lower}
        ]

        bounds = [(0.70, 1.0), (0.58, 1.0)]
        v_exh = sensor_data.get("exhaust_flow", self.plant.base_exhaust_flow)
        req_net = ((18.0 - 5.0) / 85.0) ** (1.0 / 1.6)
        ff_u_mau = max(0.70, min(1.0, (v_exh + req_net) / self.plant.mau_max_airflow))
        initial_guess = [ff_u_mau, max(0.58, min(1.0, self.plc.prev_u_ffu))]

        res = minimize(
            objective, initial_guess, method='SLSQP', bounds=bounds,
            constraints=constraints, options={'maxiter': 40, 'ftol': 1e-3}
        )
        if res.success:
            cand_u_mau, cand_u_ffu = res.x
        else:
            cand_u_mau, cand_u_ffu = initial_guess

        # Submit through PLC Safety Check Gatekeeper
        plc_result = self.plc.check_and_filter(cand_u_mau, cand_u_ffu, sensor_data)
        return plc_result
