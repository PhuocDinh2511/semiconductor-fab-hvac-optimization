"""
run_interactive_scenarios.py
Interactive Live GUI & Benchmark Runner for 5 Semiconductor Cleanroom Scenarios.
Features real-time animated multi-physics visualizer, side-by-side Baseline vs AI CDCV,
and interactive terminal control without repetitive loops.
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

import matplotlib
# Use TkAgg for native Windows desktop interactive GUI
try:
    matplotlib.use('TkAgg')
except Exception:
    pass
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from cleanroom_model import CleanroomPlant
from baseline_controller import BaselineController
from ai_controller import AIEnergyOptimizer
from scenarios_config import get_all_scenarios
from scenario_runner import run_scenario_comparison, run_all_scenarios_and_export
from visualize_scenarios import plot_scenarios_report


def run_live_gui_scenario(scenario_data, speed_factor=12):
    """
    Launch real-time desktop GUI animated simulation for the selected scenario.
    speed_factor: simulation minutes advanced per frame (12 = smooth and fast 24h).
    """
    sc_name = scenario_data["name"]
    sc_desc = scenario_data["description"]
    times_hr = scenario_data["times_hr"]
    n_steps = len(times_hr)
    q_mes = scenario_data["q_mes"]
    particle_gen = scenario_data["particle_gen"]
    exhaust_override = scenario_data["exhaust_override"]
    outdoor_temp = scenario_data.get("outdoor_temp", np.full(n_steps, 29.93))
    outdoor_rh = scenario_data.get("outdoor_rh", np.full(n_steps, 80.0))
    amc_mult = scenario_data.get("amc_multiplier", np.ones(n_steps))
    ai_fault = scenario_data.get("ai_fault_injection", np.zeros(n_steps, dtype=bool))

    print(f"\n[+] Đang khởi tạo giao diện mô phỏng đồ họa cho: {sc_name}")
    print("    Cửa sổ đồ họa thời gian thực sẽ xuất hiện trên màn hình máy tính của bạn...")
    print("    (Đóng cửa sổ đồ họa khi xem xong để quay lại terminal)\n")

    # Plants for simultaneous execution
    plant_base = CleanroomPlant()
    plant_ai = CleanroomPlant()
    ctrl_base = BaselineController(u_mau=0.95, u_ffu=1.00)
    ctrl_ai = AIEnergyOptimizer(plant_ai)

    # Histories
    hist = {
        "time_hr": [],
        "p_base": [],
        "p_ai": [],
        "energy_base": [],
        "energy_ai": [],
        "u_mau_ai": [],
        "u_ffu_ai": [],
        "dp_base": [],
        "dp_ai": [],
        "particles_base": [],
        "particles_ai": [],
        "amc_ai": [],
        "plc_failsafe": []
    }

    cum_e_base = 0.0
    cum_e_ai = 0.0

    # Setup 4-row live comparison plot
    fig, axs = plt.subplots(4, 1, figsize=(14, 10.5))
    fig.canvas.manager.set_window_title(f"SemiconFab 300mm - {sc_name}")
    plt.subplots_adjust(hspace=0.48, top=0.92, bottom=0.06, left=0.08, right=0.92)

    fig.suptitle(f"{sc_name}\nMô phỏng Trực quan Đối chuẩn Thời gian thực: 01_Baseline (Cố định) vs 02_AI_Solution (CDCV)", fontsize=12, fontweight='bold', y=0.98)

    # 1. Panel 0: Scenario Production Disturbances
    ax_dist = axs[0]
    ax_dist_twin = ax_dist.twinx()
    line_q, = ax_dist.plot([], [], color='#e67e22', lw=2.0, label="Tải nhiệt máy Q_mes (kW)")
    line_p, = ax_dist_twin.plot([], [], color='#8e44ad', linestyle='--', lw=1.5, label="Bụi sinh ra P_gen (/min)")
    ax_dist.set_xlim(0, 24)
    ax_dist.set_ylim(0, 120)
    ax_dist_twin.set_ylim(0, 1200)
    ax_dist.set_ylabel("Nhiệt (kW)", color='#e67e22', fontweight='bold')
    ax_dist_twin.set_ylabel("Bụi (/min)", color='#8e44ad', fontweight='bold')
    ax_dist.set_title("1. Lịch Trình Tải Sản Xuất & Nhiễu Ngoại Cảnh của Kịch Bản", fontsize=10, fontweight='bold')
    ax_dist.grid(True, alpha=0.25)
    lines_0 = [line_q, line_p]
    ax_dist.legend(lines_0, [l.get_label() for l in lines_0], loc="upper right", fontsize=8)

    # 2. Panel 1: Fan Electrical Power (kW) & Energy
    ax_p = axs[1]
    line_p_base, = ax_p.plot([], [], 'r--', lw=1.6, label="Baseline Power (19.7 kW Cố định)")
    line_p_ai, = ax_p.plot([], [], 'g-', lw=2.2, label="AI CDCV Power (Điều biến theo nhu cầu)")
    ax_p.set_xlim(0, 24)
    ax_p.set_ylim(0, 24)
    ax_p.set_ylabel("Công suất (kW)", fontweight='bold')
    ax_p.set_title("2. Công Suất Tiêu Thụ Điện Quạt: Baseline vs AI CDCV", fontsize=10, fontweight='bold')
    ax_p.grid(True, alpha=0.3)
    ax_p.legend(loc="upper right", fontsize=8.5)

    # 3. Panel 2: AI Fan Speed & PLC Gatekeeper
    ax_spd = axs[2]
    line_mau_ai, = ax_spd.plot([], [], color='#2980b9', lw=2.0, label="AI MAU VFD Speed (%)")
    line_ffu_ai, = ax_spd.plot([], [], color='#16a085', lw=2.0, label="AI FFU Speed (%)")
    ax_spd.axhline(95.0, color='r', linestyle=':', label='Baseline MAU (95% - 47.5 Hz)')
    ax_spd.axhline(100.0, color='darkred', linestyle=':', label='Baseline FFU (100% Cố định)')
    ax_spd.set_xlim(0, 24)
    ax_spd.set_ylim(40, 105)
    ax_spd.set_ylabel("Tốc độ (%)", fontweight='bold')
    ax_spd.set_title("3. Tốc Độ Quạt Biến Tần VFD MAU & Lưới 48 Quạt Trần FFU", fontsize=10, fontweight='bold')
    ax_spd.grid(True, alpha=0.3)
    ax_spd.legend(loc="lower right", fontsize=8)

    # 4. Panel 3: Positive Pressure (Delta P) & Cleanliness
    ax_dp = axs[3]
    ax_c_twin = ax_dp.twinx()
    line_dp_b, = ax_dp.plot([], [], 'r--', lw=1.5, label="Baseline dP (Pa)")
    line_dp_a, = ax_dp.plot([], [], 'g-', lw=2.0, label="AI Solution dP (Pa)")
    ax_dp.axhline(15.0, color='red', linestyle='-', lw=1.8, label="Ngưỡng chuẩn an toàn ISO dP (>=15 Pa)")
    line_c_a, = ax_c_twin.plot([], [], color='#f39c12', linestyle=':', lw=1.5, label="Nồng độ hạt bụi 0.5um (/m3)")
    ax_c_twin.axhline(1000.0, color='#e74c3c', linestyle=':', lw=1.2, label="Giới hạn ISO Class 3 (1000 /m3)")
    ax_dp.set_xlim(0, 24)
    ax_dp.set_ylim(0, 45)
    ax_c_twin.set_ylim(0, 2500)
    ax_dp.set_xlabel("Thời gian vận hành (Giờ)", fontweight='bold')
    ax_dp.set_ylabel("Chênh áp dP (Pa)", fontweight='bold')
    ax_c_twin.set_ylabel("Bụi (/m3)", color='#f39c12', fontweight='bold')
    ax_dp.set_title("4. Kiểm Soát Chênh Áp Phòng Sạch & Nồng Độ Hạt Bụi ISO Class 3", fontsize=10, fontweight='bold')
    ax_dp.grid(True, alpha=0.3)
    lines_3 = [line_dp_b, line_dp_a, line_c_a]
    ax_dp.legend(lines_3, [l.get_label() for l in lines_3], loc="upper right", fontsize=8)

    # Real-time state tracker
    step_idx = [0]

    def update(frame):
        # Advance simulation by speed_factor minutes per frame
        for _ in range(speed_factor):
            i = step_idx[0]
            if i >= n_steps:
                break

            t = times_hr[i]
            plant_base.outdoor_temp = float(outdoor_temp[i])
            plant_base.outdoor_rh = float(outdoor_rh[i])
            plant_ai.outdoor_temp = float(outdoor_temp[i])
            plant_ai.outdoor_rh = float(outdoor_rh[i])

            # Baseline step
            s_base = {"temp": plant_base.temp, "rh": plant_base.rh, "dp": plant_base.dp, "particle_count": plant_base.particle_count, "amc_nh3": plant_base.amc_nh3, "mau_filter_dp": plant_base.mau_filter_dp}
            cmd_b = ctrl_base.get_setpoints(s_base, q_mes[i])
            res_b = plant_base.step(cmd_b["u_mau"], cmd_b["u_ffu"], q_mes[i], particle_gen[i], exhaust_override=exhaust_override[i], dt_sec=60.0)

            # AI step
            s_ai = {"temp": plant_ai.temp, "rh": plant_ai.rh, "dp": plant_ai.dp, "particle_count": plant_ai.particle_count, "amc_nh3": plant_ai.amc_nh3, "vibration": plant_ai.vibration, "mau_filter_dp": plant_ai.mau_filter_dp}
            cmd_a = ctrl_ai.optimize_setpoints(s_ai, q_mes[i], particle_gen[i], network_connected=not ai_fault[i])
            res_a = plant_ai.step(cmd_a["u_mau"], cmd_a["u_ffu"], q_mes[i], particle_gen[i], exhaust_override=exhaust_override[i], dt_sec=60.0)

            if amc_mult[i] > 1.0:
                plant_ai.amc_nh3 = min(40.0, plant_ai.amc_nh3 * (1.0 + 0.05 * (amc_mult[i] - 1.0)))

            dt_hr = 1.0 / 60.0
            nonlocal cum_e_base, cum_e_ai
            cum_e_base += res_b["p_total_kw"] * dt_hr
            cum_e_ai += res_a["p_total_kw"] * dt_hr

            hist["time_hr"].append(t)
            hist["p_base"].append(res_b["p_total_kw"])
            hist["p_ai"].append(res_a["p_total_kw"])
            hist["energy_base"].append(cum_e_base)
            hist["energy_ai"].append(cum_e_ai)
            hist["u_mau_ai"].append(cmd_a["u_mau"] * 100.0)
            hist["u_ffu_ai"].append(cmd_a["u_ffu"] * 100.0)
            hist["dp_base"].append(res_b["dp"])
            hist["dp_ai"].append(res_a["dp"])
            hist["particles_base"].append(res_b["particle_count"])
            hist["particles_ai"].append(res_a["particle_count"])
            hist["amc_ai"].append(res_a["amc_nh3"])
            hist["plc_failsafe"].append(cmd_a.get("status") == "FAIL_SAFE_ACTIVE")

            step_idx[0] += 1

        if len(hist["time_hr"]) > 0:
            ts = hist["time_hr"]
            line_q.set_data(ts, q_mes[:len(ts)])
            line_p.set_data(ts, particle_gen[:len(ts)])
            line_p_base.set_data(ts, hist["p_base"])
            line_p_ai.set_data(ts, hist["p_ai"])
            line_mau_ai.set_data(ts, hist["u_mau_ai"])
            line_ffu_ai.set_data(ts, hist["u_ffu_ai"])
            line_dp_b.set_data(ts, hist["dp_base"])
            line_dp_a.set_data(ts, hist["dp_ai"])
            line_c_a.set_data(ts, hist["particles_ai"])

        return line_p_base, line_p_ai

    n_frames = (n_steps // speed_factor) + 2
    ani = FuncAnimation(fig, update, frames=n_frames, interval=20, repeat=False, blit=False)
    plt.show()

    # Once window is closed, compute final summary
    print("\n" + "=" * 72)
    print(f" HOÀN TẤT MÔ PHỎNG ĐỒ HỌA: {sc_name}")
    print("=" * 72)
    saved_kwh = cum_e_base - cum_e_ai
    saved_pct = (saved_kwh / max(0.001, cum_e_base)) * 100.0
    print(f"• Tổng điện năng Baseline 24h:  {cum_e_base:.2f} kWh")
    print(f"• Tổng điện năng AI CDCV 24h:   {cum_e_ai:.2f} kWh")
    print(f"• Năng lượng quạt tiết kiệm:    {saved_kwh:.2f} kWh ({saved_pct:.1f}%)")
    print(f"• Số phút Cổng PLC can thiệp:   {sum(hist['plc_failsafe'])} phút")
    print("=" * 72)


def display_menu():
    print("\n" + "=" * 76)
    print("      HỆ THỐNG KIỂM THỬ KỊCH BẢN VẬN HÀNH PHÒNG SẠCH BÁN DẪN 300MM")
    print("      (03_SCENARIO_TESTING: 01_BASELINE vs 02_AI_SOLUTION CDCV)")
    print("=" * 76)
    print("  [1] Kịch bản 1: Vận hành Chuẩn 24 Giờ (2 Ca Ngày/Đêm Tiêu chuẩn)")
    print("  [2] Kịch bản 2: Sự cố Mở Cửa Bảo Dưỡng Buồng Sạch & Xâm Nhập Bụi (11h30)")
    print("  [3] Kịch bản 3: Sóng Nhiệt Mùa Hè Cực Hạn Hsinchu (38.5°C, 90% RH)")
    print("  [4] Kịch bản 4: Đột Biến Hóa Chất AMC (Amoniac NH3 & Dung Môi Track)")
    print("  [5] Kịch bản 5: Chế độ Chờ Cuối Tuần / Bảo Trì Máy Quang Khắc ASML (35 Hz)")
    print("  [6] Master Run: Chạy TẤT CẢ 5 Kịch bản & Tự động mở Báo cáo Tổng hợp PNG")
    print("  [7] Mở tệp Biểu đồ Báo cáo Tổng hợp PNG đã xuất")
    print("  [0] Thoát")
    print("=" * 76)


def main():
    scenarios = get_all_scenarios()
    while True:
        display_menu()
        try:
            choice = input("\nNhập lựa chọn của bạn (0-7) rồi nhấn ENTER: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nĐã thoát chương trình.")
            break

        if choice == "0":
            print("\nĐã thoát chương trình kiểm thử kịch bản. Chúc bạn một ngày làm việc hiệu quả!")
            break
        elif choice in ["1", "2", "3", "4", "5"]:
            sc = scenarios[choice]
            run_live_gui_scenario(sc)
            input("\n>>> Nhấn phím ENTER để quay lại Menu chính...")
        elif choice == "6":
            print("\n[+] Đang chạy tự động đối chuẩn toàn bộ 5 kịch bản (vui lòng đợi khoảng 1 phút)...")
            run_all_scenarios_and_export()
            out_png = plot_scenarios_report()
            print(f"\n[✓] Đã xuất xong biểu đồ tổng hợp: {out_png}")
            try:
                os.startfile(out_png)
            except Exception:
                pass
            input("\n>>> Nhấn phím ENTER để quay lại Menu chính...")
        elif choice == "7":
            png_file = os.path.join(current_dir, "scenario_comparison_report.png")
            if os.path.exists(png_file):
                print(f"\n[+] Đang mở tệp ảnh: {png_file}")
                try:
                    os.startfile(png_file)
                except Exception:
                    pass
            else:
                print("\nChưa có tệp ảnh báo cáo. Vui lòng chọn [6] để chạy trước!")
            input("\n>>> Nhấn phím ENTER để quay lại Menu chính...")
        else:
            print(f"\n[!] Bạn vừa nhập '{choice}', lựa chọn này không hợp lệ. Vui lòng nhập từ 0 đến 7!")
            input("\n>>> Nhấn phím ENTER để thử lại...")


if __name__ == "__main__":
    main()
