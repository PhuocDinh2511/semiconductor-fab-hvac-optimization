# AI-CDCV: An AI-Driven Demand-Controlled Ventilation Solution for Semiconductor Cleanrooms
### Mô Hình Giải Pháp Thông Gió Theo Nhu Cầu Ứng Dụng Trí Tuệ Nhân Tạo & Cổng An Toàn PLC Cho Phòng Sạch Bán Dẫn 300mm

Dự án nghiên cứu và phát triển mô hình giải pháp điều khiển thông gió theo nhu cầu (**Coordinated Demand-Controlled Ventilation - CDCV**) kết hợp **Trí tuệ nhân tạo nhúng tri thức vật lý (PINN-MPC)** và **Cổng chốt an toàn phần cứng (Deterministic PLC Safety Gatekeeper)** cho buồng quang khắc sạch bán dẫn 300mm (Bay 1: Lithography & Track, diện tích $540\text{ m}^2$, thể tích $2,818.8\text{ m}^3$, tiêu chuẩn ISO 14644-1 Class 3), được hiệu chuẩn thực nghiệm theo dữ liệu nhà máy TSMC Hsinchu:
- **Tiêu chuẩn kiểm soát môi trường**: ISO 14644-1 Class 3 (< 1,000 hạt 0.5 µm/m³), Áp suất dương $\ge 15.0\text{ Pa}$, Nhiệt độ $22.0 \pm 0.5^\circ\text{C}$, Độ ẩm $42.5 \pm 2.5\%$.
- **Kiểm soát AMC (Airborne Molecular Contamination)**: Chuẩn SEMI F21 với màng lọc hóa học than hoạt tính ($\eta_{\text{chem}} = 95\%$), nồng độ $NH_3 \le 10\text{ ppb}$ (thực tế vận hành $\approx 0.10\text{ ppb}$).
- **Hiệu chuẩn quạt trần FFU (34-Unit Empirical Data)**: Đường đặc tính công suất thực nghiệm ($133.9\text{ W}$ rated, $1,355.6\text{ m}^3/\text{h}$ per FFU), định luật đồng dạng quạt (Fan Affinity Laws $P \propto u^3$).
- **Thông số MAU (TSMC Hsinchu Climate & Dual-Coil)**: Cụm xử lý khí tươi 2 cấp làm lạnh sơ bộ và làm lạnh sâu với nước lạnh $6^\circ\text{C}$, tổn thất áp suất lọc $1,182\text{ Pa}$.
- **Hệ thống xả Subfab phân luồng (Segregated Exhaust Streams)**: Acid Scrubber ($3,500\text{ m}^3/\text{h}$), Solvent VOC Thermal Oxidizer ($3,000\text{ m}^3/\text{h}$), General Heat ($2,000\text{ m}^3/\text{h}$).
- **Mô hình vi rung động & Murphy Wafer Yield**: Giới hạn rung VC-D $\le 1.0\text{ cm/s}^2$, mô hình Murphy tính toán tỷ lệ yield wafer nhạy cảm với hạt bụi, phân tử AMC và rung động cơ học.

---

### Cấu Trúc Thư Mục Dự Án:

```
semicon_fab_simulation/
├── 01_baseline/                   # Mô hình truyền thống (chạy quạt cố định 95% MAU / 100% FFU)
│   ├── cleanroom_model.py         # Động học vật lý, AMC, FFU hiệu chuẩn, vi rung động, wafer yield
│   ├── baseline_controller.py     # Bộ điều khiển cố định truyền thống
│   ├── run_baseline.py            # Chạy mô phỏng 24h & xuất baseline_results.png
│   ├── run_interactive_baseline.py # Giao diện tương tác trực tiếp trên Desktop
│   ├── baseline_results.png       # Đồ thị 4 kênh vận hành baseline
│   ├── baseline_kpis.json         # Chỉ số năng lượng, dP, AMC, vi rung động, wafer yield
│   └── cleanroom_visualizer.html  # Dashboard Web Digital Twin tương tác
│
├── 02_ai_solution/                # Mô hình ứng dụng giải pháp AI & Chốt an toàn PLC
│   ├── cleanroom_model.py         # Động học vật lý đồng bộ chuẩn hóa
│   ├── pinn_model.py              # Mạng nơ-ron nhúng tri thức vật lý (PINN Surrogate)
│   ├── ai_controller.py           # PINN + Tối ưu hóa phi tuyến SLSQP + Chốt an toàn PLC Gatekeeper
│   ├── run_ai_solution.py         # Chạy mô phỏng giải pháp xuất ai_results.png
│   ├── run_interactive_ai_solution.py # Giao diện tương tác trực tiếp giải pháp AI
│   ├── ai_results.png             # Đồ thị vận hành AI & kích hoạt Fail-Safe
│   ├── ai_kpis.json               # Chỉ số năng lượng, tiết kiệm điện, thời gian Fail-Safe
│   └── cleanroom_visualizer.html  # Dashboard Web Digital Twin tương tác
│
├── 03_scenario_testing/           # Phân hệ kiểm thử 5 kịch bản vận hành & sự cố thực tế
│   ├── scenarios_config.py        # Cấu hình 5 kịch bản (Chuẩn 24h, Mở cửa, Sóng nhiệt, AMC, Chế độ chờ)
│   ├── scenario_runner.py         # Bộ công cụ chạy đối chuẩn 14,400 bước MPC
│   ├── run_interactive_scenarios.py # Giao diện đồ họa động thời gian thực trên Desktop
│   ├── visualize_scenarios.py     # Xuất bảng báo cáo đối chuẩn đa chiều 6 đồ thị
│   ├── scenario_comparison_report.png # Biểu đồ tổng hợp đối chuẩn 5 kịch bản
│   ├── scenarios_benchmark_results.json # Bảng số liệu benchmark định lượng
│   └── README.md                  # Hướng dẫn chi tiết & căn cứ khoa học ISO/SEMI
│
├── compare_benchmarks.py          # Script chạy cả 2 bản và xuất báo cáo so sánh 8 khung hình
├── run_interactive_comparison.py  # Chạy 2 màn hình so sánh đối đầu trực tiếp thời gian thực
├── run_interactive_scenarios.py   # Launcher chạy trực tiếp kiểm thử kịch bản từ thư mục gốc
├── comparison_summary.png         # Đồ thị so sánh đối đầu 8 kênh toàn diện
├── benchmark_comparison.json      # Bảng dữ liệu định lượng tổng hợp
├── cleanroom_visualizer.html      # Giao diện Digital Twin Web 2D tương tác trực quan
├── semiconfab_bay1_equipment.json # Cấu hình thiết bị ASML Stepper, TEL Track, FFU lưới
└── README.md
```

---

### Kết Quả Đối Soát Định Lượng (Benchmark Summary):

| Chỉ Số Đánh Giá | 01_Baseline (Cố Định) | 02_AI Solution (Đề Xuất) | Mức Độ Cải Thiện |
| :--- | :---: | :---: | :---: |
| **Điện năng tiêu thụ 24h** | **462.91 kWh** | **280.60 kWh** | **Tiết kiệm 39.4% (182.3 kWh/ngày)** |
| **Công suất quạt trung bình** | 19.29 kW | 11.69 kW | Giảm 7.60 kW phụ tải liên tục |
| **Chênh áp phòng $\Delta P$** | Duy trì $\ge 15.0\text{ Pa}$ | Duy trì $\ge 15.0\text{ Pa}$ | Tuyệt đối an toàn theo ISO |
| **Độ sạch hạt bụi (0.5 µm)** | Đạt ISO Class 3 | Đạt ISO Class 3 | Không suy giảm chất lượng khí |
| **Nồng độ hóa học AMC $NH_3$** | 0.10 ppb (max 0.47) | 0.10 ppb (max 0.51) | Chuẩn SEMI F21 (< 10 ppb) |
| **Vi rung động cơ học** | 0.070 cm/s² | **0.051 cm/s²** | **Giảm 27% rung động lên quang khắc** |
| **Tỷ lệ Wafer Yield (Murphy)** | 99.83% | **99.71%** | Bảo toàn chất lượng xuất xưởng |
| **Kích hoạt PLC Fail-Safe** | Không có chốt | **32 phút** | 100% can thiệp khi có nhiễu |

---

### Hướng Dẫn Khởi Chạy:

1. **Chạy so sánh đối đầu trực tiếp thời gian thực (Desktop GUI):**
   ```bash
   python run_interactive_comparison.py
   ```

2. **Chạy và xuất báo cáo đối soát 8 biểu đồ chuẩn hóa:**
   ```bash
   python compare_benchmarks.py
   ```

3. **Mở giao diện Web Digital Twin:**
   * Mở file [cleanroom_visualizer.html](file:///c:/Users/admin/OneDrive/Máy tính/semicon_fab_simulation/cleanroom_visualizer.html) trên bất kỳ trình duyệt nào để trải nghiệm hoạt họa 2D dòng khí, quạt trần FFU, tầng Subfab và các đồng hồ đo thời gian thực.
