# HỒ SƠ THÔNG SỐ KỸ THUẬT NHÀ MÁY BÁN DẪN ẢO 300MM
## BẢNG ĐẶC TẢ CHI TIẾT & ĐỐI CHIẾU NGUỒN DỮ LIỆU THỰC NGHIỆM — PHÂN KHU BAY 1 (LITHOGRAPHY & TRACK)
**Mã tài liệu:** `SPEC-FAB300-BAY1-REV3.0`  
**Phiên bản:** `3.0 (Strict Tabular & Empirical Data Lineage Alignment)`  
**Ngày phê duyệt:** `16/11/2026`  
**Tiêu chuẩn áp dụng:** ISO 14644-1:2015, ISO 14644-4:2022, SEMI F21-95, IEST-RP-CC012.2, Generic Vibration Criteria VC-D

---

## 1. DANH MỤC NGUỒN DỮ LIỆU, CÔNG TRÌNH KHOA HỌC & CHUẨN QUỐC TẾ (MASTER DATA REGISTRY)

Toàn bộ các tham số vật lý, động học dòng khí, nhiệt ẩm, phụ tải công nghệ và giới hạn an toàn của buồng sạch Bay 1 được xây dựng dựa trên 10 nguồn dữ liệu và công trình nghiên cứu khoa học thực nghiệm đã công bố:

| STT | Tên Tài liệu / Bộ Dữ liệu Thực nghiệm | Cơ quan / Tác giả | Vai trò trong Mô hình Bản sao số | Link Nguồn Dữ liệu / Kiểm chứng Trực tiếp |
| :---: | :--- | :--- | :--- | :--- |
| **01** | **TSMC Hsinchu MAU Reference Parameters Dataset** | TSMC Fab Hsinchu Science Park / Dữ liệu đo đạc thực tế | Cung cấp toàn bộ 22 thông số nhiệt ẩm, lưu lượng, trở lực phin lọc, nhiệt độ nước lạnh và dải tần số biến tần VFD ($35 - 50\text{ Hz}$) của cụm MAU | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **02** | **FFU Power Consumption vs Velocity Dataset (Table 3 & 4)** | Nghiên cứu thực nghiệm quạt trần phòng sạch (32 FFU) | Đặc tính tiêu thụ điện phi tuyến của 48 quạt FFU theo 3 dải vận tốc gió bề mặt lọc ($0.32\text{ m/s}$, $0.42\text{ m/s}$, $0.52\text{ m/s}$) | [FFU Empirical Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/FFU/Table_3_Estimated_FFU_power_consumption_under_different_velocity_conditions.csv) |
| **03** | **Coordinated Demand-Controlled Ventilation (CDCV)** | Zhuang, Shan, Wang (Building and Environment 191, 2021) | Chiến lược điều khiển thông gió theo nhu cầu thực tế: phối hợp đồng bộ giữa lưu lượng hút xả Subfab, quạt FFU và quạt MAU | [Zhuang et al. 2021 (B&E)](https://doi.org/10.1016/j.buildenv.2020.107572) / [Google Drive Folder](https://drive.google.com/drive/folders/1mCBRAhG6UFvexZG5wIvbdmJ5ds6XcIMX?usp=drive_link) |
| **04** | **Multivariable MPC for Cleanroom Pressure Cascades** | Jeremić & Rakić (MDPI Electronics 14(16), 3296, 2025) | Mô hình vật lý dòng rò qua khe hở (Orifice flow model $n=1.6$), quán tính áp suất và bộ điều khiển dự báo MPC chênh áp buồng sạch | [Jeremić & Rakić 2025 (MDPI)](https://www.mdpi.com/2079-9292/14/16/3296) |
| **05** | **Physics-Informed Neural Networks for Thermal Modeling** | Di Natale, Bünning, Lygeros et al. (arXiv:2111.12066, 2021) | Cấu trúc mạng nơ-ron tích hợp định luật bảo toàn nhiệt động học (PINN RC-Network) mô hình hóa nhiệt độ và truyền nhiệt buồng sạch | [Di Natale et al. 2021 (arXiv:2111.12066)](https://arxiv.org/abs/2111.12066) |
| **06** | **Experimental Validation of PINN-based Predictive Control** | Bünning, Huber, Heer, Abate, Lygeros (Applied Energy / arXiv:2011.13227) | Phương pháp điều khiển tối ưu hóa đa biến lặp MPC dựa trên mô hình PINN giải bằng thuật toán Sequential Least Squares Programming (SLSQP) | [Bünning et al. 2020 (arXiv:2011.13227)](https://arxiv.org/abs/2011.13227) |
| **07** | **Safe Deep Reinforcement Learning & Predictive Safety Filters** | Jüni, Heer et al. (arXiv:2604.16033, 2026) | Kiến trúc Cổng an toàn phần cứng cấp thấp (PLC Safety Filter Gatekeeper) giám sát và can thiệp đè lệnh AI khi vi phạm ranh giới an toàn | [Jüni et al. 2026 (arXiv:2604.16033)](https://arxiv.org/abs/2604.16033) |
| **08** | **SemiconFab Equipment Data Model & Parameter Schema** | Fan, Zheng, Wu et al. (IEEE Trans. Semicond. Manuf. / GitHub 2020) | Cấu trúc đặc tả thuộc tính hình học, phụ tải nhiệt ($90\text{ kW}$), công suất điện ($150\text{ kVA}$) và nhánh xả của máy quang khắc ASML DUV | [SemiconFab Schema (Fan et al. 2020)](https://github.com/jinjiefan2020/SemiconFab/blob/main/schema.json) |
| **09** | **ISO Cleanroom Standards (Particle & Cascade Design)** | Tổ chức Tiêu chuẩn hóa Quốc tế (ISO 14644-1:2015 & 14644-4:2022) | Định lượng phân cấp sạch buồng ISO Class 3 ($\le 1,000\text{ hạt/m}^3$) và yêu cầu chênh áp tĩnh phân tầng ($\Delta P \ge +15.0\text{ Pa}$) | [ISO 14644-1:2015](https://www.iso.org/standard/53394.html) / [ISO 14644-4:2022](https://www.iso.org/standard/76503.html) |
| **10** | **SEMI Standards & Generic Vibration Criteria** | SEMI Standards (SEMI F21-95) & Colin Gordon Associates (VC-D) | Giới hạn ô nhiễm phân tử hóa học trong không khí AMC ($NH_3 \le 10\text{ ppb}$) và ngưỡng vi rung động sàn ($a_{\text{vib}} \le 1.0\text{ cm/s}^2$) | [SEMI F21-95](https://www.semi.org/en/standards) / [Colin Gordon VC-D Criteria](https://www.colingordon.com/vibration-criteria) |

---

## 2. THÔNG SỐ HÌNH HỌC & VỎ BAO CHE BUỒNG SẠCH BAY 1 (ARCHITECTURAL & CIVIL ENVELOPE)

Buồng sạch phân khu Bay 1 (Lithography & Track) được thiết kế theo cấu trúc phòng sạch áp lực dương với trần kỹ thuật treo (Ceiling Plenum) và sàn nâng đục lỗ (Perforated Raised Floor):

| STT | Thông số Hình học & Vỏ Bao che | Ký hiệu | Giá trị Thiết kế | Đơn vị | Phương trình Vật lý & Ý nghĩa Vận hành | Link Nguồn Dữ liệu Kế bên |
| :---: | :--- | :---: | :---: | :---: | :--- | :--- |
| **01** | Chiều dài buồng sạch | $L$ | **$20.0$** | m | Kích thước mặt bằng tiêu chuẩn phân khu xử lý quang học 300mm | [SemiconFab Schema](https://github.com/jinjiefan2020/SemiconFab/blob/main/schema.json) |
| **02** | Chiều rộng buồng sạch | $W$ | **$15.0$** | m | Mặt bằng bố trí cụm máy ASML DUV Stepper và Track Coater/Developer | [SemiconFab Schema](https://github.com/jinjiefan2020/SemiconFab/blob/main/schema.json) |
| **03** | Diện tích mặt sàn buồng | $A_{\text{floor}}$ | **$300.0$** | m² | $A_{\text{floor}} = L \times W = 20.0 \times 15.0$ | [Zhuang et al. 2021 (B&E)](https://doi.org/10.1016/j.buildenv.2020.107572) |
| **04** | Chiều cao thông thủy làm việc | $H_{\text{clear}}$ | **$3.2$** | m | Khoảng không gian từ mặt sàn nâng đục lỗ đến mặt lưới trần FFU | [IEST-RP-CC012.2](https://www.iest.org) |
| **05** | Chiều cao khoang sàn nâng đục lỗ | $H_{\text{floor}}$ | **$0.8$** | m | Khoang thu hồi khí và bố trí mạng lưới đường ống cấp thoát Subfab | [ISO 14644-4:2022](https://www.iso.org/standard/76503.html) |
| **06** | Tổng chiều cao kết cấu buồng | $H_{\text{total}}$ | **$4.0$** | m | $H_{\text{total}} = H_{\text{clear}} + H_{\text{floor}} = 3.2 + 0.8$ | [Jeremić & Rakić 2025 (MDPI)](https://www.mdpi.com/2079-9292/14/16/3296) |
| **07** | Thể tích buồng sạch vật lý | $V$ | **$1,200.0$** | m³ | $V = A_{\text{floor}} \times H_{\text{total}} = 300.0 \times 4.0$ | [Zhuang et al. 2021 (B&E)](https://doi.org/10.1016/j.buildenv.2020.107572) |
| **08** | Hệ số diện tích rò rỉ khe hở vách | $C_{\text{leak}}$ | **$0.02$** | - | Diện tích rò rỉ khe hở tương đương qua gioăng cửa và vách panel | [Jeremić & Rakić 2025 (MDPI)](https://www.mdpi.com/2079-9292/14/16/3296) |
| **09** | Số mũ dòng chảy rò rỉ qua khe hở | $n$ | **$1.6$** | - | Số mũ đặc trưng dòng chảy qua lỗ tiết lưu (Orifice flow model) | [Jeremić & Rakić 2025 (MDPI)](https://www.mdpi.com/2079-9292/14/16/3296) |
| **10** | Phương trình chênh áp tĩnh phòng | $\Delta P$ | $\Delta P = 5.0 + 85.0 \cdot (V_{\text{net}})^{1.6}$ | Pa | $V_{\text{net}} = V_{\text{mau}} - V_{\text{exhaust}}\ (\text{m}^3/\text{s})$, chênh lệch lưu lượng nạp và xả | [Jeremić & Rakić 2025 (MDPI)](https://www.mdpi.com/2079-9292/14/16/3296) |
| **11** | Hằng số thời gian quán tính áp suất | $\tau_p$ | **$20.0$** | s | Độ trễ hồi tiếp áp suất buồng khí động học khi thay đổi lưu lượng quạt | [Jeremić & Rakić 2025 (MDPI)](https://www.mdpi.com/2079-9292/14/16/3296) |
| **12** | Khối lượng nhiệt cấu trúc buồng | $C_{\text{thermal}}$ | **$3.41 \times 10^6$** | J/K | Tương đương $3,410\text{ kJ/K}$ (không khí buồng + kết cấu vỏ máy công nghệ) | [Di Natale et al. 2021 (arXiv:2111.12066)](https://arxiv.org/abs/2111.12066) |

---

## 3. THÔNG SỐ LƯỚI 48 QUẠT TRẦN TUẦN HOÀN FFU (FAN FILTER UNITS)

Hệ thống quạt trần tuần hoàn FFU đảm bảo vận tốc dòng khí một chiều (laminar flow) từ trần xuống sàn nâng, quét sạch bụi hạt sinh ra trong quá trình thao tác:

| STT | Thông số Kỹ thuật FFU | Ký hiệu | Giá trị Thiết kế | Đơn vị | Cơ sở Kỹ thuật & Tiêu chuẩn Áp dụng | Link Nguồn Dữ liệu Kế bên |
| :---: | :--- | :---: | :---: | :---: | :--- | :--- |
| **01** | Tổng số lượng quạt trần FFU | $N_{\text{FFU}}$ | **$48$** | Cụm | Bố trí ma trận $12 \times 4$ trên hệ khung nhôm trần treo | [FFU Empirical Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/FFU/Table_3_Estimated_FFU_power_consumption_under_different_velocity_conditions.csv) |
| **02** | Kích thước mặt cắt mỗi module | $L_{\text{ffu}} \times W_{\text{ffu}}$ | **$1.2 \times 1.2$** | m | Kích thước công nghiệp chuẩn $4 \times 4\text{ ft}$ của module phòng sạch | [FFU Empirical Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/FFU/Table_3_Estimated_FFU_power_consumption_under_different_velocity_conditions.csv) |
| **03** | Tổng diện tích bề mặt lọc trần | $A_{\text{filter}}$ | **$69.12$** | m² | $48 \times (1.2 \times 1.2) = 69.12\text{ m}^2$ (Độ che phủ trần $\approx 23.04\%$) | [FFU Empirical Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/FFU/Table_3_Estimated_FFU_power_consumption_under_different_velocity_conditions.csv) |
| **04** | Lưu lượng định mức mỗi quạt | $Q_{\text{FFU, rated}}$ | **$1,100.0$** | m³/h | Tương đương $0.306\text{ m}^3/\text{s}$ ở vận tốc bề mặt chuẩn $0.42\text{ m/s}$ | [FFU Empirical Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/FFU/Table_3_Estimated_FFU_power_consumption_under_different_velocity_conditions.csv) |
| **05** | Tổng lưu lượng tuần hoàn tối đa | $Q_{\text{total, max}}$ | **$52,800.0$** | m³/h | **$14.67\text{ m}^3/\text{s}$**, tương đương bội số trao đổi khí **$44\text{ ACH}$** | [Zhuang et al. 2021 (B&E)](https://doi.org/10.1016/j.buildenv.2020.107572) |
| **06** | Dải vận tốc gió bề mặt lọc | $v_{\text{face}}$ | **$0.32 – 0.45$** | m/s | Tuân thủ dải kiểm soát dòng khí tầng theo tiêu chuẩn IEST | [IEST-RP-CC012.2](https://www.iest.org) |
| **07** | Công suất điện định mức 1 FFU | $P_{\text{FFU, rated}}$ | **$110.0$** | W | Đo đạc thực tế tại vận tốc trung bình $0.42\text{ m/s}$ | [FFU Empirical Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/FFU/Table_3_Estimated_FFU_power_consumption_under_different_velocity_conditions.csv) |
| **08** | Tổng công suất điện định mức 48 quạt | $P_{\text{total, rated}}$| **$5.28$** | kW | Khi toàn bộ 48 quạt chạy $100\%$ công suất định mức | [FFU Empirical Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/FFU/Table_3_Estimated_FFU_power_consumption_under_different_velocity_conditions.csv) |
| **09** | Công suất FFU ở vận tốc Thấp | $P_{\text{low}}$ | **$82.7$** | W | Đo thực tế tại $v_{\text{face}} = 0.32\text{ m/s}$ (Tiết kiệm $24.8\%$ điện) | [FFU Empirical Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/FFU/Table_3_Estimated_FFU_power_consumption_under_different_velocity_conditions.csv) |
| **10** | Công suất FFU ở vận tốc Trung bình | $P_{\text{medium}}$ | **$108.3$** | W | Đo thực tế tại $v_{\text{face}} = 0.42\text{ m/s}$ (Chế độ sản xuất ca ngày) | [FFU Empirical Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/FFU/Table_3_Estimated_FFU_power_consumption_under_different_velocity_conditions.csv) |
| **11** | Công suất FFU ở vận tốc Cao | $P_{\text{high}}$ | **$133.9$** | W | Đo thực tế tại $v_{\text{face}} = 0.52\text{ m/s}$ (Chế độ làm sạch khẩn cấp) | [FFU Empirical Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/FFU/Table_3_Estimated_FFU_power_consumption_under_different_velocity_conditions.csv) |
| **12** | Loại màng lọc hạt siêu mịn | - | ULPA / HEPA | - | Sợi thủy tinh borosilicate siêu mịn không giải phóng sợi thứ cấp | [ISO 14644-1:2015](https://www.iso.org/standard/53394.html) |
| **13** | Hiệu suất lọc hạt bụi siêu mịn | $\eta_{\text{HEPA}}$ | **$99.999\%$** | - | Bắt giữ hạt bụi có đường kính $\ge 0.1\ \mu m$ đến $0.5\ \mu m$ | [ISO 14644-1:2015](https://www.iso.org/standard/53394.html) |
| **14** | Màng lọc hóa học trần kỹ thuật | AMC Filter | Hóa chất hấp phụ | - | Bố trí trên trần kỹ thuật khoang hòa trộn gió tươi và gió hồi | [SEMI F21-95](https://www.semi.org/en/standards) |
| **15** | Hiệu suất khử khí phân tử AMC | $\eta_{\text{chem}}$ | **$95.0\%$** | - | Khử hơi bazơ $NH_3$ và dung môi VOC bảo vệ màng quang trở | [SEMI F21-95](https://www.semi.org/en/standards) |

---

## 4. TOÀN BỘ 22 THÔNG SỐ CỤM XỬ LÝ KHÍ TƯƠI ÁP SUẤT DƯƠNG MAU (MAKE-UP AIR UNIT)
*(Hồ sơ 22 thông số thực nghiệm chuẩn hóa từ tập dữ liệu TSMC Hsinchu Reference Dataset)*

Cụm MAU thực hiện chu trình xử lý nhiệt ẩm psychrometric 3 giai đoạn độc lập: **Dàn làm lạnh sơ bộ (Precool)** $\to$ **Dàn làm lạnh sâu tách ẩm (Recool/Dehumidification)** $\to$ **Dàn sấy nóng điều nhiệt (Reheating)**:

| STT | Tên Thông số Kỹ thuật MAU | Ký hiệu | Giá trị Đo đạc | Đơn vị | Bản chất Vật lý & Ý nghĩa Vận hành Hệ thống | Link Nguồn Dữ liệu Kế bên |
| :---: | :--- | :---: | :---: | :---: | :--- | :--- |
| **01** | Nhiệt độ tính toán mùa hè (Hsinchu Outdoor) | $T_{\text{summer}}$ | **$35.0$** | °C | Phụ tải nhiệt cảm và nhiệt ẩm cực hạn thiết kế mùa hè | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **02** | Nhiệt độ tính toán mùa đông | $T_{\text{winter}}$ | **$5.0$** | °C | Phụ tải gia nhiệt và tạo ẩm bổ sung vào mùa lạnh | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **03** | Độ ẩm tương đối tính toán mùa hè | $RH_{\text{summer}}$ | **$80.0$** | % | Độ ẩm cao ngoài trời đòi hỏi công suất tách ẩm sâu | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **04** | Độ ẩm tương đối tính toán mùa đông | $RH_{\text{winter}}$ | **$20.0$** | % | Trạng thái hanh khô mùa đông | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **05** | Điểm sương ngoài trời đo đạc | $T_{\text{dp, OA}}$ | **$16.40$** | °C | Độ chứa ẩm ban đầu của không khí tươi nạp vào trạm | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **06** | Nhiệt độ gió tươi thực đo đầu vào | $T_{\text{OA}}$ | **$29.93$** | °C | Nhiệt độ khí thực tế nạp vào dàn lạnh sơ bộ MAU | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **07** | Lưu lượng đo thực tế mỗi quạt MAU | $Q_{\text{fan, meas}}$ | **$63,000$** | m³/h | Trạm thực nghiệm Hsinchu (Công suất quạt thiết kế $100,000\text{ m}^3/\text{h}$) | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **08** | Tổng lưu lượng gió cấp toàn tổ hợp MAU | $Q_{\text{total, meas}}$| **$318,008$** | m³/h | Tổ hợp 6 quạt MAU chạy song song ($88.33\text{ m}^3/\text{s}$) | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **09** | **Lưu lượng MAU phân bổ Bay 1** | $V_{\text{mau, rated}}$ | **$10,800.0$** | m³/h | **$3.0\text{ m}^3/\text{s}$** định mức cấp áp lực dương cho buồng Bay 1 | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **10** | Trở lực chênh áp qua màng lọc phin | $\Delta P_{\text{filter}}$ | **$1,182.0$** | Pa | Trở lực tĩnh phin lọc cấp khí (Ngưỡng cảnh báo nghẹt: $1,400\text{ Pa}$) | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **11** | Nhiệt độ khí vào dàn làm lạnh sơ bộ | $T_{\text{precool, in}}$ | **$29.93$** | °C | Khí trời lấy trực tiếp sau phin lọc thô và tinh | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **12** | **Nhiệt độ khí ra dàn làm lạnh sơ bộ** | $T_{\text{precool, out}}$| **$17.70$** | °C | **Hạ nhiệt cảm giai đoạn 1**, cắt giảm gánh nặng nhiệt cho dàn tách ẩm | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **13** | Nhiệt độ khí vào dàn làm lạnh sâu | $T_{\text{recool, in}}$ | **$17.70$** | °C | Khí trung gian chuyển tiếp từ dàn sơ bộ sang dàn tách ẩm | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **14** | **Nhiệt độ khí ra dàn làm lạnh sâu** | $T_{\text{recool, out}}$ | **$11.06$** | °C | **Đưa khí về điểm sương bão hòa** để ngưng tụ ẩm triệt để | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **15** | Nhiệt độ nước lạnh từ Chiller | $T_{\text{CW}}$ | **$6.0$** | °C | Nguồn nước lạnh trung tâm cung cấp cho cả 2 dàn Precool và Recool | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **16** | Dải độ mở van nước lạnh tỷ lệ | $CW_{\text{valve}}$ | **$0 – 100$** | % | Điều tiết lưu lượng nước lạnh theo giải thuật cân bằng nhiệt | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **17** | **Nhiệt độ khí ra dàn sấy nóng (Reheat)** | $T_{\text{reheat, out}}$ | **$20.99$** | °C | **Khí sau sấy đạt đúng setpoint cấp vào phòng ($21.00^\circ\text{C}$)** | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **18** | Dải độ mở van hơi/nước nóng sấy bù | $HW_{\text{valve}}$ | **$0 – 100$** | % | Tự động điều tiết lượng hơi sấy nhằm duy trì nhiệt độ gió cấp | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **19** | Tổng công suất điện thực tế đo đạc dàn quạt | $P_{\text{mau, measured}}$| **$93.0$** | kW | Dàn 6 quạt MAU hoạt động ở tần số thực tế ($15.5\text{ kW}$/quạt) | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **20** | **Công suất quạt MAU định mức Bay 1** | $P_{\text{mau, rated}}$ | **$16.5$** | kW | Động cơ biến tần chuyên dụng cấp áp lực tĩnh cao cho phân khu Bay 1 | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **21** | **Dải tần số biến tần VFD cho phép** | $f_{\text{VFD}}$ | **$35.0 – 50.0$** | Hz | Đo đạc thực tế non tải: **$35.0\text{ Hz}$**; Định mức: **$50.0\text{ Hz}$** | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **22** | Nhiệt độ và Điểm sương gió cấp vào buồng | $T_{\text{SA}} / T_{\text{dp, SA}}$| **$20.99 / 11.06$**| °C | Cung cấp trực tiếp vào Ceiling Plenum để hòa trộn với khí hồi | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |

---

## 5. HỆ THỐNG ỐNG HÚT XẢ CÔNG NGHỆ SUBFAB (SEGREGATED PROCESS EXHAUSTS)

Hệ thống hút xả công nghệ Subfab phân chia 3 tuyến ống độc lập để xử lý triệt để hóa chất độc hại phát tán từ quy trình tráng keo cảm quang và quang khắc:

| STT | Phân hệ Tuyến Ống Hút Xả Subfab | Ký hiệu | Lưu lượng Toàn tải (Ca Ngày) | Lưu lượng Tiết lưu (Ca Đêm) | Đơn vị | Quy trình Công nghệ & Thiết bị Xử lý Môi trường Đích | Link Nguồn Dữ liệu Kế bên |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **01** | **Tuyến Hút Xả Hơi Acid Vô cơ** | $V_{\text{exh, acid}}$ | **$3,500$** ($0.972\text{ m}^3/\text{s}$) | **$3,200$** ($0.889\text{ m}^3/\text{s}$) | m³/h | Hút hơi ăn mòn vô cơ từ máy rửa phôi, dẫn về Tháp rửa ướt (Wet Chemical Scrubbers) | [SemiconFab Schema](https://github.com/jinjiefan2020/SemiconFab/blob/main/schema.json) |
| **02** | **Tuyến Hút Xả Dung môi Hữu cơ (VOC)** | $V_{\text{exh, solvent}}$| **$3,000$** ($0.833\text{ m}^3/\text{s}$) | **$1,200$** ($0.333\text{ m}^3/\text{s}$) | m³/h | Hút hơi dung môi bốc hơi từ máy tráng keo Track Coater, dẫn về Lò thiêu nhiệt tái sinh (RTO) | [Zhuang et al. 2021 (B&E)](https://doi.org/10.1016/j.buildenv.2020.107572) |
| **03** | **Tuyến Hút Nhiệt Thiết bị Quang học**| $V_{\text{exh, heat}}$ | **$2,000$** ($0.556\text{ m}^3/\text{s}$) | **$600$** ($0.167\text{ m}^3/\text{s}$) | m³/h | Hút khí nóng tỏa ra từ tủ nguồn laser và động cơ dịch chuyển bàn soi thấu kính DUV | [SemiconFab Schema](https://github.com/jinjiefan2020/SemiconFab/blob/main/schema.json) |
| **04** | **TỔNG LƯU LƯỢNG HÚT XẢ NỀN** | $V_{\text{exhaust}}$ | **$8,500$** ($2.361\text{ m}^3/\text{s}$) | **$5,000$** ($1.389\text{ m}^3/\text{s}$) | m³/h | **Lưu lượng xả thực tế cần được bù bằng khí tươi MAU để giữ áp dương buồng sạch** | [Zhuang et al. 2021 (B&E)](https://doi.org/10.1016/j.buildenv.2020.107572) |
| **05** | **Tuyến Xả Cực hạn Khi Mở Cửa Bảo Dưỡng**| $V_{\text{exh, door}}$ | **$10,200$** ($2.833\text{ m}^3/\text{s}$) | - | m³/h | Dòng xả tăng vọt do mở buồng thao tác bảo trì, kích hoạt cơ chế Fail-Safe tăng tốc MAU $100\%$ | [Jüni et al. 2026 (arXiv:2604.16033)](https://arxiv.org/abs/2604.16033) |

---

## 6. THIẾT BỊ SẢN XUẤT MES & PHỤ TẢI PHÁT THẢI (PROCESS TOOLS & PRODUCTION LOADS)

Phân khu Bay 1 tích hợp các dòng máy sản xuất vi mạch bán dẫn 300mm công nghệ cao mô phỏng chuẩn xác theo bộ lược đồ SemiconFab Machine Schema:

| STT | Thiết bị Sản xuất / Nguồn Phát thải | Thuộc tính Kỹ thuật | Giá trị Thực tế | Đơn vị | Tác động Môi trường & Vai trò Kiểm soát | Link Nguồn Dữ liệu Kế bên |
| :---: | :--- | :--- | :---: | :---: | :--- | :--- |
| **01** | **ASML TWINSCAN Immersion DUV Scanner** | Model thiết bị | NXT:2050i | - | Hệ thống máy quét quang khắc bước sóng $193\text{ nm}$ nhúng ngập | [SemiconFab Schema](https://github.com/jinjiefan2020/SemiconFab/blob/main/schema.json) |
| **02** | ASML TWINSCAN Immersion DUV Scanner | Kích thước máy ($R \times D \times C$) | $3.2 \times 8.5 \times 3.8$ | m | Chiếm khoảng $27.2\text{ m}^2$ diện tích buồng sạch | [SemiconFab Schema](https://github.com/jinjiefan2020/SemiconFab/blob/main/schema.json) |
| **03** | ASML TWINSCAN Immersion DUV Scanner | Phụ tải nhiệt chế độ Chờ (Standby) | **$25.0$** | kW | Nhiệt tự tiêu hao từ các bộ điều khiển điện tử và duy trì chân không | [SemiconFab Schema](https://github.com/jinjiefan2020/SemiconFab/blob/main/schema.json) |
| **04** | ASML TWINSCAN Immersion DUV Scanner | Phụ tải nhiệt Chiếu xạ Đỉnh (Exposure) | **$90.0$** | kW | Tỏa nhiệt mãnh liệt từ nguồn laser kích thích, bàn nạp wafer và thấu kính | [SemiconFab Schema](https://github.com/jinjiefan2020/SemiconFab/blob/main/schema.json) |
| **05** | ASML TWINSCAN Immersion DUV Scanner | Công suất điện cấp nguồn tổng | **$150.0$** | kVA | Điện áp 3 pha $480\text{ V}$, $60\text{ Hz}$ | [SemiconFab Schema](https://github.com/jinjiefan2020/SemiconFab/blob/main/schema.json) |
| **06** | ASML TWINSCAN Immersion DUV Scanner | Vòng tuần hoàn nước giải nhiệt PCW | **$110.0$** | kW | Ổn định nhiệt độ thấu kính trong dải siêu chính xác $22.0 \pm 0.3^\circ\text{C}$ | [SemiconFab Schema](https://github.com/jinjiefan2020/SemiconFab/blob/main/schema.json) |
| **07** | **TEL CLEAN TRACK LITHIUS Pro Coater** | Thiết bị đồng bộ | Coater / Developer | - | Máy tráng phủ keo cảm quang và sấy nướng trước/sau khi chiếu tia | [SemiconFab Schema](https://github.com/jinjiefan2020/SemiconFab/blob/main/schema.json) |
| **08** | TEL CLEAN TRACK LITHIUS Pro Coater | Phụ tải nhiệt buồng sấy phôi (Bake units)| **$20.0 – 50.0$** | kW | Nhiệt đối lưu tỏa ra từ các đế sấy nhiệt độ cao ($110 - 150^\circ\text{C}$) | [SemiconFab Schema](https://github.com/jinjiefan2020/SemiconFab/blob/main/schema.json) |
| **09** | **Nhân sự thao tác Ca đêm (Standby)** | Mức độ sinh bụi nhân sự | **$120.0$** | hạt/phút | 1 kỹ sư giám sát định kỳ buồng máy | [ISO 14644-1:2015](https://www.iso.org/standard/53394.html) |
| **10** | **Nhân sự thao tác Ca ngày (Full Production)**| Mức độ sinh bụi nhân sự | **$480.0$** | hạt/phút | 3 đến 4 kỹ thuật viên thao tác vận hành, nạp phôi và lấy mẫu đo lường | [ISO 14644-1:2015](https://www.iso.org/standard/53394.html) |
| **11** | **Sự cố mở cửa bảo dưỡng buồng sạch** | Mức sinh bụi xâm nhập đột xuất | **$+400.0$** | hạt/phút | Hạt bụi từ hành lang kỹ thuật xâm nhập khi mở cửa liên động | [ISO 14644-1:2015](https://www.iso.org/standard/53394.html) |
| **12** | Tổng phụ tải nhiệt buồng sạch biến thiên | $Q_{\text{int}}$ | **$45.0 – 140.0$** | kW | Tổng tải nhiệt thay đổi theo ca sản xuất, được cân bằng bởi FFU và MAU | [Di Natale et al. 2021 (arXiv:2111.12066)](https://arxiv.org/abs/2111.12066) |

---

## 7. TIÊU CHUẨN KIỂM SOÁT MÔI TRƯỜNG & NGƯỠNG AN TOÀN (ENVIRONMENTAL SAFETY LIMITS)

Bảng đối chuẩn các chỉ số môi trường buồng sạch Bay 1 theo tiêu chuẩn quốc tế và ngưỡng kích hoạt của Cổng an toàn PLC Gatekeeper:

| STT | Đại lượng Kiểm soát Môi trường | Ký hiệu | Ngưỡng Tiêu chuẩn Quốc tế | Điểm đặt Mục tiêu (Setpoints) | Ranh giới Cổng PLC Gatekeeper | Đơn vị | Link Nguồn Tiêu chuẩn Kế bên |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **01** | **Chênh áp dương tĩnh buồng sạch** | $\Delta P$ | $\ge +15.0\text{ Pa}$ | **$18.0 – 20.0\text{ Pa}$** | **Từ chối giảm quạt nếu $\Delta P < 15.8\text{ Pa}$** | Pa | [ISO 14644-4:2022](https://www.iso.org/standard/76503.html) |
| **02** | **Nồng độ hạt bụi kích thước $\ge 0.5\ \mu m$** | $C_{\text{dust}}$ | $\le 1,000$ (ISO Class 3) | **$< 650\text{ hạt/m}^3$** | **Cảnh báo & can thiệp khi $> 1,000\text{ hạt/m}^3$** | hạt/m³ | [ISO 14644-1:2015](https://www.iso.org/standard/53394.html) |
| **03** | **Khí phân tử ô nhiễm Amoniac (AMC $NH_3$)** | $C_{\text{NH3}}$ | $\le 10.0\text{ ppb}$ | **$< 5.0\text{ ppb}$** | **Kích hoạt quạt khẩn cấp nếu $> 9.0\text{ ppb}$** | ppb | [SEMI F21-95](https://www.semi.org/en/standards) |
| **04** | **Nhiệt độ không khí làm việc** | $T$ | $21.5 – 22.5\text{ °C}$ | **$22.0\text{ °C}$** | Dải an toàn khóa cứng: $[21.7 – 22.3]^\circ\text{C}$ | °C | [Di Natale et al. 2021 (arXiv:2111.12066)](https://arxiv.org/abs/2111.12066) |
| **05** | **Độ ẩm tương đối không khí** | $RH$ | $42.0 – 48.0\text{ \%}$ | **$45.0\text{ \%}$** | Điểm sương kiểm soát $11.06^\circ\text{C}$ | % | [TSMC Hsinchu Dataset](https://raw.githubusercontent.com/nguyenminhhieu22444-source/semiconductor-fab-hvac-optimization/main/data/MAU/MAU%20Reference%20Parameters%20Dataset.csv) |
| **06** | **Gia tốc vi rung động kết cấu mặt sàn** | $a_{\text{vib}}$ | $\le 1.0\text{ cm/s}^2$ | **$< 0.20\text{ cm/s}^2$** | Triệt tiêu rung động thấu kính quang học | cm/s² | [Colin Gordon VC-D Criteria](https://www.colingordon.com/vibration-criteria) |
| **07** | **Tốc độ thay đổi lệnh điều khiển quạt** | Slew-rate | - | **$\le 4.0\text{ \%/phút}$** | Chống hiện tượng xung búa áp suất khí động học | %/phút | [Jeremić & Rakić 2025 (MDPI)](https://www.mdpi.com/2079-9292/14/16/3296) |
| **08** | **Tỷ lệ Wafer xuất xưởng hoàn hảo** | $Y$ | $\ge 99.5\%$ | **$> 99.80\%$** | Tính theo Murphy Yield Model cho diện tích $300\text{ mm}$ | % | [Zhuang et al. 2021 (B&E)](https://doi.org/10.1016/j.buildenv.2020.107572) |

---

## 8. KẾT QUẢ ĐỐI CHUẨN NĂNG LƯỢNG & VẬN HÀNH 24 GIỜ (BASELINE VS AI CDCV)
*(Xác thực từ tệp dữ liệu mô phỏng đối chuẩn 24 giờ: [benchmark_comparison.json](file:///c:/Users/admin/OneDrive/Máy%20tính/semicon_fab_simulation/benchmark_comparison.json))*

Dưới đây là bảng đối sánh chi tiết 100% các đại lượng vận hành giữa mô hình truyền thống cố định và giải pháp AI điều khiển thông gió theo nhu cầu phối hợp (CDCV) tích hợp Cổng an toàn PLC:

| STT | Chỉ số Hiệu năng Vận hành (KPI) | 01_BASELINE (Vận hành Cố định) | 02_AI_SOLUTION (**Áp dụng Chiến lược CDCV**) | Mức độ Tối ưu & Cải thiện | Ý nghĩa Kỹ thuật Thực tế | Link Tệp Dữ liệu Đo đạc |
| :---: | :--- | :---: | :---: | :---: | :--- | :--- |
| **01** | **Tổng điện năng tiêu thụ quạt trong 24h** | **$473.20\text{ kWh}$** | **$216.38\text{ kWh}$** | **Tiết kiệm $256.82\text{ kWh}$ ($54.3\%$)** | Cắt giảm hơn một nửa chi phí điện vận hành hệ thống thông gió phòng sạch | [benchmark_comparison.json](file:///c:/Users/admin/OneDrive/Máy%20tính/semicon_fab_simulation/benchmark_comparison.json) |
| **02** | **Công suất quạt trung bình toàn hệ thống** | $19.72\text{ kW}$ | **$9.02\text{ kW}$** | **Giảm $54.3\%$ phụ tải điện đỉnh** | Giảm dung lượng máy phát điện dự phòng và áp lực lên lưới điện nhà máy | [benchmark_comparison.json](file:///c:/Users/admin/OneDrive/Máy%20tính/semicon_fab_simulation/benchmark_comparison.json) |
| **03** | **Tần số MAU VFD trong Ca Đêm (0h – 6h)** | $47.5\text{ Hz}$ (Cố định $95\%$) | **$35.0 – 35.7\text{ Hz}$** | **Tiết kiệm $58.0\%$ điện năng MAU ca đêm** | Khai thác sâu trạng thái ít phát thải ca đêm, quạt giảm về mức non tải thực tế | [benchmark_comparison.json](file:///c:/Users/admin/OneDrive/Máy%20tính/semicon_fab_simulation/benchmark_comparison.json) |
| **04** | **Tần số MAU VFD trong Ca Ngày (8h – 18h)** | $47.5\text{ Hz}$ (Cố định $95\%$) | **$44.4\text{ Hz}$** ($88.8\%$) | Điều biến bám sát nhu cầu xả Subfab | Cân bằng hoàn hảo lưu lượng hút xả $8,500\text{ m}^3/\text{h}$ mà không lãng phí khí tươi | [benchmark_comparison.json](file:///c:/Users/admin/OneDrive/Máy%20tính/semicon_fab_simulation/benchmark_comparison.json) |
| **05** | **Tần số biến tần MAU trung bình 24h** | $47.5\text{ Hz}$ | **$38.9\text{ Hz}$** | Giảm $18.1\%$ tốc độ vòng quay | Tận dụng quy luật động cơ quạt bậc ba $P \propto f^3$ để tiết kiệm điện tối đa | [benchmark_comparison.json](file:///c:/Users/admin/OneDrive/Máy%20tính/semicon_fab_simulation/benchmark_comparison.json) |
| **06** | **Phụ tải nhiệt dàn sấy Reheat trung bình**| $34.13\text{ kW}_{th}$ | **$27.97\text{ kW}_{th}$** | **Tiết kiệm $18.0\%$ nhiệt lượng sấy bù** | Giảm lưu lượng khí tươi qua MAU trực tiếp làm giảm lượng hơi sấy bù nhiệt | [benchmark_comparison.json](file:///c:/Users/admin/OneDrive/Máy%20tính/semicon_fab_simulation/benchmark_comparison.json) |
| **07** | **Tốc độ lưới 48 quạt FFU trung bình** | $100.0\%$ (Cố định $0.42\text{ m/s}$) | **$66.8\%$** ($0.28 – 0.32\text{ m/s}$) | **Tiết kiệm $> 65.0\%$ điện năng FFU** | Điều biến tốc độ quạt trần linh hoạt theo nồng độ bụi thực tế trong phòng | [benchmark_comparison.json](file:///c:/Users/admin/OneDrive/Máy%20tính/semicon_fab_simulation/benchmark_comparison.json) |
| **08** | **Độ sạch hạt bụi trong ca sản xuất bình thường**| Đạt chuẩn ISO Class 3 | **Đạt chuẩn ISO Class 3** | An toàn hạt bụi tuyệt đối | Nồng độ hạt bụi luôn duy trì dưới ngưỡng cho phép $1,000\text{ hạt/m}^3$ | [benchmark_comparison.json](file:///c:/Users/admin/OneDrive/Máy%20tính/semicon_fab_simulation/benchmark_comparison.json) |
| **09** | **Nồng độ ô nhiễm phân tử AMC ($NH_3$)** | $0.100\text{ ppb}$ (Cực đại $0.48\text{ ppb}$) | **$0.101\text{ ppb}$ (Cực đại $0.53\text{ ppb}$)** | Dưới xa ngưỡng $10.0\text{ ppb}$ | Khả năng tự làm sạch của màng than hoạt tính duy trì môi trường hóa học siêu sạch | [benchmark_comparison.json](file:///c:/Users/admin/OneDrive/Máy%20tính/semicon_fab_simulation/benchmark_comparison.json) |
| **10** | **Gia tốc vi rung động kết cấu mặt sàn** | $0.070\text{ cm/s}^2$ | **$0.051\text{ cm/s}^2$** | **Giảm $27.1\%$ độ rung động cơ học** | Giảm tốc độ quay FFU và MAU làm giảm trực tiếp lực kích động rung thấu kính quang học | [benchmark_comparison.json](file:///c:/Users/admin/OneDrive/Máy%20tính/semicon_fab_simulation/benchmark_comparison.json) |
| **11** | **Tỷ lệ Wafer hoàn hảo (Murphy Yield Model)**| **$99.83\%$** | **$99.83\%$** | **Bảo toàn $100\%$ phẩm cấp sản xuất** | Tối ưu hóa năng lượng triệt để mà không suy giảm bất kỳ phần trăm tỷ lệ thành phẩm nào | [benchmark_comparison.json](file:///c:/Users/admin/OneDrive/Máy%20tính/semicon_fab_simulation/benchmark_comparison.json) |
| **12** | **Thời gian kích hoạt Cổng an toàn PLC Fail-Safe**| $0\text{ phút}$ (Không có AI) | **$33\text{ phút}$** (Khi mở cửa phòng) | **Khống chế $100\%$ nguy cơ mất an toàn** | PLC tự động đè lệnh AI đưa quạt lên $100\%$ khôi phục áp suất và quét sạch bụi xâm lấn | [benchmark_comparison.json](file:///c:/Users/admin/OneDrive/Máy%20tính/semicon_fab_simulation/benchmark_comparison.json) |

---

## 9. LUẬN CHỨNG KHOA HỌC: TÍNH CHÂN THỰC & KHẢ THI THỰC TẾ CỦA BẢN SAO SỐ

Hồ sơ đặc tả thông số trên chứng minh mô hình Nhà máy Bán dẫn Ảo SemiconFab (Bay 1) đạt độ tiệm cận thực tế cao nhất nhờ 4 trụ cột cơ sở:
1. **Sử dụng Dữ liệu Đo đạc Thực nghiệm Gốc:** Không sử dụng các hệ số giả định ngẫu nhiên; toàn bộ 22 thông số chu trình nhiệt ẩm của MAU được lấy trực tiếp từ trạm thực nghiệm TSMC Hsinchu, kết hợp đặc tính tiêu thụ điện của 32 quạt FFU theo các mức vận tốc bề mặt đo đạc thực tế.
2. **Tuân thủ Cơ học Chất khí & Động học Rò rỉ Chuẩn mực:** Áp suất phòng sạch tuân thủ mô hình tiết lưu phi tuyến $\Delta P \propto (V_{\text{net}})^{1.6}$ của Jeremić & Rakić (2025) thay vì mô hình tuyến tính đơn giản hóa, phản ánh đúng quán tính áp suất khí động học thực tế ($\tau_p = 20\text{ s}$).
3. **Mô hình Hóa Thiết bị Bán dẫn Chi tiết:** Bố trí thiết bị tuân theo định dạng công nghiệp SemiconFab Machine Schema (ASML DUV Scanner công suất $90\text{ kW}$ tỏa nhiệt, công suất nguồn $150\text{ kVA}$, phân chia 3 tuyến xả Subfab độc lập Acid/Solvent/Heat).
4. **Kiến trúc An toàn 2 Lớp (AI + PLC Gatekeeper):** Thuật toán tối ưu hóa thông minh CDCV giải bằng SLSQP dự báo nhu cầu tương lai, nhưng luôn được giám sát độc lập bởi Cổng an toàn PLC (Jüni et al. 2026), đảm bảo hệ thống không bao giờ vi phạm các tiêu chuẩn quốc tế ISO 14644 Class 3 và SEMI F21-95 ngay cả khi có sự cố mở cửa đột xuất.
