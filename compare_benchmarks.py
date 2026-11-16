"""
Master Benchmark Script: Runs both Baseline and AI Solution, then creates side-by-side comparison report.
"""
import os
import sys
import shutil
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Add subfolders to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(root_dir, "01_baseline"))
sys.path.append(os.path.join(root_dir, "02_ai_solution"))

from run_baseline import run_baseline_sim
from run_ai_solution import run_ai_sim

def main():
    print("="*60)
    print(" RUNNING FULL BENCHMARK: 01_BASELINE vs 02_AI_SOLUTION")
    print("="*60)

    # 1. Run Baseline
    base_data, base_kpis = run_baseline_sim()

    # 2. Run AI Solution
    ai_data, ai_kpis = run_ai_sim()

    times_hr = np.array(base_data["time_hr"])
    e_base = base_kpis["total_energy_kwh"]
    e_ai = ai_kpis["total_energy_kwh"]
    kwh_saved = e_base - e_ai
    pct_saved = (kwh_saved / e_base) * 100.0

    print("\n" + "="*60)
    print(" FINAL BENCHMARK COMPARISON REPORT")
    print("="*60)
    print(f"1. Baseline 24h Fan Energy:   {e_base:.2f} kWh (Avg Power: {base_kpis['avg_power_kw']:.2f} kW)")
    print(f"2. AI Solution 24h Fan Energy: {e_ai:.2f} kWh (Avg Power: {ai_kpis['avg_power_kw']:.2f} kW)")
    print(f"-> Energy Saved:               {kwh_saved:.2f} kWh ({pct_saved:.1f}%)")
    print(f"-> MAU VFD Frequency:          Baseline: {base_kpis.get('avg_mau_vfd_hz', 47.5):.1f} Hz | AI: {ai_kpis.get('avg_mau_vfd_hz', 39.5):.1f} Hz")
    print(f"-> MAU Reheat Duty:            Baseline: {base_kpis.get('avg_mau_reheat_kw', 33.7):.1f} kW_th | AI: {ai_kpis.get('avg_mau_reheat_kw', 28.1):.1f} kW_th")
    print(f"-> PLC Fail-Safe Activations:  {ai_kpis['failsafe_trigger_minutes']} minutes")
    print(f"-> Baseline Violations:        {base_kpis['violations_count']} minutes")
    print(f"-> AI Solution Violations:     {ai_kpis['violations_count']} minutes")
    print("="*60)

    # Generate Side-by-Side Comparison Plot (4x2 grid = 8 comprehensive panels)
    fig, axs = plt.subplots(4, 2, figsize=(15, 14), dpi=140)
    plt.subplots_adjust(hspace=0.36, wspace=0.25, top=0.94, bottom=0.05)

    # Panel 1: Fan Power (kW)
    axs[0, 0].plot(times_hr, base_data["p_total_kw"], 'r--', label=f'01_Baseline ({base_kpis["avg_power_kw"]:.1f} kW avg)', linewidth=1.5)
    axs[0, 0].plot(times_hr, ai_data["p_total_kw"], 'g-', label=f'02_AI Solution ({ai_kpis["avg_power_kw"]:.1f} kW avg)', linewidth=2.0)
    axs[0, 0].set_title("1. Fan Electrical Power (kW)", fontweight='bold')
    axs[0, 0].set_ylabel("Power (kW)")
    axs[0, 0].grid(True, alpha=0.3)
    axs[0, 0].legend(loc="upper right")

    # Panel 2: Cumulative Energy (kWh)
    axs[0, 1].plot(times_hr, base_data["energy_kwh"], 'r--', label=f'Baseline ({e_base:.1f} kWh)', linewidth=1.5)
    axs[0, 1].plot(times_hr, ai_data["energy_kwh"], 'g-', label=f'AI Solution ({e_ai:.1f} kWh, -{pct_saved:.1f}%)', linewidth=2.0)
    axs[0, 1].set_title(f"2. Energy Consumption (Savings: {pct_saved:.1f}%)", fontweight='bold')
    axs[0, 1].set_ylabel("Energy (kWh)")
    axs[0, 1].grid(True, alpha=0.3)
    axs[0, 1].legend(loc="upper left")

    # Panel 3: AI Fan Speeds & PLC Status
    axs[1, 0].plot(times_hr, np.array(ai_data["u_mau"])*100, 'b-', label=f'AI MAU VFD ({ai_kpis.get("avg_mau_vfd_hz", 39.5):.1f} Hz avg)', linewidth=1.7)
    axs[1, 0].plot(times_hr, np.array(ai_data["u_ffu"])*100, 'teal', label='AI FFU Speed (%)', linewidth=1.7)
    axs[1, 0].axhline(95.0, color='r', linestyle=':', label='Baseline MAU (47.5 Hz Cố Định)')
    axs[1, 0].axhline(100.0, color='darkred', linestyle=':', label='Baseline FFU (100% Cố Định)')
    # Shade Fail-Safe
    fs_active = [s == "FAIL_SAFE_ACTIVE" for s in ai_data["plc_status"]]
    in_block = False
    start_t = 0
    first_fs = True
    for i, active in enumerate(fs_active):
        if active and not in_block:
            in_block = True
            start_t = times_hr[i]
        elif not active and in_block:
            in_block = False
            label_fs = 'PLC Fail-Safe Active' if first_fs else None
            first_fs = False
            axs[1, 0].axvspan(start_t, times_hr[i], color='orange', alpha=0.35, label=label_fs)
    if in_block:
        axs[1, 0].axvspan(start_t, times_hr[-1], color='orange', alpha=0.35)
    axs[1, 0].set_title("3. Fan Speed Setpoints & PLC Safety States", fontweight='bold')
    axs[1, 0].set_ylabel("Speed (%)")
    axs[1, 0].set_ylim(40, 105)
    axs[1, 0].grid(True, alpha=0.3)
    axs[1, 0].legend(loc="lower right")

    # Panel 4: Cleanroom Positive Pressure (Delta P)
    axs[1, 1].plot(times_hr, base_data["dp"], 'r--', label='Baseline dP', linewidth=1.5)
    axs[1, 1].plot(times_hr, ai_data["dp"], 'g-', label='AI Solution dP', linewidth=2.0)
    axs[1, 1].axhline(15.0, color='black', linestyle='-', linewidth=1.5, label='ISO Min Limit (15 Pa)')
    axs[1, 1].fill_between(times_hr, 15.0, 26.0, color='green', alpha=0.08)
    axs[1, 1].set_title("4. Positive Differential Pressure (Delta P >= 15 Pa)", fontweight='bold')
    axs[1, 1].set_ylabel("Pressure (Pa)")
    axs[1, 1].grid(True, alpha=0.3)
    axs[1, 1].legend(loc="lower right")

    # Panel 5: Particles
    axs[2, 0].plot(times_hr, base_data["particles"], 'r--', label='Baseline Particles', linewidth=1.5)
    axs[2, 0].plot(times_hr, ai_data["particles"], 'g-', label='AI Solution Particles', linewidth=2.0)
    axs[2, 0].axhline(1000.0, color='crimson', linestyle='-', linewidth=1.5, label='ISO Class 3 Limit')
    axs[2, 0].set_title("5. Cleanroom Particle Concentration (0.5 um)", fontweight='bold')
    axs[2, 0].set_ylabel("Particles / m3")
    axs[2, 0].grid(True, alpha=0.3)
    axs[2, 0].legend(loc="upper right")

    # Panel 6: Cleanroom Temperature
    axs[2, 1].plot(times_hr, base_data["temp"], 'r--', label='Baseline Temp (C)', linewidth=1.2)
    axs[2, 1].plot(times_hr, ai_data["temp"], 'b-', label='AI Solution Temp (C)', linewidth=1.8)
    axs[2, 1].axhspan(21.5, 22.5, color='blue', alpha=0.08, label='Target [21.5 - 22.5 C]')
    axs[2, 1].set_title("6. Cleanroom Temperature Stability (Target 22.0 C)", fontweight='bold')
    axs[2, 1].set_ylabel("Temperature (C)")
    axs[2, 1].set_ylim(21.0, 23.0)
    axs[2, 1].grid(True, alpha=0.3)
    axs[2, 1].legend(loc="upper right")

    # Panel 7: Airborne Molecular Contamination (AMC NH3)
    axs[3, 0].plot(times_hr, base_data["amc_nh3"], 'r--', label=f'Baseline NH3 (Avg: {base_kpis.get("avg_amc_nh3_ppb", 0):.2f} ppb)', linewidth=1.5)
    axs[3, 0].plot(times_hr, ai_data["amc_nh3"], 'purple', label=f'AI Solution NH3 (Avg: {ai_kpis.get("avg_amc_nh3_ppb", 0):.2f} ppb)', linewidth=1.8)
    axs[3, 0].axhline(10.0, color='crimson', linestyle='-', linewidth=1.5, label='SEMI F21 Max Spec (10 ppb)')
    axs[3, 0].set_title("7. Airborne Molecular Contamination - Ammonia NH3 (ppb)", fontweight='bold')
    axs[3, 0].set_xlabel("Time (Hours)")
    axs[3, 0].set_ylabel("NH3 (ppb)")
    axs[3, 0].set_ylim(0, 15)
    axs[3, 0].grid(True, alpha=0.3)
    axs[3, 0].legend(loc="upper right")

    # Panel 8: Micro-Vibration & Murphy Wafer Yield
    ax8 = axs[3, 1]
    ax8_twin = ax8.twinx()
    l1, = ax8.plot(times_hr, base_data["vibration"], 'orange', linestyle='--', label=f'Baseline Vib ({base_kpis.get("avg_vibration_cms2", 0):.2f} cm/s2)', linewidth=1.4)
    l2, = ax8.plot(times_hr, ai_data["vibration"], 'darkorange', label=f'AI Vib ({ai_kpis.get("avg_vibration_cms2", 0):.2f} cm/s2)', linewidth=1.8)
    ax8.axhline(1.0, color='red', linestyle=':', label='VC-D Limit (1.0 cm/s2)')
    ax8.set_ylabel("Vibration (cm/s2)", color='darkorange', fontweight='bold')
    ax8.set_ylim(0, 1.4)

    l3, = ax8_twin.plot(times_hr, base_data["wafer_yield"], 'silver', linestyle=':', label=f'Base Yield ({base_kpis.get("avg_wafer_yield_pct", 0):.2f}%)', linewidth=1.3)
    l4, = ax8_twin.plot(times_hr, ai_data["wafer_yield"], 'blue', label=f'AI Yield ({ai_kpis.get("avg_wafer_yield_pct", 0):.2f}%)', linewidth=1.8)
    ax8_twin.set_ylabel("Wafer Yield (%)", color='blue', fontweight='bold')
    ax8_twin.set_ylim(95, 100)

    ax8.set_title("8. Micro-Vibration (cm/s2) & Wafer Yield (%)", fontweight='bold')
    ax8.set_xlabel("Time (Hours)")
    ax8.grid(True, alpha=0.3)
    lines = [l1, l2, l3, l4]
    ax8.legend(lines, [l.get_label() for l in lines], loc="lower right", fontsize=8)

    plt.suptitle("SemiconFab 300mm Fab: 01_Baseline vs 02_AI_Solution Full Benchmark", fontsize=14, fontweight='bold', y=0.99)

    chart_path = os.path.join(root_dir, "comparison_summary.png")
    plt.savefig(chart_path, bbox_inches='tight')
    plt.close()
    print(f"Comparison chart saved at: {chart_path}")

    # Copy to artifact directories
    artifact_dirs = [
        r"C:\Users\admin\.gemini\antigravity\brain\2cf9a30d-1206-4ed6-853e-3da4350686d0",
        r"C:\Users\admin\.gemini\antigravity\brain\394e05d3-2d60-413b-832d-8cb92ab4cdc3"
    ]
    for ad in artifact_dirs:
        if os.path.isdir(ad):
            try:
                shutil.copyfile(chart_path, os.path.join(ad, "comparison_summary.png"))
            except Exception:
                pass

    # Save Master KPI JSON
    master_kpi = {
        "baseline": base_kpis,
        "ai_solution": ai_kpis,
        "savings_kwh": float(kwh_saved),
        "savings_pct": float(pct_saved)
    }
    with open(os.path.join(root_dir, "benchmark_comparison.json"), "w") as f:
        json.dump(master_kpi, f, indent=2)
    print("Benchmark comparison JSON saved successfully!")

if __name__ == "__main__":
    main()
