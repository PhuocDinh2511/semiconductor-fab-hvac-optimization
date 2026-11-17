"""
visualize_scenarios.py
Generate comprehensive multi-scenario visual analytics report comparing Baseline vs AI CDCV.
"""
import os
import json
import numpy as np
import matplotlib
# Only set Agg if no interactive GUI backend is active
if matplotlib.get_backend().lower() not in ['tkagg', 'qt5agg', 'qtagg', 'wxagg']:
    matplotlib.use('Agg')
import matplotlib.pyplot as plt

current_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(current_dir, "scenarios_benchmark_results.json")

def plot_scenarios_report():
    if not os.path.exists(json_path):
        print(f"Error: {json_path} does not exist. Please run scenario_runner.py first.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    sc_labels = [
        "Kịch bản 1\n(Vận hành chuẩn 24h)",
        "Kịch bản 2\n(Sự cố mở cửa buồng)",
        "Kịch bản 3\n(Sóng nhiệt mùa hè 38.5°C)",
        "Kịch bản 4\n(Đột biến hóa chất AMC)",
        "Kịch bản 5\n(Chế độ chờ cuối tuần)"
    ]

    base_energies = [data[k]["baseline"]["total_energy_kwh"] for k in ["1", "2", "3", "4", "5"]]
    ai_energies = [data[k]["ai_solution"]["total_energy_kwh"] for k in ["1", "2", "3", "4", "5"]]
    savings_pct = [data[k]["savings_pct"] for k in ["1", "2", "3", "4", "5"]]
    savings_kwh = [data[k]["savings_kwh"] for k in ["1", "2", "3", "4", "5"]]
    mau_hz_ai = [data[k]["ai_solution"]["avg_mau_vfd_hz"] for k in ["1", "2", "3", "4", "5"]]
    mau_hz_base = [data[k]["baseline"]["avg_mau_vfd_hz"] for k in ["1", "2", "3", "4", "5"]]
    failsafe_mins = [data[k]["ai_solution"]["failsafe_trigger_minutes"] for k in ["1", "2", "3", "4", "5"]]
    reheat_saved_pct = [data[k]["reheat_saved_pct"] for k in ["1", "2", "3", "4", "5"]]
    yield_ai = [data[k]["ai_solution"]["avg_wafer_yield_pct"] for k in ["1", "2", "3", "4", "5"]]

    fig, axs = plt.subplots(3, 2, figsize=(16, 14), dpi=140)
    plt.subplots_adjust(hspace=0.38, wspace=0.25, top=0.93, bottom=0.06)

    fig.suptitle("HỆ THỐNG ĐỐI CHUẨN 5 KỊCH BẢN VẬN HÀNH NHÀ MÁY BÁN DẪN ẢO\n01_BASELINE (CỐ ĐỊNH) vs 02_AI_SOLUTION (CDCV + PINN-MPC + CỔNG AN TOÀN PLC)", fontsize=14, fontweight='bold', y=0.98)

    x = np.arange(len(sc_labels))
    width = 0.35

    # 1. Total Fan Electrical Energy (kWh)
    rects1 = axs[0, 0].bar(x - width/2, base_energies, width, label='01_Baseline (Cố định)', color='#d9534f', alpha=0.85)
    rects2 = axs[0, 0].bar(x + width/2, ai_energies, width, label='02_AI Solution (CDCV)', color='#5cb85c', alpha=0.85)
    axs[0, 0].set_title("1. Điện Năng Quạt Tiêu Thụ Trong 24h (kWh)", fontweight='bold')
    axs[0, 0].set_ylabel("Điện năng (kWh)")
    axs[0, 0].set_xticks(x)
    axs[0, 0].set_xticklabels(sc_labels, fontsize=8.5)
    axs[0, 0].set_ylim(0, 560)
    axs[0, 0].grid(True, linestyle='--', alpha=0.3)
    axs[0, 0].legend(loc="upper right")
    for r in rects1:
        h = r.get_height()
        axs[0, 0].annotate(f'{h:.1f}', xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=7.5)
    for r in rects2:
        h = r.get_height()
        axs[0, 0].annotate(f'{h:.1f}', xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=7.5, fontweight='bold', color='green')

    # 2. Percentage Energy Savings (%)
    colors = ['#2e6da4', '#f0ad4e', '#5bc0de', '#9966cc', '#5cb85c']
    bars2 = axs[0, 1].bar(x, savings_pct, width=0.5, color=colors, alpha=0.85)
    axs[0, 1].set_title("2. Tỷ Lệ Tiết Kiệm Điện Năng Quạt (%)", fontweight='bold')
    axs[0, 1].set_ylabel("Tiết kiệm (%)")
    axs[0, 1].set_xticks(x)
    axs[0, 1].set_xticklabels(sc_labels, fontsize=8.5)
    axs[0, 1].set_ylim(0, 65)
    axs[0, 1].grid(True, linestyle='--', alpha=0.3)
    for r, kwh in zip(bars2, savings_kwh):
        h = r.get_height()
        axs[0, 1].annotate(f'{h:.1f}%\n(-{kwh:.0f} kWh)', xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8, fontweight='bold')

    # 3. Average MAU VFD Operating Frequency (Hz)
    rects3_1 = axs[1, 0].bar(x - width/2, mau_hz_base, width, label='Baseline (Cố định 47.5 Hz)', color='#b22222', alpha=0.8)
    rects3_2 = axs[1, 0].bar(x + width/2, mau_hz_ai, width, label='AI CDCV VFD Điều biến', color='#20b2aa', alpha=0.8)
    axs[1, 0].axhline(35.0, color='blue', linestyle=':', label='Ngưỡng non tải tối thiểu TSMC (35.0 Hz)')
    axs[1, 0].set_title("3. Tần Số Biến Tần VFD MAU Trung Bình (Hz)", fontweight='bold')
    axs[1, 0].set_ylabel("Tần số (Hz)")
    axs[1, 0].set_xticks(x)
    axs[1, 0].set_xticklabels(sc_labels, fontsize=8.5)
    axs[1, 0].set_ylim(20, 55)
    axs[1, 0].grid(True, linestyle='--', alpha=0.3)
    axs[1, 0].legend(loc="lower right", fontsize=8)
    for r in rects3_2:
        h = r.get_height()
        axs[1, 0].annotate(f'{h:.1f} Hz', xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8, fontweight='bold', color='teal')

    # 4. MAU Reheating Thermal Energy Savings (%)
    bars4 = axs[1, 1].bar(x, reheat_saved_pct, width=0.5, color='#e67e22', alpha=0.85)
    axs[1, 1].set_title("4. Tiết Kiệm Nhiệt Lượng Sấy Bù Reheat Duty (%)", fontweight='bold')
    axs[1, 1].set_ylabel("Tiết kiệm nhiệt (%)")
    axs[1, 1].set_xticks(x)
    axs[1, 1].set_xticklabels(sc_labels, fontsize=8.5)
    axs[1, 1].set_ylim(0, 30)
    axs[1, 1].grid(True, linestyle='--', alpha=0.3)
    for r in bars4:
        h = r.get_height()
        axs[1, 1].annotate(f'{h:.1f}%', xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8.5, fontweight='bold')

    # 5. PLC Safety Gatekeeper Intervention (Minutes)
    bars5 = axs[2, 0].bar(x, failsafe_mins, width=0.5, color=['#3498db', '#e74c3c', '#3498db', '#e67e22', '#2ecc71'], alpha=0.85)
    axs[2, 0].set_title("5. Thời Gian Kích Hoạt Cổng An Toàn PLC Fail-Safe (Phút)", fontweight='bold')
    axs[2, 0].set_ylabel("Thời gian can thiệp (phút)")
    axs[2, 0].set_xticks(x)
    axs[2, 0].set_xticklabels(sc_labels, fontsize=8.5)
    axs[2, 0].set_ylim(0, 60)
    axs[2, 0].grid(True, linestyle='--', alpha=0.3)
    for r in bars5:
        h = r.get_height()
        txt = f'{h} phút' if h > 0 else '0 phút\n(Hoàn hảo)'
        axs[2, 0].annotate(txt, xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8, fontweight='bold')

    # 6. Wafer Production Murphy Yield (%)
    bars6 = axs[2, 1].bar(x, yield_ai, width=0.5, color='#27ae60', alpha=0.85)
    axs[2, 1].axhline(99.5, color='r', linestyle='--', label='Ngưỡng chuẩn tối thiểu (99.50%)')
    axs[2, 1].set_title("6. Tỷ Lệ Xuất Xưởng Wafer Hoàn Hảo (Murphy Model %)", fontweight='bold')
    axs[2, 1].set_ylabel("Yield (%)")
    axs[2, 1].set_xticks(x)
    axs[2, 1].set_xticklabels(sc_labels, fontsize=8.5)
    axs[2, 1].set_ylim(99.0, 100.0)
    axs[2, 1].grid(True, linestyle='--', alpha=0.3)
    axs[2, 1].legend(loc="lower right")
    for r in bars6:
        h = r.get_height()
        axs[2, 1].annotate(f'{h:.2f}%', xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8.5, fontweight='bold')

    out_png = os.path.join(current_dir, "scenario_comparison_report.png")
    plt.savefig(out_png, bbox_inches='tight')
    plt.close()
    print(f"[OK] Master scenario comparison plot saved to: {out_png}")
    return out_png

if __name__ == "__main__":
    plot_scenarios_report()
