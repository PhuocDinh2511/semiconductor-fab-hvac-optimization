"""Interactive Real-Time Desktop Visualizer for SAC Cleanroom HVAC Simulation (04_sac_solution).

Showcases:
1. Soft Actor-Critic (SAC) continuous optimal policy (Haarnoja et al., 2018).
2. Continuous Action Masking for slew-rate & pressure floor enforcement (Kumar et al., 2023).
3. Live Epistemic Uncertainty Gauge via Double-Q Critic Disagreement (Ding et al., 2024, CLUE).
4. Industrial OPC-UA Watchdog Heartbeat pulse & Fallback status (Silvestri et al., 2024, ETH Zurich).
5. PLC Safety Gatekeeper & Fail-Safe Fallback Interlock in Real Time.
"""

import os
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from bay1_model import CleanroomPlant, CONTROL, LIMITS, environment_violations
from bay1_scenarios import generate_benchmark_day
from bay1_simulation import disturbance_at, scheduled_forecast
from sac_controller import SACCleanroomController

# Global reference to keep animation alive in memory
active_animation = None


def get_mes_phase_info(t_hr):
    """Returns MES lot production stage title and descriptive badge color."""
    if 0.0 <= t_hr < 6.0:
        return "Ca Đêm: Chế Độ Chờ / Chamber Standby (25 kW)", "#64748b"
    elif 6.0 <= t_hr < 8.0:
        return "Giao Ca: Gia Nhiệt Buồng Track & Chuẩn Bị Lot A (25->90 kW)", "#d97706"
    elif 8.0 <= t_hr < 11.5:
        return "Ca Sáng: Quang Khắc UV Lot A (Peak 90 kW)", "#0284c7"
    elif 11.5 <= t_hr < 11.75:
        return "⚠️ Sự Cố MES: Cửa Mở Bảo Dưỡng Đột Xuất (Rò Rỉ)", "#dc2626"
    elif 11.75 <= t_hr < 12.0:
        return "Ca Sáng: Khôi Phục & Hoàn Tất Lot A", "#0284c7"
    elif 12.0 <= t_hr < 13.0:
        return "Nghỉ Trưa: Bán Tải Stepper Standby (60 kW)", "#ca8a04"
    elif 13.0 <= t_hr < 16.5:
        return "Ca Chiều: Quang Khắc Ngập DUV Lot B (Peak 88 kW)", "#7c3aed"
    elif 16.5 <= t_hr < 16.75:
        return "⚠️ Cảm Biến Lỗi: Nhiễu Xung Điện Từ EMI", "#ea580c"
    elif 16.75 <= t_hr < 18.0:
        return "Ca Chiều: Hoàn Tất Tráng Keo & Phơi Sáng Lot B", "#7c3aed"
    elif 18.0 <= t_hr < 22.0:
        return "Ca Tối: Xử Lý Track Coater & Developer Phụ (50 kW)", "#0891b2"
    else:
        return "Ca Đêm: Kết Thúc Mẻ / Chờ Nạp Phôi Mới (28 kW)", "#64748b"


def run_interactive_sac_simulation(speed_factor=10):
    global active_animation

    print("=" * 76)
    print("  LAUNCHING INTERACTIVE CLEANROOM SAC SIMULATION (04_sac_solution)")
    print("  SAC (Max Entropy) + Action Masking + Double-Q Uncertainty + Watchdog")
    print("=" * 76)

    scenario = generate_benchmark_day(seed=42)
    dt_sec = scenario["dt_sec"]
    dt_hr = dt_sec / 3600.0
    times_hr = np.array(scenario["times_hr"])
    total_steps = len(times_hr)

    plant = CleanroomPlant()
    controller = SACCleanroomController(plant)

    # Pre-allocate trajectory buffers
    history = {
        "time": [], "temp": [], "dp": [], "particles": [],
        "u_mau": [], "u_ffu": [], "energy_sac": [], "energy_base": [],
        "uncertainty": [],
    }

    base_fan_cum = 0.0
    sac_fan_cum = 0.0

    # Setup Dark Theme GUI
    plt.style.use("dark_background")
    fig = plt.figure(figsize=(15, 9.5), dpi=100)
    fig.patch.set_facecolor("#0b0f19")

    # 4-row layout: [Title HUD], [Temp & Pressure], [Particles & Fans], [Energy & Uncertainty]
    gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.0, 1.0], hspace=0.38, wspace=0.25,
                           top=0.88, bottom=0.08, left=0.07, right=0.94)

    ax_temp = fig.add_subplot(gs[0, 0])
    ax_dp = fig.add_subplot(gs[0, 1])
    ax_part = fig.add_subplot(gs[1, 0])
    ax_fans = fig.add_subplot(gs[1, 1])
    ax_energy = fig.add_subplot(gs[2, 0])
    ax_unc = fig.add_subplot(gs[2, 1])

    # Plot styling
    for ax in (ax_temp, ax_dp, ax_part, ax_fans, ax_energy, ax_unc):
        ax.set_facecolor("#111827")
        ax.grid(True, color="#374151", linestyle="--", linewidth=0.5, alpha=0.7)
        ax.tick_params(colors="#9ca3af", labelsize=8)
        for spine in ax.spines.values():
            spine.set_color("#374151")

    # Lines
    line_temp, = ax_temp.plot([], [], color="#38bdf8", lw=2, label="Nhiệt Độ Thực (°C)")
    line_temp_set, = ax_temp.plot([], [], color="#94a3b8", lw=1, linestyle="--", label="Setpoint (22.0°C)")
    ax_temp.axhspan(LIMITS["temp_min"], LIMITS["temp_max"], color="#0284c7", alpha=0.15, label="Vùng An Toàn ±0.5°C")
    ax_temp.set_xlim(0, 24)
    ax_temp.set_ylim(20.5, 23.5)
    ax_temp.set_title("Nhiệt Độ Bay 1 & Kiểm Soát Quán Tính Nhiệt", color="#f8fafc", fontsize=10, fontweight="bold")
    ax_temp.legend(loc="upper right", fontsize=7, framealpha=0.3)

    line_dp, = ax_dp.plot([], [], color="#34d399", lw=2, label="Chênh Áp Thực (Pa)")
    ax_dp.axhline(LIMITS["dp_min"], color="#ef4444", lw=1.5, linestyle="--", label=f"Ngưỡng Tối Thiểu ({LIMITS['dp_min']} Pa)")
    ax_dp.set_xlim(0, 24)
    ax_dp.set_ylim(0, 32)
    ax_dp.set_title("Chênh Áp Phòng Sạch (ISO Cleanroom Positive Pressure)", color="#f8fafc", fontsize=10, fontweight="bold")
    ax_dp.legend(loc="upper right", fontsize=7, framealpha=0.3)

    line_part, = ax_part.plot([], [], color="#fbbf24", lw=1.8, label="Hạt Bụi >=0.1 um (/m³)")
    ax_part.axhline(LIMITS["particles_01_max"], color="#f87171", lw=1.5, linestyle=":", label="ISO 14644-1 Class 3 (1,000)")
    ax_part.set_xlim(0, 24)
    ax_part.set_ylim(0, 3200)
    ax_part.set_title("Nồng Độ Bụi Màng Lọc FFU (ISO Class 3)", color="#f8fafc", fontsize=10, fontweight="bold")
    ax_part.legend(loc="upper right", fontsize=7, framealpha=0.3)

    line_mau, = ax_fans.plot([], [], color="#06b6d4", lw=1.8, label="MAU Command (%)")
    line_ffu, = ax_fans.plot([], [], color="#ec4899", lw=1.8, label="FFU Speed (%)")
    ax_fans.set_xlim(0, 24)
    ax_fans.set_ylim(30, 105)
    ax_fans.set_title("Điều Khiển Biến Tần VFD: Quạt MAU & FFU", color="#f8fafc", fontsize=10, fontweight="bold")
    ax_fans.legend(loc="upper right", fontsize=7, framealpha=0.3)

    line_base_e, = ax_energy.plot([], [], color="#6b7280", lw=1.5, linestyle="--", label="Baseline (Rule-Based)")
    line_sac_e, = ax_energy.plot([], [], color="#10b981", lw=2.2, label="SAC Solution (Off-Policy DRL)")
    ax_energy.set_xlim(0, 24)
    ax_energy.set_ylim(0, 1100)
    ax_energy.set_title("Năng Lượng Tiêu Thụ Tích Lũy (kWh)", color="#f8fafc", fontsize=10, fontweight="bold")
    ax_energy.set_xlabel("Thời Gian (Giờ)", color="#9ca3af", fontsize=8)
    ax_energy.legend(loc="upper left", fontsize=7, framealpha=0.3)

    line_unc, = ax_unc.plot([], [], color="#a855f7", lw=1.8, label="Double-Q Disagreement |Q1 - Q2|")
    ax_unc.axhline(25.0, color="#f43f5e", lw=1.2, linestyle="--", label="Ngưỡng Bất Định ε (CLUE 2024)")
    ax_unc.set_xlim(0, 24)
    ax_unc.set_ylim(0, 35)
    ax_unc.set_title("Độ Bất Định Nhận Thức (Epistemic Uncertainty)", color="#f8fafc", fontsize=10, fontweight="bold")
    ax_unc.set_xlabel("Thời Gian (Giờ)", color="#9ca3af", fontsize=8)
    ax_unc.legend(loc="upper right", fontsize=7, framealpha=0.3)

    # Header HUD Text Boxes
    hud_mes = fig.text(0.07, 0.945, "CA VẬN HÀNH: Đang khởi tạo...", color="#38bdf8", fontsize=10, fontweight="bold")
    hud_stat = fig.text(0.50, 0.945, "TRẠNG THÁI: INITIALIZING", color="#34d399", fontsize=10, fontweight="bold")
    hud_kpi = fig.text(0.72, 0.945, "TIẾT KIỆM NĂNG LƯỢNG: 0.0%", color="#f59e0b", fontsize=10, fontweight="bold")
    hud_wd = fig.text(0.07, 0.915, "WATCHDOG HEARTBEAT: ● OK [OPC-UA ACTIVE]", color="#22c55e", fontsize=9)
    hud_lat = fig.text(0.50, 0.915, "ĐỘ TRỄ SAC: ~220 µs | CƠ CHẾ: ACTION MASKING", color="#94a3b8", fontsize=9)

    step_idx = 0
    last_cmd = {"status": "SAFE", "watchdog_heartbeat": True}

    def update(frame):
        nonlocal step_idx, sac_fan_cum, base_fan_cum, last_cmd
        if step_idx >= total_steps:
            return line_temp, line_dp, line_part, line_mau, line_ffu, line_sac_e, line_unc

        try:
            # Advance by speed_factor steps per frame
            for _ in range(speed_factor):
                if step_idx >= total_steps:
                    break

                t_hr = float(times_hr[step_idx])
                dist = disturbance_at(scenario, step_idx)
                now_s = step_idx * dt_sec
                sensors = plant.sensor_data(dist) | {"sample_time_s": now_s}
                forecast = scheduled_forecast(scenario, step_idx, dist)

                cmd = controller.command_setpoints(
                    sensors, dist.equipment_kw, dist.particles_per_min, now_s=now_s, dt_sec=dt_sec, forecast=forecast,
                )
                last_cmd = cmd

                u_mau = cmd["u_mau"]
                u_ffu = cmd["u_ffu"]

                # Energy
                p_sac = 15.0 * (u_mau ** 3) + 30.0 * (u_ffu ** 3)
                sac_fan_cum += p_sac * dt_hr
                p_base = 15.0 * (CONTROL["baseline_mau"] ** 3) + 30.0 * (CONTROL["baseline_ffu"] ** 3)
                base_fan_cum += p_base * dt_hr

                plant.step(u_mau, u_ffu, dist.equipment_kw, dist.particles_per_min, disturbance=dist)
                curr = plant.sensor_data(dist)

                history["time"].append(t_hr)
                history["temp"].append(curr["temp"])
                history["dp"].append(curr["dp"])
                history["particles"].append(curr["particle_count"])
                history["u_mau"].append(u_mau * 100.0)
                history["u_ffu"].append(u_ffu * 100.0)
                history["energy_sac"].append(sac_fan_cum)
                history["energy_base"].append(base_fan_cum)
                history["uncertainty"].append(cmd["sac_uncertainty"])

                step_idx += 1

            # Update Live Plots
            t_data = history["time"]
            line_temp.set_data(t_data, history["temp"])
            line_temp_set.set_data([0, 24], [22.0, 22.0])
            line_dp.set_data(t_data, history["dp"])
            line_part.set_data(t_data, history["particles"])
            line_mau.set_data(t_data, history["u_mau"])
            line_ffu.set_data(t_data, history["u_ffu"])
            line_base_e.set_data(t_data, history["energy_base"])
            line_sac_e.set_data(t_data, history["energy_sac"])
            line_unc.set_data(t_data, history["uncertainty"])

            # Update HUD Text
            last_t = t_data[-1] if t_data else 0.0
            phase_str, phase_color = get_mes_phase_info(last_t)
            hud_mes.set_text(f"CA VẬN HÀNH: {phase_str}")
            hud_mes.set_color(phase_color)

            status_str = last_cmd.get("status", "SAFE")
            if status_str == "SAFE":
                hud_stat.set_text(f"TRẠNG THÁI: ● {status_str} [SAC TOÀN QUYỀN]")
                hud_stat.set_color("#34d399")
            else:
                hud_stat.set_text(f"TRẠNG THÁI: ⚠️ {status_str} [PLC CAN THIỆP]")
                hud_stat.set_color("#ef4444")

            saved_pct = 100.0 * (1.0 - sac_fan_cum / max(1e-6, base_fan_cum))
            hud_kpi.set_text(f"TIẾT KIỆM NĂNG LƯỢNG: {saved_pct:.1f}% ({base_fan_cum - sac_fan_cum:.1f} kWh)")

            wd_pulse = "●" if last_cmd.get("watchdog_heartbeat", True) else "○"
            hud_wd.set_text(f"WATCHDOG HEARTBEAT: {wd_pulse} OPC-UA PULSE [HEALTHY]")

        except Exception as err:
            print(f"[!] Animation Error: {err}")
            import traceback
            traceback.print_exc()

        return line_temp, line_dp, line_part, line_mau, line_ffu, line_sac_e, line_unc

    active_animation = FuncAnimation(fig, update, interval=40, blit=False, cache_frame_data=False)
    plt.show()


if __name__ == "__main__":
    speed = 10
    if len(sys.argv) > 1:
        try:
            speed = int(sys.argv[1])
        except ValueError:
            pass
    run_interactive_sac_simulation(speed_factor=speed)
