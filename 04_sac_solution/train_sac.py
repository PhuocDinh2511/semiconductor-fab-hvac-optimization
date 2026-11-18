"""Offline Pre-training and SAC Reinforcement Learning for Bay 1 Cleanroom.

Implements the multi-stage training curriculum and optimizations from:
1. Haarnoja et al. (2018): Soft Actor-Critic with automatic temperature alpha tuning.
2. Ding et al. (2024, CLUE): Epistemic uncertainty quantification via Double-Q critic disagreement.
3. Kumar et al. (2023): Continuous Action Masking for slew-rate & pressure floor enforcement.
4. Silvestri et al. (2024, ETH Zurich): Simulation-to-real pre-training via Behavioral Cloning (BC).
5. Biemann et al. (2021, Applied Energy):
   - Hybrid Gaussian + Piecewise Trapezoid multi-objective reward formulation.
   - Action Smoothness Regularization against mechanical chatter/fatigue.
   - Dynamic temporal momentum states (temp_velocity, dp_velocity) for 29-feature representation.
"""

import sys
import time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bay1_control import AIEnergyOptimizer, PLCSafetyChecker, bounded
from bay1_model import CleanroomPlant, CONTROL, LIMITS
from bay1_policy import upcoming_requirements
from bay1_scenarios import (
    generate_scenario_1_standard,
    generate_scenario_3_summer_heatwave,
    generate_scenario_5_weekend_maintenance,
)
from bay1_simulation import disturbance_at, scheduled_forecast
from sac_agent import SACAgent, extract_sac_features


PERIOD_S = CONTROL["control_period_s"]
MODEL_PATH = Path(__file__).resolve().parent / "sac_weights.json"


def compute_hybrid_reward(sensors, u_mau, u_ffu, prev_u_mau=None, prev_u_ffu=None, dt_sec=PERIOD_S):
    """Hybrid Gaussian + Piecewise Trapezoid Reward Function (Biemann et al., Applied Energy 2021).
    
    Provides smooth dense gradients near optimal setpoints (Gaussian bell) and steep linear
    restoring slopes outside safe bounds (Piecewise Trapezoid), preventing vanishing gradients
    and penalizing mechanical actuator chatter.
    """
    # 1. Temperature Reward: Gaussian bell within +/-0.5 C of 22.0 C, linear slope outside
    t_diff = abs(sensors["temp"] - 22.0)
    sigma_t = 0.25
    if t_diff <= 0.5:
        r_temp = np.exp(-0.5 * (t_diff / sigma_t) ** 2)
    else:
        # Linear trapezoid penalty outside +/-0.5 C
        r_temp = np.exp(-0.5 * (0.5 / sigma_t) ** 2) - 4.0 * (t_diff - 0.5)

    # 2. Differential Pressure Reward: Gaussian bell at 18.0 Pa, steep linear slope below 15.0 Pa
    dp = sensors["dp"]
    sigma_dp = 2.0
    if dp >= 18.0:
        r_dp = np.exp(-0.5 * ((dp - 18.0) / sigma_dp) ** 2)
    elif dp >= 15.0:
        # Smooth interpolation between 15.0 Pa and 18.0 Pa
        r_dp = (dp - 15.0) / 3.0
    else:
        # Steep linear trapezoid penalty below 15.0 Pa (ISO Class 3 containment breach)
        r_dp = -8.0 * (15.0 - dp)

    # 3. Particle Count Penalty (ISO Class 3: 1,000 /m3 for >= 0.1 um)
    particles = sensors["particle_count"]
    if particles <= LIMITS["particles_01_max"]:
        r_particle = 0.5 * (1.0 - (particles / LIMITS["particles_01_max"]))
    else:
        r_particle = -5.0 * ((particles - LIMITS["particles_01_max"]) / 200.0)

    # 4. Fan Energy Cost (Cubic Affinity Law: P ~ u^3)
    p_fan_kw = 15.0 * (u_mau ** 3) + 30.0 * (u_ffu ** 3)
    e_kwh = p_fan_kw * (dt_sec / 3600.0)
    r_energy = -1.2 * e_kwh

    # 5. Action Smoothness Regularization (Biemann et al., Footnote 9)
    # Penalizes excessive rate of actuator change to prevent fan chatter and mechanical fatigue
    r_smooth = 0.0
    if prev_u_mau is not None and prev_u_ffu is not None:
        delta_mau = u_mau - prev_u_mau
        delta_ffu = u_ffu - prev_u_ffu
        r_smooth = -0.5 * (delta_mau ** 2 + delta_ffu ** 2)

    # Composite multi-objective reward
    composite_reward = (
        1.5 * r_temp +
        2.0 * r_dp +
        1.0 * r_particle +
        r_energy +
        r_smooth
    )
    return float(composite_reward)


def collect_mpc_demonstrations(scenario_func, seed):
    """Collect optimal demonstration transitions using the offline MPC teacher with 29 state features."""
    scenario = scenario_func(seed=seed)
    plant = CleanroomPlant()
    expert = AIEnergyOptimizer(plant, use_gpr=False)
    plc = PLCSafetyChecker(plant)

    states = []
    actions_raw = []
    rewards = []

    prev_temp = None
    prev_dp = None
    dt_sec = PERIOD_S
    dt_min = max(0.1, dt_sec / 60.0)

    for idx in range(len(scenario["times_hr"])):
        dist = disturbance_at(scenario, idx)
        plan = scheduled_forecast(scenario, idx, dist)
        sensors = plant.sensor_data(dist)

        # Track dynamic physical velocity (Biemann et al., 2021)
        temp_vel = (sensors["temp"] - prev_temp) / dt_min if prev_temp is not None else 0.0
        dp_vel = (sensors["dp"] - prev_dp) / dt_min if prev_dp is not None else 0.0
        prev_temp = float(sensors["temp"])
        prev_dp = float(sensors["dp"])

        upcoming, req_floor = upcoming_requirements(plant, dist, plan, dt_sec)
        (lo_mau, hi_mau), (lo_ffu, hi_ffu) = plc.reachable_bounds(dt_sec)
        lo_mau = bounded(req_floor, lo_mau, hi_mau)

        result = expert.optimize_setpoints(
            sensors, dist.equipment_kw, dist.particles_per_min, dt_sec=dt_sec, forecast=plan,
        )

        u_mau = result["u_mau"]
        u_ffu = result["u_ffu"]

        # Action Masking Inverse: Map [lo, hi] -> [-1, 1]
        a_mau = 2.0 * (u_mau - lo_mau) / max(1e-6, hi_mau - lo_mau) - 1.0
        a_ffu = 2.0 * (u_ffu - lo_ffu) / max(1e-6, hi_ffu - lo_ffu) - 1.0
        a_raw = np.clip([a_mau, a_ffu], -1.0, 1.0)

        feat = extract_sac_features(
            sensors, dist, upcoming, lo_mau, plc.prev_u_mau, plc.prev_u_ffu,
            temp_velocity=temp_vel, dp_velocity=dp_vel,
        )

        r = compute_hybrid_reward(
            sensors, u_mau, u_ffu, prev_u_mau=plc.prev_u_mau, prev_u_ffu=plc.prev_u_ffu, dt_sec=dt_sec,
        )

        states.append(feat)
        actions_raw.append(a_raw)
        rewards.append(r)

        plc.prev_u_mau = u_mau
        plc.prev_u_ffu = u_ffu
        plant.step(u_mau, u_ffu, dist.equipment_kw, dist.particles_per_min, disturbance=dist)

    return np.array(states), np.array(actions_raw), np.array(rewards)


def train():
    print("=" * 76)
    print("  TRAINING ADVANCED SOFT ACTOR-CRITIC (SAC) FOR CLEANROOM BAY 1")
    print("  Optimizations: Biemann et al. (2021) + CLUE (2024) + Action Masking (2023)")
    print("  State Dim: 29 | Action Dim: 2 | Auto-Alpha Entropy | Hybrid Reward")
    print("=" * 76)

    agent = SACAgent(state_dim=29, action_dim=2, hidden_dim=64, alpha=0.05, seed=631)

    # -------------------------------------------------------------
    # STAGE 1: Behavioral Cloning (Pre-training from MPC Demonstrations)
    # -------------------------------------------------------------
    print("\n[Stage 1/2] Generating MPC Teacher Demonstrations across scenarios...")
    t0 = time.time()
    s_list, a_list, r_list = [], [], []
    for gen, seed in [
        (generate_scenario_1_standard, 431),
        (generate_scenario_3_summer_heatwave, 432),
        (generate_scenario_5_weekend_maintenance, 433),
    ]:
        st, act, rew = collect_mpc_demonstrations(gen, seed)
        s_list.append(st)
        a_list.append(act)
        r_list.append(rew)

    all_states = np.vstack(s_list)
    all_actions = np.vstack(a_list)
    all_rewards = np.concatenate(r_list)
    print(f"  Collected {len(all_states)} expert transitions in {time.time() - t0:.2f}s")
    print(f"  Expert raw actions mean: {np.mean(all_actions, axis=0)}")
    print(f"  Expert hybrid rewards mean: {np.mean(all_rewards):.3f}")

    print("  Pre-training SAC Actor network via Behavioral Cloning (BC)...")
    bc_loss = agent.pretrain_behavioral_cloning(all_states, all_actions, epochs=150, lr=1e-3)
    print(f"  Behavioral Cloning MSE Loss: {bc_loss:.6f}")

    # -------------------------------------------------------------
    # STAGE 2: Off-Policy SAC Exploration with Replay Buffer & Auto-Alpha
    # -------------------------------------------------------------
    print("\n[Stage 2/2] Training Double-Q Critics & Fine-tuning SAC...")
    t1 = time.time()

    # Populate replay buffer with expert transitions and hybrid rewards
    for i in range(len(all_states) - 1):
        agent.buffer.add(all_states[i], all_actions[i], all_rewards[i], all_states[i + 1], done=False)

    # Initial Critic training on the replay buffer
    print(f"  Warming up Double-Q Critics on {agent.buffer.size} transitions...")
    for _ in range(800):
        agent.train_step(batch_size=64, lr_actor=2e-5, lr_critic=1e-3)

    # Roll out SAC in closed-loop environment across training scenarios
    scenarios = [
        generate_scenario_1_standard(seed=777),
        generate_scenario_3_summer_heatwave(seed=888),
    ]
    total_steps = 0
    dt_sec = PERIOD_S
    dt_min = max(0.1, dt_sec / 60.0)

    for sc_idx, sc in enumerate(scenarios):
        plant = CleanroomPlant()
        plc = PLCSafetyChecker(plant)
        prev_temp = None
        prev_dp = None

        for step in range(len(sc["times_hr"]) - 1):
            dist = disturbance_at(sc, step)
            plan = scheduled_forecast(sc, step, dist)
            sensors = plant.sensor_data(dist)

            temp_vel = (sensors["temp"] - prev_temp) / dt_min if prev_temp is not None else 0.0
            dp_vel = (sensors["dp"] - prev_dp) / dt_min if prev_dp is not None else 0.0
            prev_temp = float(sensors["temp"])
            prev_dp = float(sensors["dp"])

            upcoming, req_floor = upcoming_requirements(plant, dist, plan, dt_sec)
            (lo_mau, hi_mau), (lo_ffu, hi_ffu) = plc.reachable_bounds(dt_sec)
            lo_mau = bounded(req_floor, lo_mau, hi_mau)

            feat = extract_sac_features(
                sensors, dist, upcoming, lo_mau, plc.prev_u_mau, plc.prev_u_ffu,
                temp_velocity=temp_vel, dp_velocity=dp_vel,
            )

            # Sample action with stochastic exploration
            raw_action = agent.get_action(feat, deterministic=False)

            # Action Masking mapping
            u_mau = lo_mau + 0.5 * (raw_action[0] + 1.0) * (hi_mau - lo_mau)
            u_ffu = lo_ffu + 0.5 * (raw_action[1] + 1.0) * (hi_ffu - lo_ffu)
            u_mau = float(np.clip(u_mau, 0.0, 1.0))
            u_ffu = float(np.clip(u_ffu, 0.0, 1.0))

            plant.step(u_mau, u_ffu, dist.equipment_kw, dist.particles_per_min, disturbance=dist)

            next_dist = disturbance_at(sc, step + 1)
            next_sensors = plant.sensor_data(next_dist)
            next_plan = scheduled_forecast(sc, step + 1, next_dist)
            next_upcoming, next_req = upcoming_requirements(plant, next_dist, next_plan, dt_sec)
            (next_lo_mau, _), _ = plc.reachable_bounds(dt_sec)
            next_lo_mau = bounded(next_req, next_lo_mau, 1.0)

            next_temp_vel = (next_sensors["temp"] - prev_temp) / dt_min
            next_dp_vel = (next_sensors["dp"] - prev_dp) / dt_min

            next_feat = extract_sac_features(
                next_sensors, next_dist, next_upcoming, next_lo_mau, u_mau, u_ffu,
                temp_velocity=next_temp_vel, dp_velocity=next_dp_vel,
            )

            reward = compute_hybrid_reward(
                next_sensors, u_mau, u_ffu, prev_u_mau=plc.prev_u_mau, prev_u_ffu=plc.prev_u_ffu, dt_sec=dt_sec,
            )
            agent.buffer.add(feat, raw_action, reward, next_feat, done=False)

            # Train SAC networks
            if agent.buffer.size >= 64:
                metrics = agent.train_step(batch_size=64, lr_actor=5e-5, lr_critic=5e-4)

            plc.prev_u_mau = u_mau
            plc.prev_u_ffu = u_ffu
            total_steps += 1

        print(f"  Completed SAC environment rollout {sc_idx + 1}/{len(scenarios)} ({total_steps} steps) | Alpha: {agent.alpha:.4f}")

    print(f"  SAC Training finished in {time.time() - t1:.2f}s | Final Temperature Alpha: {agent.alpha:.4f}")

    # -------------------------------------------------------------
    # STAGE 3: Save Model Weights
    # -------------------------------------------------------------
    agent.save_weights(MODEL_PATH)
    print(f"\n[Stage 3/3] Successfully saved SAC model weights to: {MODEL_PATH}")
    print(f"  File size: {MODEL_PATH.stat().st_size:,} bytes")
    print("=" * 76)


if __name__ == "__main__":
    train()
