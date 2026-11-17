# 03_SCENARIO_TESTING: PHÂN HỆ KIỂM THỬ KỊCH BẢN VẬN HÀNH & SỰ CỐ
### Dự án: AI-CDCV – An AI-Driven Demand-Controlled Ventilation Solution for Semiconductor Cleanrooms

Thư mục này được thiết kế để kiểm thử, đối chuẩn và đánh giá độ bền vững của mô hình giải pháp **AI-CDCV** so với mô hình truyền thống:
- **`01_BASELINE`**: Vận hành quạt cố định truyền thống (MAU chạy $95\%$ định mức $47.5\text{ Hz}$, 48 quạt FFU chạy $100\%$).
- **`02_AI_SOLUTION (AI-CDCV)`**: Giải pháp thông gió theo nhu cầu phối hợp **CDCV (Coordinated Demand-Controlled Ventilation)** kết hợp **Mạng Nơ-ron Vật lý (PINN-MPC)** và **Cổng Giám sát An toàn Phần cứng (PLC Safety Filter Gatekeeper)**.

---

## 1. BẢNG ĐỐI CHIẾU 5 KỊCH BẢN VỚI CÔNG BỐ KHOA HỌC & SỰ CỐ THỰC TẾ

| Kịch bản | Tên Kịch bản & Sự cố Mô phỏng | Căn cứ Tài liệu / Nghiên cứu / Tiêu chuẩn Công nghiệp | Cơ chế Mô phỏng Chi tiết | Kết quả Tiết kiệm Điện Quạt |
| :---: | :--- | :--- | :--- | :---: |
| **Kịch bản 1** | **Vận hành Chuẩn 24 Giờ (2 Ca Ngày/Đêm)** | • Nghiên cứu **Zhuang et al. (Building & Environment, 2021)** về CDCV.<br>• Dữ liệu chuẩn hóa **TSMC Hsinchu Baseline**. | Chu trình sản xuất thực tế: ca ngày toàn tải quang khắc ($8,500\text{ m}^3/\text{h}$ xả Subfab), ca đêm chuyển chế độ chờ ($5,000\text{ m}^3/\text{h}$). | **$46.5\%$** ($220.1\text{ kWh}$) |
| **Kịch bản 2** | **Sự cố Mở Cửa Bảo Dưỡng & Sụp Đổ Áp Suất Dương** | • Nghiên cứu **Zhou et al. (Building & Environment, 2024)** về sụp đổ chênh áp.<br>• Tiêu chuẩn **ISO 14644-3** & Khóa liên động **SEMI S2**. | Cửa buồng mở 30 phút (11h30 - 12h00), xả khí tăng vọt $10,800\text{ m}^3/\text{h}$, bụi rò rỉ $+750\text{ hạt/min}$. Kèm thử nghiệm lệnh AI bất thường lúc 14h00. | **$45.9\%$** ($217.4\text{ kWh}$)<br>*(PLC can thiệp 47 phút)* |
| **Kịch bản 3** | **Sóng Nhiệt Mùa Hè Cực Hạn ($38.5^\circ\text{C}$, $90\%$ RH)** | • Nghiên cứu **Porowski & Jakubiak (Energies, 2022)**.<br>• Dữ liệu nhiệt ẩm cực hạn mùa hè Đài Loan (TSMC Peak). | Nhiệt độ môi trường tăng vọt $38.5^\circ\text{C}$, $90\%$ RH, điểm sương $26.2^\circ\text{C}$. Kiểm tra tải tách ẩm sâu (Recool) và sấy bù (Reheat) của MAU. | **$46.5\%$** ($220.1\text{ kWh}$)<br>*(Nhiệt độ $22.0 \pm 0.3^\circ\text{C}$)* |
| **Kịch bản 4** | **Đột Biến Hóa Chất AMC (Amoniac & Dung Môi Bốc Hơi)** | • Công bố thực địa **Li et al. (AAQR, 2007)** về rò rỉ khí ăn mòn và dung môi.<br>• Tiêu chuẩn **SEMI F21-95** (Giới hạn AMC $<10\text{ ppb}$). | Quá trình nướng keo Track phát tán lượng lớn hơi bazơ Amoniac $NH_3$ ($4.5\times$) và dung môi hữu cơ VOC. Thử thách màng lọc than hoạt tính FFU $95\%$. | **$46.8\%$** ($221.5\text{ kWh}$)<br>*(AMC $\le 3.5\text{ ppb}$ đạt chuẩn)* |
| **Kịch bản 5** | **Chế độ Chờ Cuối Tuần / Bảo Trì Máy Quang Khắc ASML** | • Dữ liệu thực nghiệm tần số biến tần **TSMC VFD $35\text{ Hz}$**.<br>• Kiến trúc **DeepMind Safety-First AI** (Chế độ dự phòng khi non tải). | 24h buồng sạch ở trạng thái chờ bảo trì: máy quang khắc chạy không tải ($25\text{ kW}$), xả công nghệ tối thiểu $4,800\text{ m}^3/\text{h}$. | **$54.3\%$** ($257.1\text{ kWh}$)<br>*(Mức tiết kiệm kỷ lục)* |

---

## 2. PHÂN ĐỊNH PHẠM VI: MÔ HÌNH GIẢI PHÁP GIẢI QUYẾT ĐƯỢC NHỮNG SỰ CỐ NÀO?

### A. Những sự cố MÔ HÌNH GIẢI PHÁP (AI CDCV + PLC GATEKEEPER) GIẢI QUYẾT ĐƯỢC:
1. **Sự cố Mất Áp Suất Dương & Xâm Nhập Bụi (Kịch bản 2):** 
   - *Cơ chế giải quyết:* Khi phát hiện $\Delta P < 15.8\text{ Pa}$, PLC Gatekeeper lập tức ngắt quyền kiểm soát của AI, kích hoạt **Fail-Safe Mode** đẩy quạt MAU và FFU lên $95\% - 100\%$ để bơm bù áp suất, chặn đứng nguy cơ bụi từ hành lang tràn vào buồng quang khắc.
2. **Sự cố Quá Tải Tách Ẩm & Sóng Nhiệt Ngoại Cảnh (Kịch bản 3):**
   - *Cơ chế giải quyết:* Thuật toán CDCV điều phối lưu lượng gió tươi MAU bám sát lượng xả Subfab, loại bỏ lượng gió tươi dư thừa mang hơi ẩm vào phòng, giảm mạnh phụ tải lạnh tách ẩm và triệt tiêu nhiệt sấy bù lãng phí ($89.6\%$).
3. **Sự cố Đột Biến Hóa Chất Phân Tử Bay Hơi AMC (Kịch bản 4):**
   - *Cơ chế giải quyết:* Tự động tăng tốc độ dàn quạt trần FFU để đẩy khí qua màng lọc hóa học (Chemical Filter) hiệu suất $95\%$ và tăng quạt hút xả ra Scrubber, duy trì nồng độ AMC $<10\text{ ppb}$ chuẩn SEMI F21-95.
4. **Sự cố Lỗi Cảm Biến (Sensor EMI) & Xung Đột Lệnh AI (Kịch bản 2 & Kịch bản 1):**
   - *Cơ chế giải quyết:* Bộ lọc tính toàn vẹn cảm biến của PLC tự động nhận diện giá trị bất thường (như nhiệt độ nhảy vọt ảo hoặc dP âm) và giới hạn tốc độ biến thiên ($\le 4\%/\text{phút}$), ngăn chặn mọi lệnh nguy hiểm từ thuật toán AI.

### B. Những sự cố VƯỢT NGOÀI PHẠM VI PHẦN MỀM (Cần Giải Pháp Phần Cứng Fab Chuyên Dụng):
1. **Sự cố Nhiễm Bẩn Hóa Chất Nguyên Liệu (Điển hình TSMC Fab 14B năm 2019):** 
   - Tạp chất nằm sẵn trong thùng keo cảm quang lỏng $\to$ Hệ thống HVAC khí động học không thể can thiệp. Cần trạm phân tích sắc ký khối phổ tự động (GC-MS / ICP-MS) kiểm tra nguyên liệu đầu vào.
2. **Sự cố Sụt Áp Điện Lưới / Mất Điện Fab (Điển hình Samsung Pyeongtaek 2018 - Chuẩn SEMI F47):**
   - Khi sụt áp quá $100\text{ ms}$, biến tần quạt và máy quang khắc tự động ngắt nguồn $\to$ Cần hệ thống lưu điện công nghiệp UPS và bộ phục hồi điện áp động (DVR - Dynamic Voltage Restorer).
3. **Sự cố Cháy Nổ & Rò Rỉ Độc Chất Trầm Trọng (Điển hình Renesas Naka 2021 - Chuẩn SEMI S2):**
   - Khi xảy ra cháy bể mạ/chập điện $\to$ Cần khóa liên động phần cứng ngắt khẩn cấp (Emergency Power Off - EPO), van chặn lửa (Fire dampers) tự động đóng sập cô lập buồng, và hệ thống dập lửa khí trơ Inergen.

---

## 3. HƯỚNG DẪN CHẠY KIỂM THỬ KỊCH BẢN

### Cách 1: Giao diện Dòng lệnh Tương tác (Interactive CLI - Khuyên dùng)
```powershell
python run_interactive_scenarios.py
```
Menu tương tác sẽ hiển thị cho phép bạn chọn chạy từng kịch bản hoặc chạy toàn bộ có biểu đồ động.

### Cách 2: Chạy Tự Động Toàn Bộ 5 Kịch bản & Xuất Kết Quả
```powershell
python scenario_runner.py
python visualize_scenarios.py
```

---

## 3. CÁC TỆP ĐẦU RA (OUTPUT ASSETS)

1. **`scenarios_benchmark_results.json`**: Tệp JSON lưu trữ toàn bộ chỉ số KPI chi tiết (Điện năng tiêu thụ, công suất trung bình, áp suất min, bụi max, AMC max, thời gian can thiệp PLC, tỷ lệ wafer yield) của cả 2 mô hình qua 5 kịch bản.
2. **`scenario_comparison_report.png`**: Biểu đồ so sánh đồ họa xuất bản 6 ô (Điện năng 24h, % tiết kiệm, tần số biến tần MAU VFD, nhiệt sấy bù Reheat, thời gian can thiệp PLC, và tỷ lệ Wafer hoàn hảo Murphy).
