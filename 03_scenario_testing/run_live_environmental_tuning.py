"""
run_live_environmental_tuning.py
Bảng điều khiển tương tác trực tiếp các tham số ngoại cảnh & mô phỏng thời gian thực (Live GUI Sliders).
Cho phép người dùng tự do điều chỉnh các tham số ngoại cảnh:
- Nhiệt độ ngoài trời (15°C - 42°C)
- Độ ẩm ngoài trời (40% - 98% RH)
- Lưu lượng hút xả Subfab / Cửa mở (4,500 - 11,500 m3/h)
- Phát tán hạt bụi (50 - 1,500 hạt/min)
- Đột biến hóa chất phân tử AMC (0.5x - 5.0x)
- Phụ tải nhiệt thiết bị MES (15 - 120 kW)
Xem ngay phản ứng của phòng sạch và sự can thiệp của Cổng an toàn PLC Safety Gatekeeper.
"""
import os
import sys
import numpy as np

# Force interactive TkAgg backend before importing pyplot
import matplotlib
matplotlib.use('TkAgg', force=True)
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, CheckButtons

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(os.path.join(root_dir, "01_baseline"))
sys.path.append(os.path.join(root_dir, "02_ai_solution"))
sys.path.append(current_dir)

from cleanroom_model import CleanroomPlant
from baseline_controller import BaselineController
from ai_controller import AIEnergyOptimizer


def run_simulation(outdoor_temp, outdoor_rh, exhaust_m3h, particle_rate, amc_factor, q_mes_val, sensor_glitch=False, ai_fault=False):
    """
    Run 24h simulation (1440 steps) under given ambient stress and control parameters.
    """
    n_steps = 1440
    times_hr = np.linspace(0, 24, n_steps, endpoint=False)
    
    # Baseline & AI plants
    plant_base = CleanroomPlant()
    plant_ai = CleanroomPlant()
    
    ctrl_base = BaselineController(u_mau=0.95, u_ffu=1.00)
    ctrl_ai = AIEnergyOptimizer(plant_ai)
    
    # Dynamic profile based on slider base values
    exhaust_flow_sec = exhaust_m3h / 3600.0
    
    hist_base = {"time": times_hr, "dp": [], "particles": [], "temp": [], "amc": [], "power": [], "energy": 0.0}
    hist_ai = {"time": times_hr, "dp": [], "particles": [], "temp": [], "amc": [], "power": [], "energy": 0.0, "plc_failsafe": []}
    
    failsafe_minutes = 0
    cum_e_base = 0.0
    cum_e_ai = 0.0
    
    for i, t in enumerate(times_hr):
        # Apply diurnal temperature variation around the slider outdoor_temp
        amb_t = outdoor_temp + 2.5 * np.sin((t - 6.0) * np.pi / 12.0) if 6.0 <= t <= 18.0 else outdoor_temp - 1.5
        amb_rh = outdoor_rh
        
        # Hourly production load variation scaled by q_mes_val
        load_scale = 1.0 if (8.0 <= t <= 18.0) else 0.5
        q_cur = q_mes_val * load_scale
        p_gen = particle_rate * (1.0 if 8.0 <= t <= 18.0 else 0.4)
        exh_cur = exhaust_flow_sec * (1.0 if 8.0 <= t <= 18.0 else 0.75)
        
        # Baseline execution
        res_b = plant_base.step(
            u_mau=0.95,
            u_ffu=1.00,
            q_mes_kw=q_cur,
            particle_gen_rate=p_gen,
            exhaust_override=exh_cur,
            dt_sec=60.0
        )
        cum_e_base += res_b["p_total_kw"] * (1.0 / 60.0)
        hist_base["dp"].append(res_b["dp"])
        hist_base["particles"].append(res_b["particle_count"])
        hist_base["temp"].append(res_b["temp"])
        hist_base["amc"].append(res_b["amc_nh3"])
        hist_base["power"].append(res_b["p_total_kw"])
        
        # AI execution with PLC check
        sensor_data = {
            "temp": plant_ai.temp,
            "rh": plant_ai.rh,
            "dp": plant_ai.dp,
            "particle_count": plant_ai.particle_count,
            "amc_nh3": plant_ai.amc_nh3,
            "vibration": plant_ai.vibration,
            "mau_filter_dp": plant_ai.mau_filter_dp
        }
        
        if sensor_glitch and (14.0 <= t <= 15.0):
            sensor_data["temp"] += 15.0
            sensor_data["dp"] = -5.0
            
        net_conn = not (ai_fault and (11.0 <= t <= 11.5))
        cmd = ctrl_ai.optimize_setpoints(sensor_data, q_cur, p_gen, network_connected=net_conn)
        
        res_a = plant_ai.step(
            u_mau=cmd["u_mau"],
            u_ffu=cmd["u_ffu"],
            q_mes_kw=q_cur,
            particle_gen_rate=p_gen,
            exhaust_override=exh_cur,
            dt_sec=60.0
        )
        if amc_factor > 1.0:
            plant_ai.amc_nh3 = min(40.0, plant_ai.amc_nh3 * (1.0 + 0.05 * (amc_factor - 1.0)))
            
        cum_e_ai += res_a["p_total_kw"] * (1.0 / 60.0)
        hist_ai["dp"].append(res_a["dp"])
        hist_ai["particles"].append(res_a["particle_count"])
        hist_ai["temp"].append(res_a["temp"])
        hist_ai["amc"].append(res_a["amc_nh3"])
        hist_ai["power"].append(res_a["p_total_kw"])
        
        is_fs = (cmd.get("status") == "FAIL_SAFE_ACTIVE")
        hist_ai["plc_failsafe"].append(is_fs)
        if is_fs:
            failsafe_minutes += 1
            
    hist_base["energy"] = cum_e_base
    hist_ai["energy"] = cum_e_ai
    hist_ai["failsafe_minutes"] = failsafe_minutes
    
    return hist_base, hist_ai


def create_live_tuning_app():
    # Initial default values
    init_temp = 29.93
    init_rh = 80.0
    init_exh = 8500.0
    init_particles = 480.0
    init_amc = 1.0
    init_qmes = 88.0
    
    # State flags
    flags = {"sensor_glitch": False, "ai_fault": False}
    
    # Create Figure
    fig = plt.figure(figsize=(16, 10), dpi=110)
    fig.canvas.manager.set_window_title("SemiconFab - Bảng Điều Khiển Tương Tác Tham Số Ngoại Cảnh Thời Gian Thực")
    
    # Layout: Top title, 6 telemetry plots in 2x3 grid, bottom sliders panel
    plt.subplots_adjust(left=0.07, right=0.95, top=0.92, bottom=0.34, hspace=0.38, wspace=0.22)
    
    suptitle = fig.suptitle(
        "BẢNG ĐIỀU KHIỂN & MÔ PHỎNG NGOẠI CẢNH THỜI GIAN THỰC (LIVE ENVIRONMENTAL STRESS TUNING)\n"
        "So sánh trực tiếp: 01_Baseline (Cố định 95%/100%) vs 02_AI CDCV + Cổng Giám Sát PLC Safety Gatekeeper",
        fontsize=13, fontweight='bold', y=0.97, color='#0f172a'
    )
    
    # Subplots
    ax_dp = plt.subplot(2, 3, 1)
    ax_particles = plt.subplot(2, 3, 2)
    ax_amc = plt.subplot(2, 3, 3)
    ax_temp = plt.subplot(2, 3, 4)
    ax_power = plt.subplot(2, 3, 5)
    ax_kpi = plt.subplot(2, 3, 6)
    
    # Initial Simulation
    h_b, h_a = run_simulation(init_temp, init_rh, init_exh, init_particles, init_amc, init_qmes)
    t = h_b["time"]
    
    # Plot 1: Chênh áp phòng sạch (dP)
    line_dp_b, = ax_dp.plot(t, h_b["dp"], label="01_Baseline (95%)", color="#d9534f", linestyle="--", linewidth=1.8)
    line_dp_a, = ax_dp.plot(t, h_a["dp"], label="02_AI + PLC CDCV", color="#22c55e", linewidth=2.0)
    line_dp_limit = ax_dp.axhline(15.0, color="#b91c1c", linestyle=":", linewidth=1.6, label="Ngưỡng Min ISO (15 Pa)")
    ax_dp.set_title("1. Chênh Áp Phòng Sạch (ΔP - Pa)", fontweight="bold", fontsize=10.5)
    ax_dp.set_ylabel("Áp suất (Pa)")
    ax_dp.set_ylim(0, 50)
    ax_dp.grid(True, linestyle="--", alpha=0.4)
    ax_dp.legend(loc="upper right", fontsize=7.5)
    
    # Plot 2: Nồng độ hạt bụi (Particles)
    line_p_b, = ax_particles.plot(t, h_b["particles"], label="01_Baseline", color="#d9534f", linestyle="--", linewidth=1.8)
    line_p_a, = ax_particles.plot(t, h_a["particles"], label="02_AI + PLC", color="#22c55e", linewidth=2.0)
    ax_particles.axhline(1000.0, color="#b91c1c", linestyle=":", linewidth=1.6, label="Giới hạn ISO Class 3 (1000)")
    ax_particles.set_title("2. Nồng Độ Hạt Bụi 0.5 µm (hạt/m³)", fontweight="bold", fontsize=10.5)
    ax_particles.set_ylabel("Số hạt / m³")
    ax_particles.set_ylim(0, 1500)
    ax_particles.grid(True, linestyle="--", alpha=0.4)
    ax_particles.legend(loc="upper right", fontsize=7.5)
    
    # Plot 3: Hóa chất AMC NH3
    line_amc_b, = ax_amc.plot(t, h_b["amc"], label="01_Baseline", color="#d9534f", linestyle="--", linewidth=1.8)
    line_amc_a, = ax_amc.plot(t, h_a["amc"], label="02_AI + PLC", color="#22c55e", linewidth=2.0)
    ax_amc.axhline(10.0, color="#b91c1c", linestyle=":", linewidth=1.6, label="SEMI F21 Max (10 ppb)")
    ax_amc.set_title("3. Hóa Chất AMC (NH₃ & VOC - ppb)", fontweight="bold", fontsize=10.5)
    ax_amc.set_ylabel("Nồng độ (ppb)")
    ax_amc.set_ylim(0, 16)
    ax_amc.grid(True, linestyle="--", alpha=0.4)
    ax_amc.legend(loc="upper right", fontsize=7.5)
    
    # Plot 4: Nhiệt độ phòng sạch
    line_t_b, = ax_temp.plot(t, h_b["temp"], label="01_Baseline", color="#d9534f", linestyle="--", linewidth=1.8)
    line_t_a, = ax_temp.plot(t, h_a["temp"], label="02_AI + PLC", color="#22c55e", linewidth=2.0)
    ax_temp.axhline(22.5, color="#b91c1c", linestyle=":", alpha=0.7)
    ax_temp.axhline(21.5, color="#b91c1c", linestyle=":", alpha=0.7, label="Dải nhiệt 22.0 ± 0.5°C")
    ax_temp.set_title("4. Nhiệt Độ Phòng Sạch (°C)", fontweight="bold", fontsize=10.5)
    ax_temp.set_ylabel("Nhiệt độ (°C)")
    ax_temp.set_xlabel("Thời gian trong ngày (Giờ)")
    ax_temp.set_ylim(20.5, 24.0)
    ax_temp.grid(True, linestyle="--", alpha=0.4)
    ax_temp.legend(loc="upper right", fontsize=7.5)
    
    # Plot 5: Công suất quạt (kW)
    line_pw_b, = ax_power.plot(t, h_b["power"], label="01_Baseline (19.3 kW)", color="#d9534f", linestyle="--", linewidth=1.8)
    line_pw_a, = ax_power.plot(t, h_a["power"], label="02_AI Solution", color="#22c55e", linewidth=2.0)
    ax_power.set_title("5. Công Suất Quạt Tiêu Thụ (kW)", fontweight="bold", fontsize=10.5)
    ax_power.set_ylabel("Công suất (kW)")
    ax_power.set_xlabel("Thời gian trong ngày (Giờ)")
    ax_power.set_ylim(0, 25)
    ax_power.grid(True, linestyle="--", alpha=0.4)
    ax_power.legend(loc="upper right", fontsize=7.5)
    
    # Plot 6: KPI & Trạng thái PLC
    ax_kpi.axis("off")
    kpi_card = ax_kpi.text(
        0.05, 0.95,
        "",
        verticalalignment="top",
        fontsize=9.5,
        family="monospace",
        bbox=dict(boxstyle="round,pad=0.8", facecolor="#f8fafc", edgecolor="#cbd5e1", linewidth=1.5)
    )
    
    def update_kpi_text(hb, ha):
        e_base = hb["energy"]
        e_ai = ha["energy"]
        saved_kwh = e_base - e_ai
        saved_pct = (saved_kwh / e_base) * 100.0 if e_base > 0 else 0.0
        fs_mins = ha["failsafe_minutes"]
        min_dp = np.min(ha["dp"])
        max_part = np.max(ha["particles"])
        max_amc = np.max(ha["amc"])
        
        status_text = "🟢 BÌNH THƯỜNG (AI TỐI ƯU)"
        status_color = "#15803d"
        if fs_mins > 0:
            status_text = f"🚨 PLC FAIL-SAFE KÍCH HOẠT ({fs_mins} phút)"
            status_color = "#b91c1c"
            
        text = (
            f"📊 BÁO CÁO HIỆU NĂNG 24H:\n"
            f"─────────────────────────────────────\n"
            f"• Điện Baseline:   {e_base:.1f} kWh\n"
            f"• Điện AI CDCV:    {e_ai:.1f} kWh\n"
            f"• TIẾT KIỆM:       {saved_kwh:.1f} kWh ({saved_pct:.1f}%)\n"
            f"─────────────────────────────────────\n"
            f"• Chênh áp Min ΔP: {min_dp:.2f} Pa (Chuẩn ≥15)\n"
            f"• Bụi tối đa:      {max_part:.0f} /m³ (ISO <1000)\n"
            f"• AMC tối đa:      {max_amc:.2f} ppb (SEMI <10)\n"
            f"─────────────────────────────────────\n"
            f"TRẠNG THÁI CỔNG AN TOÀN PLC:\n"
            f"► {status_text}"
        )
        kpi_card.set_text(text)
        
    update_kpi_text(h_b, h_a)
    
    # -------------------------------------------------------------
    # SLIDERS CONTROLS PANEL (Tọa độ ở dưới đáy figure)
    # -------------------------------------------------------------
    # Màu sắc thanh trượt
    slider_bg = "#f1f5f9"
    active_color = "#0284c7"
    
    ax_s_temp = plt.axes([0.10, 0.24, 0.33, 0.024], facecolor=slider_bg)
    ax_s_rh   = plt.axes([0.10, 0.19, 0.33, 0.024], facecolor=slider_bg)
    ax_s_exh  = plt.axes([0.10, 0.14, 0.33, 0.024], facecolor=slider_bg)
    
    ax_s_part = plt.axes([0.56, 0.24, 0.33, 0.024], facecolor=slider_bg)
    ax_s_amc  = plt.axes([0.56, 0.19, 0.33, 0.024], facecolor=slider_bg)
    ax_s_qmes = plt.axes([0.56, 0.14, 0.33, 0.024], facecolor=slider_bg)
    
    s_temp = Slider(ax_s_temp, "Nhiệt độ ngoài (°C)", 15.0, 42.0, valinit=init_temp, valstep=0.5, color=active_color)
    s_rh   = Slider(ax_s_rh,   "Độ ẩm ngoài (%RH)",   40.0, 98.0, valinit=init_rh,   valstep=1.0, color=active_color)
    s_exh  = Slider(ax_s_exh,  "Xả Subfab (m³/h)",    4500.0, 11500.0, valinit=init_exh, valstep=250.0, color="#ea580c")
    
    s_part = Slider(ax_s_part, "Hạt bụi sinh (hạt/m)", 50.0, 1500.0, valinit=init_particles, valstep=50.0, color="#8b5cf6")
    s_amc  = Slider(ax_s_amc,  "Đột biến AMC (x)",    0.5, 5.0, valinit=init_amc, valstep=0.25, color="#059669")
    s_qmes = Slider(ax_s_qmes, "Tải nhiệt MES (kW)",  15.0, 120.0, valinit=init_qmes, valstep=2.0, color="#d97706")
    
    # -------------------------------------------------------------
    # PRESET BUTTONS (Các kịch bản sự cố nhanh)
    # -------------------------------------------------------------
    ax_btn_door  = plt.axes([0.10, 0.05, 0.15, 0.04])
    ax_btn_heat  = plt.axes([0.27, 0.05, 0.15, 0.04])
    ax_btn_amc   = plt.axes([0.44, 0.05, 0.15, 0.04])
    ax_btn_fault = plt.axes([0.61, 0.05, 0.15, 0.04])
    ax_btn_reset = plt.axes([0.78, 0.05, 0.11, 0.04])
    
    btn_door  = Button(ax_btn_door,  "🚨 Mở Cửa Khẩn", color="#fee2e2", hovercolor="#fca5a5")
    btn_heat  = Button(ax_btn_heat,  "☀️ Sóng Nhiệt 39°C", color="#fef3c7", hovercolor="#fde68a")
    btn_amc   = Button(ax_btn_amc,   "🧪 Đột Biến AMC", color="#d1fae5", hovercolor="#a7f3d0")
    btn_fault = Button(ax_btn_fault, "⚡ Lỗi Cảm Biến EMI", color="#e0e7ff", hovercolor="#c7d2fe")
    btn_reset = Button(ax_btn_reset, "↺ Mặc Định", color="#f1f5f9", hovercolor="#e2e8f0")
    
    # -------------------------------------------------------------
    # UPDATE LOGIC
    # -------------------------------------------------------------
    def on_slider_change(val):
        t_val = s_temp.val
        rh_val = s_rh.val
        exh_val = s_exh.val
        part_val = s_part.val
        amc_val = s_amc.val
        q_val = s_qmes.val
        
        hb, ha = run_simulation(
            t_val, rh_val, exh_val, part_val, amc_val, q_val,
            sensor_glitch=flags["sensor_glitch"],
            ai_fault=flags["ai_fault"]
        )
        
        # Update lines
        line_dp_b.set_ydata(hb["dp"])
        line_dp_a.set_ydata(ha["dp"])
        
        line_p_b.set_ydata(hb["particles"])
        line_p_a.set_ydata(ha["particles"])
        
        line_amc_b.set_ydata(hb["amc"])
        line_amc_a.set_ydata(ha["amc"])
        
        line_t_b.set_ydata(hb["temp"])
        line_t_a.set_ydata(ha["temp"])
        
        line_pw_b.set_ydata(hb["power"])
        line_pw_a.set_ydata(ha["power"])
        
        update_kpi_text(hb, ha)
        fig.canvas.draw_idle()
        
    # Attach listeners
    s_temp.on_changed(on_slider_change)
    s_rh.on_changed(on_slider_change)
    s_exh.on_changed(on_slider_change)
    s_part.on_changed(on_slider_change)
    s_amc.on_changed(on_slider_change)
    s_qmes.on_changed(on_slider_change)
    
    # Button Callbacks
    def on_click_door(event):
        flags["sensor_glitch"] = False
        flags["ai_fault"] = False
        s_exh.set_val(10800.0)
        s_part.set_val(1100.0)
        
    def on_click_heat(event):
        flags["sensor_glitch"] = False
        flags["ai_fault"] = False
        s_temp.set_val(38.5)
        s_rh.set_val(92.0)
        
    def on_click_amc(event):
        flags["sensor_glitch"] = False
        flags["ai_fault"] = False
        s_amc.set_val(4.5)
        s_exh.set_val(9500.0)
        
    def on_click_fault(event):
        flags["sensor_glitch"] = not flags["sensor_glitch"]
        flags["ai_fault"] = True
        btn_fault.label.set_text("⚡ ĐÃ KÍCH HOẠT LỖI!" if flags["sensor_glitch"] else "⚡ Lỗi Cảm Biến EMI")
        on_slider_change(None)
        
    def on_click_reset(event):
        flags["sensor_glitch"] = False
        flags["ai_fault"] = False
        btn_fault.label.set_text("⚡ Lỗi Cảm Biến EMI")
        s_temp.reset()
        s_rh.reset()
        s_exh.reset()
        s_part.reset()
        s_amc.reset()
        s_qmes.reset()
        
    btn_door.on_clicked(on_click_door)
    btn_heat.on_clicked(on_click_heat)
    btn_amc.on_clicked(on_click_amc)
    btn_fault.on_clicked(on_click_fault)
    btn_reset.on_clicked(on_click_reset)
    
    print("\n" + "=" * 70)
    print(" [✓] KHỞI CHẠY BẢNG ĐIỀU KHIỂN THAM SỐ NGOẠI CẢNH THỜI GIAN THỰC (LIVE GUI)")
    print("=" * 70)
    print(" ► Cửa sổ đồ họa Matplotlib đã mở trên màn hình máy tính của bạn.")
    print(" ► Kéo các thanh trượt bên dưới để thay đổi:")
    print("   1. Nhiệt độ ngoài trời (15°C - 42°C)")
    print("   2. Độ ẩm ngoài trời (40% - 98% RH)")
    print("   3. Lưu lượng xả Subfab / Cửa mở (4,500 - 11,500 m3/h)")
    print("   4. Tốc độ phát tán hạt bụi (50 - 1500 hạt/m)")
    print("   5. Nồng độ hóa chất AMC (0.5x - 5.0x)")
    print("   6. Phụ tải thiết bị quang khắc MES (15 - 120 kW)")
    print(" ► Hoặc bấm các nút sự cố nhanh: [Mở Cửa Khẩn], [Sóng Nhiệt], [Đột Biến AMC], [Lỗi Cảm Biến]")
    print(" ► Quan sát đồ họa và trạng thái Cổng An Toàn PLC phản ứng tức thì!")
    print("=" * 70 + "\n")
    
    plt.show()

if __name__ == "__main__":
    create_live_tuning_app()
