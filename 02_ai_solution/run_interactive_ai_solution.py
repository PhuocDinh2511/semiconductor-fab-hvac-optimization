"""
Interactive Real-Time Desktop Visualizer for AI-Driven Cleanroom Simulation
Showcases:
1. MES Production Schedule & Lithography Thermal / Particle Disturbances
2. Learned MAU and FFU setpoints from current state and MES schedule (MPC imitation policy)
3. Microsecond inference per eligible control cycle (< 0.1 ms)
4. PINN multi-physics transition checks & GPR uncertainty evaluation
5. PLC Safety Gatekeeper & Fail-Safe Fallback Interlock in Real Time
"""
import os
import sys
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from bay1_model import CleanroomPlant, CONTROL, LIMITS
from bay1_scenarios import generate_benchmark_day
from bay1_simulation import simulation_step
from ai_controller import DirectFanController

# Global reference to keep animation object alive in memory and prevent GC pausing
active_animation = None


def get_mes_phase_info(t_hr):
    """
    Returns MES lot production stage title and descriptive badge color based on simulation time.
    """
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


def run_interactive_ai_simulation(speed_factor=10):
    """
    speed_factor: Number of simulation minutes advanced per animation frame.
    Default 10 = fast, smooth 24h interactive execution.
    """
    global active_animation

    print("=" * 76)
    print("  LAUNCHING INTERACTIVE CLEANROOM AI SIMULATION (02_AI_SOLUTION)")
    print("  Fast Policy (MPC Imitation) + PINN Forecast + GPR Uncertainty + PLC Gatekeeper")
    print("=" * 76)
    print(f"-> Tốc độ mô phỏng: {speed_factor} phút/frame")
    print("-> Cửa sổ mô phỏng thời gian thực đang hiển thị trên màn hình của bạn.")
    print("-> Đóng cửa sổ đồ họa sau khi xem xong để kết thúc chương trình.\n")

    n_steps = 1440
    scenario = generate_benchmark_day(n_steps)
    times_hr, q_mes, particle_gen = (scenario[key] for key in ("times_hr", "q_mes", "particle_gen"))

    plant = CleanroomPlant()
    baseline_kw = sum(plant.compute_fan_powers(CONTROL["baseline_mau"], CONTROL["baseline_ffu"])) / 1000.0
    ai_optimizer = DirectFanController(plant)

    # Historical data tracking
    history = {
        "step": [],
        "time_hr": [],
        "q_mes": [],
        "particle_gen": [],
        "power_kw": [],
        "cum_energy_kwh": [],
        "u_mau": [],
        "u_ffu": [],
        "dp": [],
        "particles": [],
        "temp": [],
        "plc_status": [],
        "failsafe_active": []
    }

    # Setup interactive figure with 5 subplots
    fig, axs = plt.subplots(5, 1, figsize=(13, 10.5))
    fig.canvas.manager.set_window_title("AI-CDCV Cleanroom Digital Twin - Real-Time Interactive Simulation")
    plt.subplots_adjust(hspace=0.52, top=0.93, bottom=0.05, left=0.08, right=0.92)

    # Bring window to foreground
    try:
        mngr = plt.get_current_fig_manager()
        if hasattr(mngr, 'window') and hasattr(mngr.window, 'lift'):
            mngr.window.lift()
            mngr.window.attributes('-topmost', True)
            mngr.window.after_idle(mngr.window.attributes, '-topmost', False)
            mngr.window.focus_force()
    except Exception:
        pass

    # 0. MES Production Schedule & Litho Equipment Load
    ax_mes = axs[0]
    ax_mes_twin = ax_mes.twinx()

    mes_blocks = [
        (0.0, 6.0, "#f1f5f9", "Ca Đêm: Chờ"),
        (6.0, 8.0, "#fef3c7", "Giao Ca"),
        (8.0, 12.0, "#e0f2fe", "Ca Sáng: Lot A UV"),
        (12.0, 13.0, "#fef9c3", "Nghỉ Trưa"),
        (13.0, 18.0, "#f3e8ff", "Ca Chiều: Lot B DUV"),
        (18.0, 22.0, "#cffafe", "Ca Tối: Track"),
        (22.0, 24.0, "#f1f5f9", "Ca Đêm: Chờ")
    ]
    for start, end, col, lbl in mes_blocks:
        ax_mes.axvspan(start, end, color=col, alpha=0.55)
        ax_mes.text((start + end) / 2.0, 93, lbl, ha='center', va='top', fontsize=8.5, fontweight='bold', color='#475569')

    ax_mes.axvline(11.5, color='#ef4444', linestyle=':', lw=1.5)
    ax_mes.text(11.5, 30, "11:30 Cửa Mở", color='#b91c1c', fontsize=8, fontweight='bold', rotation=90, va='bottom', ha='right')
    ax_mes.axvline(16.5, color='#ea580c', linestyle=':', lw=1.5)
    ax_mes.text(16.5, 30, "16:30 Nhiễu EMI", color='#c2410c', fontsize=8, fontweight='bold', rotation=90, va='bottom', ha='right')

    line_q_mes, = ax_mes.plot([], [], color='#ea580c', lw=2.2, label="Tải nhiệt máy quang khắc Q_MES (kW)")
    line_p_gen, = ax_mes_twin.plot([], [], color='#8b5cf6', linestyle='--', lw=1.4, alpha=0.85, label="Bụi sinh ra do nhân sự P_gen (/min)")

    ax_mes.set_xlim(0, 24)
    ax_mes.set_ylim(10, 115)
    ax_mes_twin.set_ylim(0, 1000)
    ax_mes.set_ylabel("Q_MES (kW)", fontweight='bold', color='#ea580c')
    ax_mes_twin.set_ylabel("P_gen (/min)", fontweight='bold', color='#8b5cf6')
    ax_mes.set_title("0. Lịch Trình Sản Xuất MES & Tải Nhiệt Máy Quang Khắc (Litho Exposure & Track Schedule)", fontsize=10.5, fontweight='bold')
    ax_mes.grid(True, alpha=0.25)

    lines_0 = [line_q_mes, line_p_gen]
    labels_0 = [l.get_label() for l in lines_0]
    ax_mes.legend(lines_0, labels_0, loc="upper right", fontsize=8.5)

    # 1. Fan Electrical Power (kW)
    model_label = "AI trực tiếp (Học MPC) + PLC" if ai_optimizer.policy is not None else "PLC dự phòng"
    line_power, = axs[1].plot([], [], color='#16a34a', lw=2.2, label=f"{model_label} fan power")
    axs[1].axhline(baseline_kw, color='#dc2626', linestyle='--', lw=1.5, label=f"Baseline ({baseline_kw:.1f} kW)")
    axs[1].set_xlim(0, 24)
    axs[1].set_ylim(0, 24)
    axs[1].set_ylabel("Power (kW)", fontweight='bold')
    axs[1].set_title(f"1. Điện quạt mô phỏng với {model_label} và baseline", fontsize=10.5, fontweight='bold')
    axs[1].grid(True, alpha=0.3)
    axs[1].legend(loc="upper right", fontsize=8.5)

    # 2. Dynamic Setpoints & PLC Safety States
    line_mau, = axs[2].plot([], [], color='#0284c7', lw=1.8, label="Lệnh MAU vấp (VFD)")
    line_ffu, = axs[2].plot([], [], color='#7c3aed', lw=1.8, label="Lệnh FFU tốc độ gió")
    axs[2].set_xlim(0, 24)
    axs[2].set_ylim(0.50, 1.05)
    axs[2].set_ylabel("Setpoint (0.5-1.0)", fontweight='bold')
    axs[2].set_title("2. Tần Số Quạt Điều Khiển Tối Ưu Tự Động (AI Setpoints: MAU & FFU)", fontsize=10.5, fontweight='bold')
    axs[2].grid(True, alpha=0.3)
    axs[2].legend(loc="lower right", fontsize=8.5)

    # 3. Cleanroom Positive Pressure (dP)
    line_dp, = axs[3].plot([], [], color='#2563eb', lw=1.8, label="Chênh áp phòng ΔP (Pa)")
    axs[3].axhline(15.0, color='#dc2626', linestyle='--', lw=1.5, label="Ngưỡng an toàn tối thiểu (15.0 Pa)")
    axs[3].set_xlim(0, 24)
    axs[3].set_ylim(0, 32)
    axs[3].set_ylabel("ΔP (Pa)", fontweight='bold')
    axs[3].set_title("3. Chênh Áp Dương Phòng Sạch (Cleanroom Positive Differential Pressure)", fontsize=10.5, fontweight='bold')
    axs[3].grid(True, alpha=0.3)
    axs[3].legend(loc="lower right", fontsize=8.5)

    # 4. Nanoparticle Cleanliness (ISO Class 3 >= 0.1 µm)
    line_part, = axs[4].plot([], [], color='#d97706', lw=1.8, label="Bụi nano (≥0.1 µm / m³)")
    axs[4].axhline(1000.0, color='#dc2626', linestyle='--', lw=1.5, label="Giới hạn tối đa ISO Class 3 (1,000 / m³)")
    axs[4].set_xlim(0, 24)
    axs[4].set_ylim(0, 1100)
    axs[4].set_ylabel("Hạt/m³", fontweight='bold')
    axs[4].set_xlabel("Thời Gian Mô Phỏng (Giờ trong ngày)", fontweight='bold')
    axs[4].set_title("4. Nồng Độ Bụi Hạt Nano Phòng Sạch (ISO 14644-1:2015 Class 3 Compliance)", fontsize=10.5, fontweight='bold')
    axs[4].grid(True, alpha=0.3)
    axs[4].legend(loc="upper right", fontsize=8.5)

    # Status banner at top
    status_text = fig.text(
        0.5, 0.965,
        "ĐANG KHỞI CHẠY MÔ PHỎNG THỜI GIAN THỰC...",
        ha='center', va='center', fontsize=11, fontweight='bold',
        bbox=dict(boxstyle="round,pad=0.4", fc="#f8fafc", ec="#cbd5e1", lw=1.5)
    )

    time_cursors = [ax.axvline(0, color='#475569', linestyle='-', lw=1.2, alpha=0.7) for ax in axs]

    state_tracker = {
        "current_step": 0,
        "cum_energy": 0.0
    }

    def update_frame(frame):
        try:
            for _ in range(speed_factor):
                idx = state_tracker["current_step"]
                if idx >= n_steps:
                    break
                cmd, res = simulation_step(plant, ai_optimizer, scenario, idx, "ai")
                state_tracker["cum_energy"] += res["p_total_kw"] * (1.0 / 60.0)

                history["step"].append(idx)
                history["time_hr"].append(times_hr[idx])
                history["q_mes"].append(q_mes[idx])
                history["particle_gen"].append(particle_gen[idx])
                history["power_kw"].append(res["p_total_kw"])
                history["cum_energy_kwh"].append(state_tracker["cum_energy"])
                history["u_mau"].append(cmd["u_mau"])
                history["u_ffu"].append(cmd["u_ffu"])
                history["dp"].append(res["dp"])
                history["particles"].append(res["particle_count"])
                history["temp"].append(res["temp"])
                history["plc_status"].append(cmd["status"])
                history["failsafe_active"].append(cmd["production_hold"])

                state_tracker["current_step"] += 1

            if not history["time_hr"]:
                return line_q_mes, line_p_gen, line_power, line_mau, line_ffu, line_dp, line_part

            t_data = history["time_hr"]
            line_q_mes.set_data(t_data, history["q_mes"])
            line_p_gen.set_data(t_data, history["particle_gen"])
            line_power.set_data(t_data, history["power_kw"])
            line_mau.set_data(t_data, history["u_mau"])
            line_ffu.set_data(t_data, history["u_ffu"])
            axs[3].set_ylim(min(0, min(history["dp"])), max(32, max(history["dp"]) * 1.05))
            axs[4].set_ylim(0, max(1100, max(history["particles"]) * 1.05))
            line_dp.set_data(t_data, history["dp"])
            line_part.set_data(t_data, history["particles"])

            last_t = t_data[-1]
            for cur in time_cursors:
                cur.set_xdata([last_t, last_t])

            hr_int = int(last_t)
            min_int = int((last_t - hr_int) * 60)
            clock_str = f"{hr_int:02d}:{min_int:02d}"

            cur_q = history["q_mes"][-1]
            cur_p = history["power_kw"][-1]
            cur_dp = history["dp"][-1]
            cur_status = history["plc_status"][-1]
            cum_e = state_tracker["cum_energy"]

            mes_desc, _ = get_mes_phase_info(last_t)

            base_e_so_far = baseline_kw * (state_tracker["current_step"] / 60.0)
            saved_pct = ((base_e_so_far - cum_e) / max(0.1, base_e_so_far)) * 100.0

            if cur_status != "SAFE":
                status_text.set_text(
                    f"[{clock_str}] MES: {mes_desc} | ⚠️ GIỮ SẢN XUẤT (PLC Gatekeeper Fallback) | dP: {cur_dp:.1f} Pa | Tiết kiệm: {saved_pct:.1f}%"
                )
                status_text.set_backgroundcolor("#fee2e2")
                status_text.get_bbox_patch().set_edgecolor("#ef4444")
            else:
                status_text.set_text(
                    f"[{clock_str}] MES: {mes_desc} |  LỆNH ĐẠT KIỂM TRA (AI Policy + PINN + GPR) | Q_MES: {cur_q:.0f}kW | Quạt: {cur_p:.1f}kW | Tiết kiệm: {saved_pct:.1f}%"
                )
                status_text.set_backgroundcolor("#ecfdf5")
                status_text.get_bbox_patch().set_edgecolor("#10b981")

        except Exception as err:
            print(f"[!] Animation Error: {err}")
            import traceback
            traceback.print_exc()

        return line_q_mes, line_p_gen, line_power, line_mau, line_ffu, line_dp, line_part

    active_animation = FuncAnimation(fig, update_frame, interval=40, blit=False, cache_frame_data=False)
    plt.show()


if __name__ == "__main__":
    speed = 10
    if len(sys.argv) > 1:
        try:
            speed = int(sys.argv[1])
        except ValueError:
            pass
    run_interactive_ai_simulation(speed_factor=speed)
