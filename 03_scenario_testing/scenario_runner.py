"""
scenario_runner.py
Core simulation engine for executing and benchmarking cleanroom operational scenarios
comparing 01_baseline (Traditional Fixed) vs 02_ai_solution (CDCV + PINN-MPC + PLC Gatekeeper).
"""
import os
import sys
import json
import numpy as np

# Ensure root paths are in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(os.path.join(root_dir, "01_baseline"))
sys.path.append(os.path.join(root_dir, "02_ai_solution"))
sys.path.append(current_dir)

from cleanroom_model import CleanroomPlant
from baseline_controller import BaselineController
from ai_controller import AIEnergyOptimizer
from scenarios_config import get_all_scenarios


def simulate_single_mode(scenario_data, mode="ai"):
    """
    Run 24h simulation (1440 minutes) for a given scenario under specified mode.
    mode: 'baseline' or 'ai'
    """
    times_hr = scenario_data["times_hr"]
    n_steps = len(times_hr)
    q_mes = scenario_data["q_mes"]
    particle_gen = scenario_data["particle_gen"]
    exhaust_override = scenario_data["exhaust_override"]
    outdoor_temp = scenario_data.get("outdoor_temp", np.full(n_steps, 29.93))
    outdoor_rh = scenario_data.get("outdoor_rh", np.full(n_steps, 80.0))
    amc_mult = scenario_data.get("amc_multiplier", np.ones(n_steps))
    sensor_glitch = scenario_data.get("sensor_glitch", np.zeros(n_steps, dtype=bool))
    ai_fault = scenario_data.get("ai_fault_injection", np.zeros(n_steps, dtype=bool))

    plant = CleanroomPlant()

    if mode == "baseline":
        controller = BaselineController(u_mau=0.95, u_ffu=1.00)
    else:
        controller = AIEnergyOptimizer(plant)

    history = {
        "time_hr": times_hr.tolist(),
        "u_mau": [],
        "u_ffu": [],
        "mau_vfd_hz": [],
        "temp": [],
        "rh": [],
        "dp": [],
        "particles": [],
        "amc_nh3": [],
        "vibration": [],
        "wafer_yield": [],
        "p_total_kw": [],
        "energy_kwh": [],
        "reheat_kw": [],
        "plc_status": []
    }

    cum_energy = 0.0
    cum_reheat = 0.0
    failsafe_minutes = 0
    violations_count = 0

    for i in range(n_steps):
        # Update ambient outdoor conditions if scenario modulates them
        plant.outdoor_temp = float(outdoor_temp[i])
        plant.outdoor_rh = float(outdoor_rh[i])

        # Current sensor readings
        sensor_data = {
            "temp": plant.temp,
            "rh": plant.rh,
            "dp": plant.dp,
            "particle_count": plant.particle_count,
            "amc_nh3": plant.amc_nh3,
            "vibration": plant.vibration,
            "mau_filter_dp": plant.mau_filter_dp
        }

        # Apply sensor EMI glitch if flagged in scenario
        if sensor_glitch[i]:
            sensor_data["temp"] += 12.0 # Corrupted reading
            sensor_data["dp"] = -5.0

        # Step controller
        if mode == "baseline":
            cmd = controller.get_setpoints(sensor_data, q_mes[i])
            plc_stat = "NORMAL_BASELINE"
        else:
            net_connected = not ai_fault[i]
            cmd = controller.optimize_setpoints(sensor_data, q_mes[i], particle_gen[i], network_connected=net_connected)
            plc_stat = cmd.get("status", "OPTIMAL_NORMAL")
            if plc_stat == "FAIL_SAFE_ACTIVE":
                failsafe_minutes += 1

        # Advance plant physics
        res = plant.step(
            u_mau=cmd["u_mau"],
            u_ffu=cmd["u_ffu"],
            q_mes_kw=q_mes[i],
            particle_gen_rate=particle_gen[i],
            exhaust_override=exhaust_override[i],
            dt_sec=60.0
        )

        # Modulate AMC if scenario specifies high outgassing
        if amc_mult[i] > 1.0:
            plant.amc_nh3 = min(40.0, plant.amc_nh3 * (1.0 + 0.05 * (amc_mult[i] - 1.0)))

        # Accumulate metrics
        dt_hr = 1.0 / 60.0
        cum_energy += res["p_total_kw"] * dt_hr
        cum_reheat += res["mau_reheat_kw"] * dt_hr

        # Check safety violations (ISO Class 3 <= 1000, dP >= 15.0 Pa, AMC <= 10 ppb)
        is_violated = (res["dp"] < 15.0) or (res["particle_count"] > 1000.0) or (res["amc_nh3"] > 10.0) or (res["temp"] < 21.5 or res["temp"] > 22.5)
        if is_violated:
            violations_count += 1

        # Append to history
        history["u_mau"].append(float(cmd["u_mau"]))
        history["u_ffu"].append(float(cmd["u_ffu"]))
        history["mau_vfd_hz"].append(float(res["mau_vfd_hz"]))
        history["temp"].append(float(res["temp"]))
        history["rh"].append(float(res["rh"]))
        history["dp"].append(float(res["dp"]))
        history["particles"].append(float(res["particle_count"]))
        history["amc_nh3"].append(float(res["amc_nh3"]))
        history["vibration"].append(float(res["vibration"]))
        history["wafer_yield"].append(float(res["wafer_yield"]))
        history["p_total_kw"].append(float(res["p_total_kw"]))
        history["energy_kwh"].append(float(cum_energy))
        history["reheat_kw"].append(float(res["mau_reheat_kw"]))
        history["plc_status"].append(plc_stat)

    kpis = {
        "mode": mode,
        "total_energy_kwh": float(cum_energy),
        "avg_power_kw": float(cum_energy / 24.0),
        "total_reheat_energy_kwh": float(cum_reheat),
        "avg_reheat_kw": float(cum_reheat / 24.0),
        "avg_mau_vfd_hz": float(np.mean(history["mau_vfd_hz"])),
        "avg_ffu_speed_pct": float(np.mean(history["u_ffu"]) * 100.0),
        "min_dp_pa": float(np.min(history["dp"])),
        "avg_dp_pa": float(np.mean(history["dp"])),
        "max_particles": float(np.max(history["particles"])),
        "avg_particles": float(np.mean(history["particles"])),
        "max_amc_nh3_ppb": float(np.max(history["amc_nh3"])),
        "avg_amc_nh3_ppb": float(np.mean(history["amc_nh3"])),
        "avg_vibration_cms2": float(np.mean(history["vibration"])),
        "avg_wafer_yield_pct": float(np.mean(history["wafer_yield"])),
        "violations_count": int(violations_count),
        "failsafe_trigger_minutes": int(failsafe_minutes)
    }

    return history, kpis


def run_scenario_comparison(scenario_data):
    """
    Run both baseline and AI solution on a single scenario, computing comparative KPIs.
    """
    base_hist, base_kpis = simulate_single_mode(scenario_data, mode="baseline")
    ai_hist, ai_kpis = simulate_single_mode(scenario_data, mode="ai")

    e_base = base_kpis["total_energy_kwh"]
    e_ai = ai_kpis["total_energy_kwh"]
    saved_kwh = e_base - e_ai
    saved_pct = (saved_kwh / e_base) * 100.0

    reheat_base = base_kpis["total_reheat_energy_kwh"]
    reheat_ai = ai_kpis["total_reheat_energy_kwh"]
    reheat_saved_kwh = reheat_base - reheat_ai
    reheat_saved_pct = (reheat_saved_kwh / reheat_base) * 100.0

    summary = {
        "scenario_id": scenario_data["id"],
        "scenario_name": scenario_data["name"],
        "scenario_description": scenario_data["description"],
        "baseline": base_kpis,
        "ai_solution": ai_kpis,
        "savings_kwh": float(saved_kwh),
        "savings_pct": float(saved_pct),
        "reheat_saved_kwh": float(reheat_saved_kwh),
        "reheat_saved_pct": float(reheat_saved_pct)
    }

    return base_hist, ai_hist, summary


def run_all_scenarios_and_export():
    """
    Execute all 5 operational scenarios and export master summary JSON.
    """
    scenarios = get_all_scenarios()
    all_results = {}

    print("=" * 70)
    print(" EXECUTING ALL 5 SEMICONDUCTOR CLEANROOM OPERATIONAL SCENARIOS")
    print("=" * 70)

    for sc_id, sc_data in scenarios.items():
        print(f"\n---> Running {sc_data['name']} ...")
        _, _, summary = run_scenario_comparison(sc_data)
        all_results[sc_id] = summary

        print(f"   [Baseline] Energy: {summary['baseline']['total_energy_kwh']:.2f} kWh | Min dP: {summary['baseline']['min_dp_pa']:.2f} Pa")
        print(f"   [AI CDCV ] Energy: {summary['ai_solution']['total_energy_kwh']:.2f} kWh | Min dP: {summary['ai_solution']['min_dp_pa']:.2f} Pa")
        print(f"   ===> Fan Energy Saved: {summary['savings_kwh']:.2f} kWh ({summary['savings_pct']:.1f}%) | PLC Failsafe: {summary['ai_solution']['failsafe_trigger_minutes']} mins")

    # Export to JSON
    json_path = os.path.join(current_dir, "scenarios_benchmark_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Successfully saved scenarios results to {json_path}")

    return all_results


if __name__ == "__main__":
    run_all_scenarios_and_export()
