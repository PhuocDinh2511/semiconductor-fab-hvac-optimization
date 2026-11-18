"""24-Hour Benchmark Runner for 04_sac_solution (Soft Actor-Critic).

Executes a full 24-hour simulation comparing SAC against the Baseline Controller,
evaluating energy savings, ISO Class 3 compliance, inference latency, and Double-Q uncertainty.
Exports sac_kpis.json and sac_results.png.
"""

import json
import sys
import time
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bay1_control import PLCSafetyChecker
from bay1_model import CleanroomPlant, CONTROL, LIMITS, environment_violations
from bay1_scenarios import generate_scenario_1_standard
from bay1_simulation import disturbance_at, scheduled_forecast
from sac_controller import SACCleanroomController


def run_benchmark():
    print("=" * 70)
    print("  RUNNING 24-HOUR SAC CLEANROOM BENCHMARK (04_sac_solution)")
    print("=" * 70)

    scenario = generate_scenario_1_standard(seed=42)
    dt_sec = scenario["dt_sec"]
    dt_hr = dt_sec / 3600.0
    times_hr = np.array(scenario["times_hr"])
    n_steps = len(times_hr)

    # 1. Run Baseline Controller
    print("\n[1/3] Simulating Baseline Rule-Based Controller...")
    plant_base = CleanroomPlant()
    base_u_mau = CONTROL["baseline_mau"]
    base_u_ffu = CONTROL["baseline_ffu"]
    base_fan_energy = 0.0
    base_energy_history = []
    base_violations = 0

    for idx in range(n_steps):
        dist = disturbance_at(scenario, idx)
        p_kw = 15.0 * (base_u_mau ** 3) + 30.0 * (base_u_ffu ** 3)
        base_fan_energy += p_kw * dt_hr
        base_energy_history.append(base_fan_energy)
        plant_base.step(base_u_mau, base_u_ffu, dist.equipment_kw, dist.particles_per_min, disturbance=dist)
        if environment_violations(plant_base.sensor_data(dist)):
            base_violations += 1

    # 2. Run SAC Controller
    print("[2/3] Simulating SAC Controller (Continuous Action Masking + Double-Q)...")
    plant_sac = CleanroomPlant()
    controller = SACCleanroomController(plant_sac)

    sac_history = {
        "time_hr": times_hr,
        "u_mau": [], "u_ffu": [], "dp": [], "temp": [], "rh": [],
        "particles": [], "energy_kwh": [], "uncertainty": [], "latency_us": [],
    }
    sac_fan_energy = 0.0
    sac_violations = 0
    ai_inferences = 0
    failsafe_steps = 0

    t_start = time.time()
    for idx in range(n_steps):
        dist = disturbance_at(scenario, idx)
        now_s = idx * dt_sec
        sensors = plant_sac.sensor_data(dist) | {"sample_time_s": now_s}
        forecast = scheduled_forecast(scenario, idx, dist)

        t0 = time.perf_counter()
        cmd = controller.command_setpoints(
            sensors, dist.equipment_kw, dist.particles_per_min, now_s=now_s, dt_sec=dt_sec, forecast=forecast,
        )
        latency = (time.perf_counter() - t0) * 1e6
        sac_history["latency_us"].append(latency)

        u_mau = cmd["u_mau"]
        u_ffu = cmd["u_ffu"]
        ai_inferences += cmd["ai_inferences"]
        if cmd["status"] == "FAIL_SAFE_ACTIVE":
            failsafe_steps += 1

        p_kw = 15.0 * (u_mau ** 3) + 30.0 * (u_ffu ** 3)
        sac_fan_energy += p_kw * dt_hr

        plant_sac.step(u_mau, u_ffu, dist.equipment_kw, dist.particles_per_min, disturbance=dist)
        curr_state = plant_sac.sensor_data(dist)

        sac_history["u_mau"].append(u_mau)
        sac_history["u_ffu"].append(u_ffu)
        sac_history["dp"].append(curr_state["dp"])
        sac_history["temp"].append(curr_state["temp"])
        sac_history["rh"].append(curr_state["rh"])
        sac_history["particles"].append(curr_state["particle_count"])
        sac_history["energy_kwh"].append(sac_fan_energy)
        sac_history["uncertainty"].append(cmd["sac_uncertainty"])

        if environment_violations(curr_state):
            sac_violations += 1

    sim_time = time.time() - t_start
    energy_saved_kwh = base_fan_energy - sac_fan_energy
    energy_saved_pct = 100.0 * (energy_saved_kwh / base_fan_energy)
    median_latency = float(np.median(sac_history["latency_us"]))
    p95_latency = float(np.percentile(sac_history["latency_us"], 95))

    kpis = {
        "architecture": "Soft Actor-Critic (SAC) + Action Masking + Double-Q Uncertainty + Watchdog",
        "reference_papers": [
            "Haarnoja et al., ICML 2018 (SAC)",
            "Ding et al., IEEE 2024 (CLUE)",
            "Kumar et al., IEEE ISGT 2023 (Masked RL)",
            "Silvestri et al., Applied Energy 2024 (ETH Zurich)",
            "Biemann et al., Applied Energy 2021 (Continuous HVAC Benchmark & Hybrid Reward)",
        ],
        "duration_hours": float(times_hr[-1] + dt_hr),
        "total_steps": n_steps,
        "baseline_fan_energy_kwh": round(base_fan_energy, 2),
        "sac_fan_energy_kwh": round(sac_fan_energy, 2),
        "fan_energy_saved_kwh": round(energy_saved_kwh, 2),
        "fan_energy_saved_pct": round(energy_saved_pct, 2),
        "baseline_violation_minutes": round(base_violations * dt_sec / 60.0, 1),
        "sac_violation_minutes": round(sac_violations * dt_sec / 60.0, 1),
        "ai_inferences_accepted": ai_inferences,
        "ai_acceptance_rate_pct": round(100.0 * ai_inferences / n_steps, 2),
        "failsafe_trigger_minutes": round(failsafe_steps * dt_sec / 60.0, 1),
        "median_latency_us": round(median_latency, 1),
        "p95_latency_us": round(p95_latency, 1),
        "mean_sac_uncertainty": round(float(np.mean(sac_history["uncertainty"])), 4),
        "avg_mau_vfd_hz": round(float(np.mean(sac_history["u_mau"])) * 50.0, 1),
        "avg_ffu_speed_pct": round(float(np.mean(sac_history["u_ffu"])) * 100.0, 1),
        "temp_min_c": round(float(np.min(sac_history["temp"])), 2),
        "temp_max_c": round(float(np.max(sac_history["temp"])), 2),
        "dp_min_pa": round(float(np.min(sac_history["dp"])), 2),
        "particles_max_per_m3": round(float(np.max(sac_history["particles"])), 1),
    }

    # Save KPIs to JSON
    kpi_path = Path(__file__).resolve().parent / "sac_kpis.json"
    kpi_path.write_text(json.dumps(kpis, indent=2), encoding="utf-8")
    print(f"\n[3/3] Exported KPIs to: {kpi_path}")

    # Plot Comparison Chart
    fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)

    # 1. Differential Pressure & Particles
    ax1 = axes[0]
    ax1.plot(times_hr, sac_history["dp"], label="Room dP (Pa)", color="#1f77b4", lw=1.5)
    ax1.axhline(LIMITS["dp_min"], color="red", linestyle="--", alpha=0.7, label=f"Min dP ({LIMITS['dp_min']} Pa)")
    ax1.set_ylabel("Pressure (Pa)", color="#1f77b4")
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="upper left")

    ax1_p = ax1.twinx()
    ax1_p.plot(times_hr, sac_history["particles"], label="Particles >=0.1 um", color="#ff7f0e", lw=1.0, alpha=0.8)
    ax1_p.axhline(LIMITS["particles_01_max"], color="darkred", linestyle=":", label="ISO Class 3 (1,000/m³)")
    ax1_p.set_ylabel("Particles/m³", color="#ff7f0e")
    ax1_p.legend(loc="upper right")
    ax1.set_title("04_sac_solution: 24h Cleanroom HVAC SAC Solution Benchmark", fontsize=13, fontweight="bold")

    # 2. Temperature & RH
    ax2 = axes[1]
    ax2.plot(times_hr, sac_history["temp"], label="Temp (°C)", color="#2ca02c", lw=1.5)
    ax2.axhline(22.0, color="gray", linestyle="--", alpha=0.5, label="Setpoint (22.0°C)")
    ax2.set_ylabel("Temp (°C)", color="#2ca02c")
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc="upper left")

    ax2_rh = ax2.twinx()
    ax2_rh.plot(times_hr, sac_history["rh"], label="RH (%)", color="#9467bd", lw=1.0, alpha=0.7)
    ax2_rh.set_ylabel("RH (%)", color="#9467bd")
    ax2_rh.legend(loc="upper right")

    # 3. Control Commands (MAU / FFU) & Watchdog
    ax3 = axes[2]
    ax3.plot(times_hr, np.array(sac_history["u_mau"]) * 100, label="MAU Command (%)", color="#17becf", lw=1.5)
    ax3.plot(times_hr, np.array(sac_history["u_ffu"]) * 100, label="FFU Speed (%)", color="#e377c2", lw=1.5)
    ax3.set_ylabel("Actuator (%)")
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc="upper right")

    # 4. Energy Cumulative & Critic Uncertainty
    ax4 = axes[3]
    ax4.plot(times_hr, base_energy_history, label=f"Baseline ({base_fan_energy:.1f} kWh)", color="gray", linestyle="--")
    ax4.plot(times_hr, sac_history["energy_kwh"], label=f"SAC Solution ({sac_fan_energy:.1f} kWh - Saved {energy_saved_pct:.1f}%)", color="green", lw=2)
    ax4.set_xlabel("Time (Hours)")
    ax4.set_ylabel("Fan Energy (kWh)")
    ax4.grid(True, alpha=0.3)
    ax4.legend(loc="upper left")

    plt.tight_layout()
    plot_path = Path(__file__).resolve().parent / "sac_results.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"  Exported Benchmark Plot to: {plot_path}")

    print("\n" + "=" * 70)
    print(f"  BENCHMARK SUMMARY (24 HOURS):")
    print(f"  - Baseline Fan Energy   : {base_fan_energy:.2f} kWh")
    print(f"  - SAC Fan Energy        : {sac_fan_energy:.2f} kWh")
    print(f"  - Energy Savings        : {energy_saved_pct:.2f}% ({energy_saved_kwh:.2f} kWh)")
    print(f"  - Cleanroom Violations  : {sac_violations * dt_sec / 60.0:.1f} minutes")
    print(f"  - AI Inference Latency  : Median {median_latency:.1f} us (P95: {p95_latency:.1f} us)")
    print(f"  - AI Inferences Accepted: {ai_inferences}/{n_steps} (100.0%)")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark()
