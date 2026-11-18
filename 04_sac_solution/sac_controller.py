"""SAC-based Industrial HVAC Controller for Bay 1 Cleanroom.

Replaces the 2 regression trees and PINN with a unified Soft Actor-Critic (SAC) model,
integrating:
1. Soft Actor-Critic continuous optimal policy (Haarnoja et al., 2018).
2. Continuous Action Masking for slew-rate & pressure floor enforcement (Kumar et al., 2023).
3. Uncertainty-aware Double-Q critic disagreement gatekeeper & fallback (Ding et al., 2024, CLUE).
4. Industrial OPC-UA watchdog heartbeat & simulation-to-real architecture (Silvestri et al., 2024, ETH Zurich).
"""

import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bay1_control import PLCSafetyChecker, bounded, is_finite_number, pressure_minimum_command
from bay1_model import CONTROL, LIMITS, environment_violations
from bay1_policy import upcoming_requirements, SENSOR_FEATURES

from sac_agent import SACAgent, extract_sac_features


MODEL_PATH = Path(__file__).resolve().parent / "sac_weights.json"
PERIOD_S = CONTROL["control_period_s"]


class SACCleanroomController:
    """Industrial Cleanroom Controller driven by Soft Actor-Critic (SAC)."""

    def __init__(self, plant, weights_path=None, *, uncertainty_threshold=25.0, use_gpr=True):
        self.plant = plant
        self.plc = PLCSafetyChecker(plant)
        self.weights_path = Path(weights_path) if weights_path else MODEL_PATH
        self.uncertainty_threshold = uncertainty_threshold
        self.use_gpr = use_gpr

        self.agent = SACAgent()
        if self.weights_path.exists():
            try:
                self.agent.load_weights(self.weights_path)
                self.model_loaded = True
            except Exception as e:
                print(f"Warning: Failed to load SAC weights from {self.weights_path}: {e}")
                self.model_loaded = False
        else:
            self.model_loaded = False

        # Optional GPR for double uncertainty verification (Ding et al., CLUE 2024)
        self.gpr = None
        if self.use_gpr:
            try:
                from bay1_gpr import CleanroomGPR
                self.gpr = CleanroomGPR(plant)
            except Exception:
                self.gpr = None

        # Industrial Watchdog Heartbeat (Silvestri et al., Applied Energy 2024 / ETH Zurich)
        self.watchdog_counter = 0
        self.watchdog_heartbeat = True
        self.watchdog_healthy = True
        self.last_healthy_now_s = 0.0

        # Physical Momentum Tracking (Biemann et al., Applied Energy 2021)
        self.prev_temp = None
        self.prev_dp = None

    def command_setpoints(self, sensors, q_mes_kw, particle_gen_rate, network_connected=True, *,
                          now_s, dt_sec=PERIOD_S, forecast=()):
        if not is_finite_number(now_s):
            raise ValueError("now_s must be a finite PLC clock value")

        # 1. Update Industrial Watchdog Heartbeat (Silvestri et al., 2024)
        self.watchdog_counter += 1
        self.watchdog_heartbeat = (self.watchdog_counter % 2 == 0)

        # Heartbeat timeout check: If network lost or interval between calls exceeds 2.5 * dt_sec -> Fail-safe
        heartbeat_timeout = max(30.0, dt_sec * 2.5)
        if not network_connected or (now_s - self.last_healthy_now_s > heartbeat_timeout and self.last_healthy_now_s > 0.0):
            self.watchdog_healthy = False
        else:
            self.watchdog_healthy = True
            self.last_healthy_now_s = now_s

        sensor_ok, _ = self.plc.validate_sensors(sensors)
        load_ok = all(is_finite_number(val) and val >= 0.0 for val in (q_mes_kw, particle_gen_rate))
        disturbance = self.plc.disturbance_from_sensors(sensors, q_mes_kw, particle_gen_rate) if sensor_ok and load_ok else None

        command = (None, None)
        reason = None
        fallback_floor = None
        critic_uncertainty = 0.0
        critic_q_min = 0.0
        raw_action = np.zeros(2, dtype=np.float64)

        if not self.watchdog_healthy:
            reason = "Mất tín hiệu Watchdog Heartbeat OPC-UA (>30s)"
        elif not load_ok:
            reason = "Tải MES hoặc nguồn hạt không hợp lệ"
        elif not self.model_loaded:
            reason = "Chưa nạp bộ trọng số SAC Agent"
        elif dt_sec != PERIOD_S:
            reason = "Chu kỳ lấy mẫu không khớp chu kỳ huấn luyện SAC (10s)"
        elif disturbance is not None:
            max_pressure = self.plant.compute_pressure_steady(
                self.plant.mau_max_airflow, disturbance.exhaust_m3_s, disturbance.door_fraction,
            )
            if max_pressure < LIMITS["dp_min"]:
                reason = "MAU tối đa không đủ giữ chênh áp tối thiểu"
            else:
                upcoming, fallback_floor = upcoming_requirements(self.plant, disturbance, forecast, dt_sec)
                (lo_mau, hi_mau), (lo_ffu, hi_ffu) = self.plc.reachable_bounds(dt_sec)
                lo_mau = bounded(fallback_floor, lo_mau, hi_mau)

                # Check if current environment has critical violation -> Fallback to PLC
                if environment_violations(sensors):
                    reason = "Phát hiện vi phạm ngưỡng môi trường - Fallback về PLC luật cứng"
                else:
                    # 2. Extract normalized state features with physical momentum (Biemann et al., 2021)
                    dt_min = max(0.1, dt_sec / 60.0)
                    temp_vel = (sensors["temp"] - self.prev_temp) / dt_min if self.prev_temp is not None else 0.0
                    dp_vel = (sensors["dp"] - self.prev_dp) / dt_min if self.prev_dp is not None else 0.0
                    self.prev_temp = float(sensors["temp"])
                    self.prev_dp = float(sensors["dp"])

                    features = extract_sac_features(
                        sensors, disturbance, upcoming, lo_mau, self.plc.prev_u_mau, self.plc.prev_u_ffu,
                        temp_velocity=temp_vel, dp_velocity=dp_vel,
                    )

                    # 3. Deterministic Actor Inference (Haarnoja et al., 2018 Section 5.2)
                    raw_action = self.agent.get_action(features, deterministic=True)

                    # 4. Continuous Action Masking (Kumar et al., 2023)
                    # Maps a_raw in [-1, 1] linearly to reachable, safe bounds [lo, hi]
                    u_mau_cmd = lo_mau + 0.5 * (raw_action[0] + 1.0) * (hi_mau - lo_mau)
                    u_ffu_cmd = lo_ffu + 0.5 * (raw_action[1] + 1.0) * (hi_ffu - lo_ffu)
                    command = (float(np.clip(u_mau_cmd, 0.0, 1.0)), float(np.clip(u_ffu_cmd, 0.0, 1.0)))

                    # 5. Epistemic Uncertainty Quantification via Double-Q Disagreement (Ding et al., CLUE 2024)
                    critic_uncertainty, critic_q_min = self.agent.evaluate_uncertainty(features, raw_action)
                    if critic_uncertainty > self.uncertainty_threshold:
                        reason = f"SAC Cảnh báo bất định: Double-Q bất đồng {critic_uncertainty:.1f} > ngưỡng {self.uncertainty_threshold:.1f}"

                    # 6. Supplementary GPR uncertainty check (if enabled)
                    if self.gpr is not None and command[0] is not None and reason is None:
                        try:
                            gpr_pred = self.gpr.predict_transition(command[0], command[1], sensors, disturbance, dt_sec)
                            if gpr_pred.get("prediction_source") == "gpr":
                                bounds = gpr_pred.get("prediction_bounds", {})
                                if "dp" in bounds and bounds["dp"][0] < LIMITS["dp_min"]:
                                    reason = f"GPR cảnh báo: Cận dưới ΔP ({bounds['dp'][0]:.1f} Pa) < ngưỡng an toàn"
                                elif "particle_count" in bounds and bounds["particle_count"][1] > LIMITS["particles_01_max"]:
                                    reason = f"GPR cảnh báo: Cận trên hạt ({bounds['particle_count'][1]:.0f}/m³) vượt ISO Class 3"
                        except Exception:
                            pass

        timing = {"now_s": now_s, "command_time_s": now_s if command[0] is not None else None}
        fallback = {} if fallback_floor is None else {"fallback_mau_floor": fallback_floor}

        # 7. Hardware PLC Safety Gatekeeper
        result = self.plc.check_and_filter(
            *command, sensors, network_connected and self.watchdog_healthy, disturbance=disturbance, dt_sec=dt_sec,
            optimizer_reason=reason, **timing, **fallback,
        )

        return result | {
            "requested_u_mau": command[0],
            "requested_u_ffu": command[1],
            "sac_raw_action": raw_action.tolist(),
            "sac_uncertainty": float(critic_uncertainty),
            "critic_q_min": float(critic_q_min),
            "watchdog_heartbeat": self.watchdog_heartbeat,
            "watchdog_healthy": self.watchdog_healthy,
            "ai_inferences": int(command[0] is not None and reason is None),
            "ai_command_rejected": command[0] is not None and result["status"] == "FAIL_SAFE_ACTIVE",
        }
