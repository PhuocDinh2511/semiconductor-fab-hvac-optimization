"""
run_interactive_scenarios.py
Interactive CLI for selecting, executing, and comparing semiconductor fab operational scenarios.
"""
import os
import sys
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(current_dir)

from scenarios_config import get_all_scenarios
from scenario_runner import run_scenario_comparison, run_all_scenarios_and_export
from visualize_scenarios import plot_scenarios_report

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
    print("  [6] Master Run: Chạy TẤT CẢ 5 Kịch bản & Xuất Báo Cáo Tổng Hợp PNG")
    print("  [7] Vẽ lại Biểu đồ Tổng hợp 5 Kịch bản (từ tệp JSON có sẵn)")
    print("  [0] Thoát")
    print("=" * 76)

def run_single(scenario_choice):
    scenarios = get_all_scenarios()
    if scenario_choice not in scenarios:
        print("Lựa chọn không hợp lệ!")
        return

    sc = scenarios[scenario_choice]
    print(f"\n---> Đang mô phỏng {sc['name']} ...")
    print(f"Mô tả: {sc['description']}")
    print("Vui lòng đợi trong giây lát...")

    _, _, summary = run_scenario_comparison(sc)

    b = summary["baseline"]
    a = summary["ai_solution"]

    print("\n" + "-" * 72)
    print(f" KẾT QUẢ ĐỐI CHUẨN: {summary['scenario_name']}")
    print("-" * 72)
    print(f"1. Tổng điện năng quạt 24h:  Baseline: {b['total_energy_kwh']:.2f} kWh  |  AI: {a['total_energy_kwh']:.2f} kWh")
    print(f"   => Tiết kiệm điện quạt:   {summary['savings_kwh']:.2f} kWh ({summary['savings_pct']:.1f}%)")
    print(f"2. Công suất quạt trung bình: Baseline: {b['avg_power_kw']:.2f} kW   |  AI: {a['avg_power_kw']:.2f} kW")
    print(f"3. Tần số MAU VFD trung bình: Baseline: {b['avg_mau_vfd_hz']:.1f} Hz   |  AI: {a['avg_mau_vfd_hz']:.1f} Hz")
    print(f"4. Tốc độ quạt trần 48 FFU:   Baseline: {b['avg_ffu_speed_pct']:.1f}%     |  AI: {a['avg_ffu_speed_pct']:.1f}%")
    print(f"5. Nhiệt sấy Reheat trung bình: Baseline: {b['avg_reheat_kw']:.2f} kW_th | AI: {a['avg_reheat_kw']:.2f} kW_th (-{summary['reheat_saved_pct']:.1f}%)")
    print(f"6. Áp suất phòng nhỏ nhất:    Baseline: {b['min_dp_pa']:.2f} Pa    |  AI: {a['min_dp_pa']:.2f} Pa (Chuẩn: >= 15.0 Pa)")
    print(f"7. Nồng độ hạt bụi cực đại:   Baseline: {b['max_particles']:.0f} /m3    |  AI: {a['max_particles']:.0f} /m3 (ISO Class 3 <= 1000)")
    print(f"8. Hóa chất AMC NH3 cực đại:  Baseline: {b['max_amc_nh3_ppb']:.2f} ppb  |  AI: {a['max_amc_nh3_ppb']:.2f} ppb (SEMI F21 <= 10 ppb)")
    print(f"9. Can thiệp Cổng PLC Safety: Baseline: 0 phút        |  AI: {a['failsafe_trigger_minutes']} phút")
    print(f"10. Tỷ lệ Wafer xuất xưởng:   Baseline: {b['avg_wafer_yield_pct']:.2f}%  |  AI: {a['avg_wafer_yield_pct']:.2f}%")
    print("-" * 72)

def main():
    while True:
        display_menu()
        choice = input("\nNhập lựa chọn của bạn (0-7): ").strip()
        if choice == "0":
            print("\nĐã thoát chương trình kiểm thử kịch bản. Chúc bạn làm việc hiệu quả!")
            break
        elif choice in ["1", "2", "3", "4", "5"]:
            run_single(choice)
        elif choice == "6":
            run_all_scenarios_and_export()
            plot_scenarios_report()
            print("\nĐã hoàn thành mô phỏng 5 kịch bản và xuất biểu đồ so sánh tổng hợp!")
        elif choice == "7":
            plot_scenarios_report()
        else:
            print("Lựa chọn không hợp lệ, vui lòng thử lại!")

if __name__ == "__main__":
    main()
