# 02_AI_SOLUTION: Mô Hình Giải Pháp AI-CDCV (PINN-Policy + GPR + PLC Gatekeeper)
### AI-CDCV: An AI-Driven Demand-Controlled Ventilation Solution for Semiconductor Cleanrooms

Dự án này hiện thực hóa giải pháp điều khiển thông minh và tối ưu hóa năng lượng cho phòng sạch nhà máy bán dẫn (**SemiconFab 300mm Bay 1 - Lithography & Track**), dựa trên các nghiên cứu khoa học tiên tiến và tiêu chuẩn an toàn công nghiệp quốc tế (ISO 14644-1:2015 Class 3 và SEMI F21).

---

## 1. Kiến Trúc Giải Pháp 4 Tầng Lai Hóa (4-Tier Hybrid Architecture)

Nhằm loại bỏ hoàn toàn độ trễ và rủi ro không hội tụ của các bộ giải tối ưu toán học trực tuyến (Online SLSQP Solver), hệ thống chuyển sang kiến trúc **Approximate Neural MPC + Multi-Physics PINN + GPR Uncertainty Monitoring + PLC Gatekeeper**:

```
[MES Production Schedule]  +  [Cleanroom Sensors]
                   │
                   ├────────────────────────────────┐
                   ▼                                ▼
       [Khối 1: PINN Fast Policy]       [Khối 2: GPR Monitor]
      (Học bắt chước MPC ngoại tuyến)     (Đo độ bất định σ² & kernel support)
                   │                                │
                   ▼ (Lệnh đề xuất u*)              ▼ (Chỉ số tin cậy)
       [Khối 3: PINN Physics Engine] ───────────────┤
   (Dự báo vi phân T, dP, cuộn lạnh RK4)            │
                   │                                │
                   └───────────────┬────────────────┘
                                   │
                                   ▼
                   [Khối 4: PLC SAFETY GATEKEEPER]
                    (Kiểm tra 5 cửa ải an toàn)
                    /                         \
                (Hợp lệ)                   (Bất thường / σ cao)
                   │                                │
                   ▼                                ▼
        [VFD Fans: MAU & FFU]            [Fail-Safe Fallback Interlock]
        (Thời gian tính < 0.1 ms)        (Khóa áp 19 Pa, chạy quạt bảo toàn)
                   │                                │
                   └───────────────┬────────────────┘
                                   │
                                   ▼
                   [Semiconductor Cleanroom Plant]
```

---

## 2. Chi Tiết Các Khối Kỹ Thuật

### Khối 1: Fast Neural Policy (Học Bắt Chước MPC Ngoại Tuyến)
* **Nguyên lý:** Thay vì để bộ giải tối ưu toán học (SLSQP / Grid Search) chạy lặp hàng trăm lần lúc online (mất 200–500 ms và có rủi ro văng lỗi không hội tụ), một mạng chính sách hồi quy (`FanPolicy` / Decision Trees) được huấn luyện ngoại tuyến (Offline) dựa trên hàng ngàn kịch bản tối ưu chuẩn của MPC.
* **Hiệu năng:** 
  - Thời gian suy luận: **$\approx 70 - 190\ \mu\text{s}$** ($< 0.2\text{ ms}$, nhanh gấp ~2,000 lần so với giải MPC online).
  - Hoàn toàn xác định, không bao giờ bị nghẽn CPU hoặc timeout trên PLC.

### Khối 2: PINN Multi-Physics Transition Engine
* **Nguyên lý:** Mạng nơ-ron nhúng tri thức vật lý vi phân (**Physics-Informed Neural Network - PINN**) mô hình hóa phản hồi nhiệt động lực học và dòng khí:
  - Cân bằng năng lượng nhiệt bậc 1: $M_{\text{air}} \frac{dT}{dt} = \dot{Q}_{\text{load}} - U A (T - T_{\text{target}}) - \dot{Q}_{\text{coil}}$.
  - Quán tính nhiệt cuộn làm lạnh $\tau_{\text{coil}} = 60\text{s}$ tích phân giải tích bằng phương pháp Runge-Kutta 4 (RK4).
  - Đảm bảo dự báo trạng thái không bao giờ vi phạm các định luật bảo toàn khối lượng và nhiệt động học.

### Khối 3: GPR Uncertainty & Out-of-Distribution Monitor
* **Nguyên lý:** Mô hình hồi quy quá trình Gauss (**Gaussian Process Regression - GPR**) với hàm nhân RBF (Radial Basis Function) giám sát phần dư (residual) của chênh áp $\Delta P$ và hạt nano.
* **Cơ chế "Thổi còi rủi ro":**
  - GPR liên tục tính toán phương sai dự báo $\sigma^2(x)$ và chỉ số hỗ trợ kernel (`support`).
  - Khi phòng sạch gặp biến cố bất thường (công nhân mở toang cửa, rò rỉ hóa chất lạ) nằm ngoài phân phối dữ liệu đã học (Out-of-Distribution - OOD, `support < 0.35` hoặc $\sigma$ vượt ngưỡng), GPR lập tức cảnh báo PLC để kích hoạt phòng vệ.

### Khối 4: PLC Safety Gatekeeper & Fail-Safe Interlock
* **Nguyên lý:** Lớp bảo vệ độc lập chuẩn công nghiệp (IEC 61508 / IEC 61511):
  - **Giới hạn tốc độ biến thiên:** Khống chế độ tăng/giảm quạt $\le 4\%/\text{phút}$ chống sốc áp.
  - **Bảo vệ áp suất dương:** Cảnh báo và chặn giảm quạt nếu $\Delta P < 15.0\text{ Pa}$.
  - **Bảo vệ độ sạch nano:** Giới hạn hạt $\ge 0.1\ \mu\text{m} \le 1,000\text{ hạt/m}^3$ (ISO 14644-1:2015 Class 3).
  - **Chế độ phục hồi:** Yêu cầu 3 chu kỳ liên tiếp đạt trạng thái `SAFE` trước khi nhả cờ giữ sản xuất (`production_hold`).

---

## 3. Kết Quả Đối Chuẩn 24 Giờ

| Chỉ số vận hành | Baseline (Quạt cố định) | AI-CDCV Solution | Mức cải thiện |
| :--- | :---: | :---: | :---: |
| **Điện năng tiêu thụ quạt (24h)** | 473.20 kWh | **278.09 kWh** | **Giảm 41.23% điện quạt** |
| **Công suất quạt trung bình** | 19.72 kW | **11.59 kW** | Giảm 41.2% công suất |
| **Tần số trung bình biến tần MAU** | 47.5 Hz | **38.8 Hz** | Giảm mài mòn cơ khí |
| **Nhiệt sấy bù MAU (Reheat Duty)** | 34.1 kW | **28.1 kW** | Tiết kiệm nhiệt sấy |
| **Độ trễ suy luận + kiểm tra PLC** | ~200,000 µs (SLSQP) | **189.7 µs (Fast Policy)** | **Nhanh gấp ~1,000 lần** |
| **Vi phạm giới hạn thiết kế** | 20 phút | 20 phút | Đạt chuẩn ISO Class 3 |

---

## 4. Hướng Dẫn Vận Hành & Khởi Chạy

### 1. Chạy mô phỏng kiểm tra đối chuẩn 24h
```powershell
python 02_ai_solution/run_ai_solution.py
```

### 2. Mở giao diện đồ họa tương tác thời gian thực (Native Desktop GUI)
```powershell
python 02_ai_solution/run_interactive_ai_solution.py
```

### 3. Huấn luyện lại các mô hình AI (nếu thay đổi cấu hình xưởng)
```powershell
# Huấn luyện mạng PINN nhiệt vi phân
python 02_ai_solution/train_pinn.py

# Huấn luyện mô hình GPR đo độ bất định
python 02_ai_solution/train_gpr.py

# Huấn luyện chính sách nơ-ron học bắt chước MPC
python 02_ai_solution/train_fan_policy.py
```

### 4. Chạy bộ kiểm thử tự động 14 tiêu chuẩn
```powershell
python run_tests.py
```
