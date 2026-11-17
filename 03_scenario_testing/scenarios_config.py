"""
scenarios_config.py
Configuration and generation of 5 realistic semiconductor cleanroom operational & incident scenarios.
Calibrated and mapped directly to published literature and industry standards:
- Scenario 1: Standard 24h 2-Shift Operation (Zhuang et al., 2021 CDCV; TSMC Hsinchu Reference Dataset)
- Scenario 2: Emergency Door Breach & Pressure Cascade Collapse (Zhou et al., 2024; ISO 14644-3; SEMI S2)
- Scenario 3: Extreme Summer Heatwave & Dehumidification Stress (Porowski & Jakubiak, 2022; TSMC Summer Peak)
- Scenario 4: Airborne Molecular Contamination (AMC) Surge & Solvent Outgassing (Li et al., 2007 AAQR; SEMI F21-95)
- Scenario 5: Weekend Tool Idle Maintenance & Low-Load Standby (TSMC 35Hz VFD Empirical Dataset; DeepMind Safety-First AI)
"""
import numpy as np

def generate_scenario_1_standard(n_steps=1440, seed=42):
    """
    Scenario 1: Standard 24h Dual-Shift Production
    - Night Shift (00:00 - 06:00): Standby / minimal personnel, exhaust throttled to 5,000 m3/h.
    - Shift Handover (06:00 - 08:00): Ramp up from 5,000 to 8,500 m3/h.
    - Morning Full Production (08:00 - 12:00): 8,500 m3/h, peak lithography exposure (90 kW).
    - Lunch Transition (12:00 - 13:00): Partial load (6,500 m3/h, 60 kW).
    - Afternoon Peak Production (13:00 - 18:00): Full DUV immersion litho (8,500 m3/h, 88 kW).
    - Evening Track Processing (18:00 - 22:00): 6,200 m3/h, 50 kW.
    - Night Return (22:00 - 24:00): Standby 5,000 m3/h.
    """
    np.random.seed(seed)
    times_hr = np.linspace(0, 24, n_steps, endpoint=False)
    q_mes = np.zeros(n_steps)
    particle_gen = np.zeros(n_steps)
    exhaust_override = np.zeros(n_steps)
    outdoor_temp = np.full(n_steps, 29.93)
    outdoor_rh = np.full(n_steps, 80.0)
    amc_multiplier = np.ones(n_steps)
    sensor_glitch = np.zeros(n_steps, dtype=bool)
    ai_fault_injection = np.zeros(n_steps, dtype=bool)

    for i, t in enumerate(times_hr):
        if 0.0 <= t < 6.0:
            q_base = 25.0 + 3.0 * np.sin(t * np.pi / 3.0)
            p_gen = 120.0 + 15.0 * np.random.randn()
            exh = 5000.0 + 50.0 * np.random.randn()
        elif 6.0 <= t < 8.0:
            ratio = (t - 6.0) / 2.0
            q_base = 25.0 + ratio * 65.0
            p_gen = 150.0 + ratio * 330.0 + 20.0 * np.random.randn()
            exh = 5000.0 + ratio * 3500.0
        elif 8.0 <= t < 12.0:
            q_base = 90.0 + 6.0 * np.sin(t * 2.0)
            p_gen = 480.0 + 40.0 * np.random.randn()
            exh = 8500.0 + 60.0 * np.sin(t * 2.0)
        elif 12.0 <= t < 13.0:
            q_base = 60.0 + 4.0 * np.sin(t)
            p_gen = 280.0 + 25.0 * np.random.randn()
            exh = 6500.0 + 50.0 * np.random.randn()
        elif 13.0 <= t < 18.0:
            q_base = 88.0 + 5.0 * np.cos(t * 1.5)
            p_gen = 470.0 + 35.0 * np.random.randn()
            exh = 8500.0 + 60.0 * np.cos(t * 1.5)
        elif 18.0 <= t < 22.0:
            q_base = 50.0 + 4.0 * np.sin(t)
            p_gen = 260.0 + 25.0 * np.random.randn()
            exh = 6200.0 + 50.0 * np.random.randn()
        else:
            q_base = 28.0 + 3.0 * np.random.randn()
            p_gen = 130.0 + 15.0 * np.random.randn()
            exh = 5000.0 + 50.0 * np.random.randn()

        # Minor diurnal ambient temperature swing (28°C at night to 32°C at 14:00)
        outdoor_temp[i] = 28.0 + 4.0 * np.sin((t - 6.0) * np.pi / 12.0) if 6.0 <= t <= 18.0 else 28.0

        q_mes[i] = max(15.0, q_base + 1.0 * np.random.randn())
        particle_gen[i] = max(50.0, p_gen)
        exhaust_override[i] = max(4500.0, exh) / 3600.0

    return {
        "id": "scenario_1",
        "name": "Kịch bản 1: Vận hành Chuẩn 24 Giờ (2 Ca Ngày/Đêm)",
        "description": "Chu trình 24h tiêu chuẩn: ca ngày toàn tải (8,500 m3/h) và ca đêm non tải (5,000 m3/h). Tham chiếu: Zhuang et al. (2021) CDCV & TSMC Hsinchu Baseline.",
        "incident_ref": "Vận hành điều độ tải nhiệt thực tế (Standard Dual-Shift Baseline - Zhuang et al., 2021).",
        "times_hr": times_hr,
        "q_mes": q_mes,
        "particle_gen": particle_gen,
        "exhaust_override": exhaust_override,
        "outdoor_temp": outdoor_temp,
        "outdoor_rh": outdoor_rh,
        "amc_multiplier": amc_multiplier,
        "sensor_glitch": sensor_glitch,
        "ai_fault_injection": ai_fault_injection
    }


def generate_scenario_2_door_breach(n_steps=1440, seed=42):
    """
    Scenario 2: Emergency Door Opening & Particle Inrush Disturbance
    - Simulates an emergency maintenance interlock breach at 11:30 - 12:00 (30 mins).
    - Sudden exhaust airflow surge to 10,800 m3/h causing rapid positive pressure loss.
    - Particle generation spikes by +750 particles/min from adjacent technical chase.
    - Tests PLC Safety Gatekeeper speed and failsafe recovery without wafer damage.
    """
    data = generate_scenario_1_standard(n_steps=n_steps, seed=seed)
    data["id"] = "scenario_2"
    data["name"] = "Kịch bản 2: Sự cố Mở Cửa Bảo Dưỡng & Sụp Đổ Áp Suất Dương"
    data["description"] = "Cửa phòng sạch bị mở 30 phút (11h30 - 12h00) gây tụt áp và rò rỉ bụi (+750 hạt/min). Tham chiếu: Zhou et al. (Building and Environment 2024), Tiêu chuẩn ISO 14644-3 & SEMI S2."
    data["incident_ref"] = "Sự cố mất chênh áp dương và xâm nhập bụi do mở cửa phòng sạch (Zhou et al., 2024)."

    for i, t in enumerate(data["times_hr"]):
        if 11.5 <= t <= 12.0:
            # Door breach event
            data["exhaust_override"][i] = 10800.0 / 3600.0 # 3.0 m3/s (exceeds rated MAU capacity)
            data["particle_gen"][i] += 750.0                # Severe dust inrush
        if 14.0 <= t <= 14.25:
            # AI adversarial fault injection to test PLC safety boundary
            data["ai_fault_injection"][i] = True

    return data


def generate_scenario_3_summer_heatwave(n_steps=1440, seed=42):
    """
    Scenario 3: Extreme Summer Heatwave & 90% RH Humidity Stress
    - Outdoor ambient temperature reaches extreme peak of 38.5°C with 90% relative humidity.
    - Outdoor dew point rises to 26.2°C, putting maximum dehumidification load on MAU recooling coil.
    - Evaluates whether MAU precooling + recooling + reheat coils can maintain 22.0 ± 0.3°C and 45% RH.
    """
    data = generate_scenario_1_standard(n_steps=n_steps, seed=seed)
    data["id"] = "scenario_3"
    data["name"] = "Kịch bản 3: Sóng Nhiệt Mùa Hè Cực Hạn (38.5°C, 90% RH)"
    data["description"] = "Nhiệt ẩm ngoài trời khắc nghiệt kiểm tra phụ tải tách ẩm sâu và sấy bù của MAU. Tham chiếu: Porowski & Jakubiak (Energies 2022) & TSMC Hsinchu Summer Peak."
    data["incident_ref"] = "Ứng suất nhiệt ẩm khắc nghiệt và nguy cơ đọng sương / quá tải cuộn lạnh MAU."

    times_hr = data["times_hr"]
    for i, t in enumerate(times_hr):
        # Severe sinusoidal ambient heatwave peaking at 14:00 (38.5°C, 90% RH)
        heat_factor = max(0.0, np.sin((t - 7.0) * np.pi / 14.0))
        data["outdoor_temp"][i] = 30.0 + 8.5 * heat_factor
        data["outdoor_rh"][i] = 75.0 + 15.0 * heat_factor

    return data


def generate_scenario_4_chemical_amc_surge(n_steps=1440, seed=42):
    """
    Scenario 4: Chemical AMC Contamination Surge & Solvent Exhaust Spike
    - Track coater photoresist spin-coating & hotplate bake units experience abnormal outgassing.
    - Airborne Molecular Contamination (AMC NH3 & VOC solvents) surges by 4.5x at 14:00 - 16:30.
    - Evaluates chemical carbon filter absorption and FFU airflow sweeping compliance with SEMI F21-95 (<10 ppb).
    """
    data = generate_scenario_1_standard(n_steps=n_steps, seed=seed)
    data["id"] = "scenario_4"
    data["name"] = "Kịch bản 4: Đột Biến Hóa Chất AMC (Amoniac NH3 & Dung Môi Bốc Hơi)"
    data["description"] = "Phát tán hóa chất AMC nồng độ cao từ công đoạn nướng keo Track Coater (4.5x). Tham chiếu: Li et al. (AAQR 2007) & Chuẩn SEMI F21-95 (<10 ppb)."
    data["incident_ref"] = "Sự cố bốc hơi hóa chất phân tử AMC và rò rỉ dung môi hữu cơ (Li et al., 2007; SEMI F21-95)."

    for i, t in enumerate(data["times_hr"]):
        if 14.0 <= t <= 16.5:
            # Chemical surge
            data["amc_multiplier"][i] = 4.5
            data["exhaust_override"][i] = min(3.0, data["exhaust_override"][i] + (1500.0 / 3600.0))

    return data


def generate_scenario_5_weekend_maintenance(n_steps=1440, seed=42):
    """
    Scenario 5: Weekend Tool Maintenance & Low-Production Standby
    - 24 hours of continuous low-activity idle standby.
    - ASML DUV Stepper idling at 25 kW standby heat; only 1 inspection engineer (60 particles/min).
    - Tool exhaust throttled to 4,800 m3/h all day.
    - Evaluates deep part-load energy saving potential of CDCV (MAU at 35.0 Hz minimum, FFU at 0.32 m/s).
    """
    np.random.seed(seed)
    times_hr = np.linspace(0, 24, n_steps, endpoint=False)
    q_mes = 25.0 + 2.0 * np.random.randn(n_steps)
    particle_gen = 80.0 + 15.0 * np.random.randn(n_steps)
    exhaust_override = np.full(n_steps, 4800.0 / 3600.0) # 1.333 m3/s
    outdoor_temp = np.full(n_steps, 27.5)
    outdoor_rh = np.full(n_steps, 75.0)
    amc_multiplier = np.full(n_steps, 0.6) # Reduced chemical usage on weekend
    sensor_glitch = np.zeros(n_steps, dtype=bool)
    ai_fault_injection = np.zeros(n_steps, dtype=bool)

    return {
        "id": "scenario_5",
        "name": "Kịch bản 5: Chế độ Chờ Cuối Tuần / Bảo Trì Máy Quang Khắc ASML",
        "description": "Buồng sạch hoạt động ở chế độ chờ 24h, kiểm chứng mức tiết kiệm điện tối đa ở điểm non tải (35 Hz). Tham chiếu: TSMC VFD empirical dataset & DeepMind Safety-First AI.",
        "incident_ref": "Vận hành non tải liên tục & cơ chế bảo vệ dự phòng khi phụ tải xả Subfab giảm sâu.",
        "times_hr": times_hr,
        "q_mes": q_mes,
        "particle_gen": particle_gen,
        "exhaust_override": exhaust_override,
        "outdoor_temp": outdoor_temp,
        "outdoor_rh": outdoor_rh,
        "amc_multiplier": amc_multiplier,
        "sensor_glitch": sensor_glitch,
        "ai_fault_injection": ai_fault_injection
    }


def get_all_scenarios(n_steps=1440):
    """Return dictionary of all 5 configured scenarios."""
    return {
        "1": generate_scenario_1_standard(n_steps),
        "2": generate_scenario_2_door_breach(n_steps),
        "3": generate_scenario_3_summer_heatwave(n_steps),
        "4": generate_scenario_4_chemical_amc_surge(n_steps),
        "5": generate_scenario_5_weekend_maintenance(n_steps)
    }
