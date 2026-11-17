# 03_SCENARIO_TESTING: PHÂN HỆ KIỂM THỬ KỊCH BẢN VẬN HÀNH PHÒNG SẠCH BÁN DẪN 300MM

Thư mục này được thiết kế để kiểm thử, đối chuẩn và đánh giá độ bền vững của 2 mô hình vận hành:
- **`01_BASELINE`**: Vận hành quạt cố định truyền thống (MAU chạy $95\%$ định mức $47.5\text{ Hz}$, 48 quạt FFU chạy $100\%$).
- **`02_AI_SOLUTION`**: Giải pháp thông gió theo nhu cầu phối hợp **CDCV (Coordinated Demand-Controlled Ventilation)** kết hợp **Mạng Nơ-ron Vật lý (PINN-MPC)** và **Cổng Giám sát An toàn Phần cứng (PLC Safety Filter Gatekeeper)**.

---

## 1. DANH SÁCH 5 KỊCH BẢN VẬN HÀNH THỰC TẾ

| Kịch bản | Tên Kịch bản Vận hành | Tình huống Thực tế Nhà máy Bán dẫn | Mục tiêu Kiểm thử & Đánh giá | Tiết kiệm Điện Quạt |
| :---: | :--- | :--- | :--- | :---: |
| **Kịch bản 1** | **Vận hành Chuẩn 24 Giờ (2 Ca Ngày/Đêm)** | Chu trình sản xuất thực tế: ca ngày toàn tải quang khắc ($8,500\text{ m}^3/\text{h}$ xả Subfab), ca đêm chuyển chế độ chờ ($5,000\text{ m}^3/\text{h}$). | Kiểm chứng thuật toán CDCV giảm lưu lượng quạt MAU về non tải ($35.7\text{ Hz}$) trong ca đêm. | **$46.5\%$** ($220.1\text{ kWh}$) |
| **Kịch bản 2** | **Sự cố Mở Cửa Bảo Dưỡng Buồng Sạch (11h30 - 12h00)** | Cửa phòng sạch bị mở trong 30 phút, gây tụt áp suất buồng sạch và làm rò rỉ hạt bụi từ hành lang ($+750\text{ hạt/min}$). | Thử thách Cổng an toàn PLC Gatekeeper: tự động đè lệnh AI đưa quạt lên $100\%$ để khôi phục áp suất và thổi sạch bụi. | **$45.9\%$** ($217.4\text{ kWh}$) |
| **Kịch bản 3** | **Sóng Nhiệt Mùa Hè Cực Hạn ($38.5^\circ\text{C}$, $90\%$ RH)** | Nhiệt độ môi trường ngoài trời tăng vọt $38.5^\circ\text{C}$ và độ ẩm $90\%$ (vượt điều kiện Hsinchu thông thường). | Kiểm tra năng lực làm lạnh sơ bộ (Precool), tách ẩm sâu (Recool) và sấy bù (Reheat) của MAU để giữ buồng ở $22.0 \pm 0.3^\circ\text{C}$. | **$46.5\%$** ($220.1\text{ kWh}$) |
| **Kịch bản 4** | **Đột Biến Hóa Chất AMC ($NH_3$ & Dung Môi Track)** | Quá trình nướng keo cảm quang phát tán lượng lớn hơi bazơ Amoniac $NH_3$ ($4.5\times$) và dung môi hữu cơ VOC ($4,500\text{ m}^3/\text{h}$). | Đánh giá hiệu suất màng lọc than hoạt tính chemical filter ($95\%$) phối hợp quạt FFU để bảo toàn chuẩn SEMI F21-95 ($<10\text{ ppb}$). | **$46.8\%$** ($221.5\text{ kWh}$) |
| **Kịch bản 5** | **Chế độ Chờ Cuối Tuần / Bảo Trì Máy ASML** | Toàn bộ 24h buồng sạch ở trạng thái chờ bảo trì: máy quang khắc chạy không tải ($25\text{ kW}$), xả công nghệ tối thiểu $4,800\text{ m}^3/\text{h}$. | Khai thác tối đa điểm non tải thực nghiệm TSMC Hsinchu ($35.0\text{ Hz}$ VFD) và FFU mức thấp ($0.32\text{ m/s}$). | **$54.3\%$** ($257.1\text{ kWh}$) |

---

## 2. HƯỚNG DẪN CHẠY KIỂM THỬ KỊCH BẢN

### Cách 1: Giao diện Dòng lệnh Tương tác (Interactive CLI - Khuyên dùng)
Mở terminal tại thư mục này và chạy:
```powershell
python run_interactive_scenarios.py
```
Menu tương tác sẽ hiện ra cho phép bạn chọn chạy từng kịch bản từ 1 đến 5 hoặc chạy toàn bộ.

### Cách 2: Chạy Tự Động Toàn Bộ 5 Kịch bản & Xuất Kết Quả
```powershell
python scenario_runner.py
python visualize_scenarios.py
```

---

## 3. CÁC TỆP ĐẦU RA (OUTPUT ASSETS)

1. **`scenarios_benchmark_results.json`**: Tệp JSON lưu trữ toàn bộ chỉ số KPI chi tiết (Điện năng tiêu thụ, công suất trung bình, áp suất min, bụi max, AMC max, thời gian can thiệp PLC, tỷ lệ wafer yield) của cả 2 mô hình qua 5 kịch bản.
2. **`scenario_comparison_report.png`**: Biểu đồ so sánh đồ họa xuất bản 6 ô (Điện năng 24h, % tiết kiệm, tần số biến tần MAU VFD, nhiệt sấy bù Reheat, thời gian can thiệp PLC, và tỷ lệ Wafer hoàn hảo Murphy).
