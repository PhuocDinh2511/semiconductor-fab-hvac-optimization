# 01_baseline: Mô Hình Phòng Sạch Vận Hành Truyền Thống

### 1. Đặc điểm vận hành
- Quạt cấp gió tươi và duy trì áp suất (MAU) chạy cố định ở mức **95%** ($14.25\text{ kW}$ rated, cung cấp gió dương).
- 48 quạt lọc trần FFU (Fan Filter Unit) chạy cố định ở mức **100%** ($133.9\text{ W}$ rated per unit từ dữ liệu thực nghiệm 34 FFU).
- Không có bộ tối ưu năng lượng AI và không thay đổi tốc độ quạt theo ca làm việc (MES).
- Tổng điện năng tiêu thụ: **462.91 kWh/ngày** (Công suất trung bình: **19.29 kW**).
- Môi trường: Đảm bảo chênh áp $\ge 15\text{ Pa}$, ISO Class 3, AMC $NH_3 \approx 0.10\text{ ppb}$, Vi rung động $0.070\text{ cm/s}^2$, Wafer yield $99.83\%$.

### 2. Cách chạy mô phỏng
```bash
# 1. Chạy xuất báo cáo và đồ thị tĩnh:
python run_baseline.py

# 2. Chạy giao diện tương tác trực tiếp trên Desktop:
python run_interactive_baseline.py
```

### 3. File đầu ra
- `baseline_results.png`: Đồ thị công suất quạt, lịch trình MES, chênh áp và thông số môi trường.
- `baseline_kpis.json`: Báo cáo định lượng tổng điện năng tiêu thụ (kWh), công suất trung bình, nồng độ AMC, vi rung động và tỷ lệ wafer yield.
- `cleanroom_visualizer.html`: Giao diện Digital Twin Web 2D tương tác trực quan.
