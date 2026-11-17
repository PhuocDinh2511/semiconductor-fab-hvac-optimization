"""
Cleanroom Physics and Semiconductor Plant Dynamics Model
Based on SemiconFab Digital Twin Architecture (300mm Wafer Fab Bay 1 - Lithography & Track)
Conforms to:
- SEMI Standards: SEMI F21 (AMC Chemical Limits), SEMI E72 (Footprint), SEMI S2 (Safety)
- ISO 14644-1:2015 Cleanroom Standards (ISO Class 3)
- Empirical Datasets:
  * 300mm Cleanroom Workplace Contaminants Dataset (AMC, Vibration, Particles)
  * Real-world 34 FFU Empirical Velocity & Power Dataset (Table 3 & 4)
  * TSMC Hsinchu MAU Reference Parameters Dataset (Summer/Winter Coils, 6C Chilled Water)
"""
import numpy as np


class CleanroomPlant:
    def __init__(self):
        # 1. Physical Geometry (from SemiconFab TWIN-DATA-MAP)
        # Bay 1 (Lithography & Track): Length 30m, Width 18m, Height 5.22m (FFU plenum ceiling)
        self.length = 30.0  # m
        self.width = 18.0   # m
        self.height = 5.22  # m
        self.volume = self.length * self.width * self.height  # 2818.8 m3
        self.floor_area = self.length * self.width            # 540.0 m2

        # 2. Air Properties (standard cleanroom condition: 22C, 101.3 kPa)
        self.rho_air = 1.204   # kg/m3
        self.cp_air = 1005.0   # J/(kg*K)
        self.mass_air = self.volume * self.rho_air # ~3394 kg

        # 3. Cleanroom FFU Equipment Specifications (Calibrated from Table 3 Empirical Data)
        # 48 FFU units covering the ceiling grid
        self.n_ffu = 48
        # High speed: v = 0.52 m/s -> Q = 1355.6 m3/h -> P = 133.9 W per unit
        self.ffu_rated_airflow = 1355.6 / 3600.0  # m3/s per unit (~0.3765 m3/s)
        self.ffu_rated_power = 133.9              # Watts per unit (calibrated from Table 3)
        self.hepa_efficiency = 0.99999           # ULPA U15/U16 99.999% efficiency at MPPS (0.1 - 0.2 µm particles)
        self.chemical_filter_efficiency = 0.95   # Activated carbon filter for AMC (Ammonia/VOC)

        # 4. MAU (Make-up Air Unit) System Specifications (from TSMC Hsinchu Dataset)
        # Airflow: 63,000 m3/h actual / 100,000 m3/h design per fan (total 318,008 m3/h across 6 units)
        # Bay 1 slice fresh air flow: 10,800 m3/h (3.0 m3/s design capacity)
        self.mau_max_airflow = 10800.0 / 3600.0  # m3/s (3.0 m3/s design capacity)
        self.mau_design_airflow_m3h = 100000.0   # m3/h design full-scale
        self.mau_actual_airflow_m3h = 63000.0    # m3/h measured operating fan
        self.mau_rated_power = 15500.0           # Watts (15.5 kW per MAU fan; 93 kW for 6 units)
        self.mau_filter_dp = 1182.0              # Pa (measured filter differential pressure)
        self.mau_chilled_water_temp = 6.0        # deg C (chilled water supply setpoint)
        self.mau_vfd_rated_freq = 50.0           # Hz (rated motor frequency)
        self.mau_vfd_measured_freq = 35.0        # Hz (measured operating frequency at partial load)

        # Ambient Outdoor Psychrometric Conditions (Hsinchu Taiwan Summer/Winter)
        self.outdoor_temp_summer = 35.0          # deg C (peak summer design)
        self.outdoor_temp_winter = 5.0           # deg C (winter design)
        self.outdoor_temp = 29.93                # deg C (measured cooling coil inlet air temperature)
        self.outdoor_rh = 80.0                   # % (summer outdoor RH)
        self.outdoor_dew_point = 16.40           # deg C (measured outdoor air dew point)

        # 2-Stage Cooling & Dehumidification Coil Specifications
        self.mau_precool_inlet_temp = 29.93      # deg C (precool coil inlet)
        self.mau_precool_outlet_temp = 17.70     # deg C (precool coil outlet)
        self.mau_recool_inlet_temp = 17.70       # deg C (recool coil inlet)
        self.mau_recool_outlet_temp = 11.06      # deg C (recool coil outlet = supply dew point)
        self.mau_heating_outlet_temp = 20.99     # deg C (heating coil outlet setpoint 21.00 deg C)
        self.mau_supply_air_temp = 20.99         # deg C (measured supply air temp)
        self.mau_supply_air_dewpoint = 11.06     # deg C (measured supply air dew point)

        # 5. Segregated Process Exhaust Streams (SemiconFab & Subfab Standards)
        # Total: 8,500 m3/h (2.361 m3/s) split by hazard category
        self.exhaust_acid_flow = 3500.0 / 3600.0    # Acid exhaust to wet scrubbers
        self.exhaust_solvent_flow = 3000.0 / 3600.0 # VOC solvent exhaust from Track to RTO
        self.exhaust_heat_flow = 2000.0 / 3600.0   # General heat exhaust
        self.base_exhaust_flow = self.exhaust_acid_flow + self.exhaust_solvent_flow + self.exhaust_heat_flow

        # 6. Environmental Management Targets & Limits (from 300mm Fab Dataset)
        self.target_temp = 22.0                  # deg C (target 22.0C - 23.0C)
        self.temp_min = 21.5
        self.temp_max = 22.5
        self.target_rh = 42.5                    # % RH (range 40 - 45%)
        self.rh_min = 40.0
        self.rh_max = 45.0
        self.target_dp_min = 15.0                # Pa (>= 0.5 mmH2O = 15 Pa threshold)
        self.particle_class_limit = 1000.0       # particles/m3 (ISO 14644-1:2015 Class 3 limit for particles >= 0.1 µm)

        # Airborne Molecular Contamination (SEMI F21 / 300mm Dataset)
        self.amc_nh3_limit = 10.0                # ppb (Ammonium / Ammonia max management criteria)
        self.amc_nh3_baseline = 0.8              # ppb (Empirical cleanroom 300mm avg 0.8 ppb)
        self.amc_ambient_nh3 = 3.5               # ppb (Outdoor/corridor infiltration level)

        # Micro-Vibration (VC Criteria for Lithography Steppers)
        self.vibration_limit = 1.0               # cm/s2 zero-peak max criteria
        self.vibration_baseline = 0.05           # cm/s2 typical floor vibration (0.01 - 0.15)

        # 7. Wafer Economics & Yield Modeling
        self.wafer_lot_size = 25                 # 25 wafers per FOUP
        self.wafer_unit_value_usd = 5000.0       # $5,000 USD per 300mm processed wafer

        # Thermal capacitance
        self.C_thermal = self.mass_air * self.cp_air # J/K (~3.41 MJ/K)

        self.reset()

    def reset(self):
        self.temp = 22.0            # deg C
        self.rh = 42.5              # %
        self.dp = 20.0              # Pa
        self.particle_count = 250.0 # particles/m3
        self.amc_nh3 = 0.8          # ppb
        self.vibration = 0.05       # cm/s2
        self.wafer_yield = 99.8     # %
        self.time_min = 0.0

    def compute_fan_powers(self, u_mau, u_ffu):
        """
        Fan Affinity Laws: Power is proportional to speed cubed (P ~ u^3).
        Calibrated against Table 3 empirical FFU measurements:
        At u=1.0: 48 * 133.9 W = 6,427 W.
        MAU fan: 15,000 W * u^3.
        """
        p_mau = self.mau_rated_power * (u_mau ** 3)
        p_ffu = self.n_ffu * self.ffu_rated_power * (u_ffu ** 3)
        return p_mau, p_ffu  # in Watts

    def compute_pressure_steady(self, v_mau, v_exhaust):
        """
        Orifice flow relation for cleanroom envelope leakage:
        V_net = V_mau - V_exhaust = C_leak * sqrt(2 * dP / rho)
        """
        v_net = v_mau - v_exhaust
        if v_net <= 0:
            return max(0.0, 5.0 + v_net * 10.0) # Complete loss of positive pressure
        dp = 5.0 + 85.0 * (v_net ** 1.6)
        return np.clip(dp, 0.0, 50.0)

    def step(self, u_mau, u_ffu, q_mes_kw, particle_gen_rate, exhaust_override=None, dt_sec=60.0):
        """
        Simulate 1 time step (dt_sec) of cleanroom multi-physics dynamics:
        - Airflows & Differential Pressure
        - Particle Concentration & ISO Class 3 Filter Decay
        - Airborne Molecular Contamination (AMC NH3 in ppb)
        - Micro-Vibration (cm/s2)
        - Thermal Balance (First Law) & Chilled Water Coil
        - Wafer Yield & Scrap Impact
        """
        u_mau = float(np.clip(u_mau, 0.2, 1.0))
        u_ffu = float(np.clip(u_ffu, 0.2, 1.0))

        # 1. Airflows
        v_mau = u_mau * self.mau_max_airflow
        v_ffu = u_ffu * (self.n_ffu * self.ffu_rated_airflow)
        v_exhaust = exhaust_override if exhaust_override is not None else self.base_exhaust_flow

        # 2. Positive Differential Pressure (Delta P) Dynamics
        dp_steady = self.compute_pressure_steady(v_mau, v_exhaust)
        tau_p = 20.0 # seconds
        alpha_p = dt_sec / (tau_p + dt_sec)
        self.dp = float(self.dp + alpha_p * (dp_steady - self.dp))

        # 3. Particle Concentration Dynamics (ISO 14644-1)
        c_ambient = 500000.0 # Ambient corridor particle count
        leak_in = max(0.0, 15.0 - self.dp) * 0.02
        filter_rate = (v_ffu * self.hepa_efficiency + v_exhaust) / self.volume
        d_particles = (particle_gen_rate / self.volume) + (leak_in * c_ambient / self.volume) - (filter_rate * self.particle_count)
        self.particle_count = float(max(50.0, self.particle_count + d_particles * dt_sec))

        # 4. Airborne Molecular Contamination (AMC NH3 ppb - SEMI F21)
        # Operator emission (sweat/breath) correlates with human presence
        g_amc_nh3 = 0.02 * (particle_gen_rate / 150.0) # ppb*m3/s
        chem_filt_rate = (v_ffu * self.chemical_filter_efficiency + v_exhaust) / self.volume
        leak_amc = leak_in * self.amc_ambient_nh3 / self.volume
        d_amc = (g_amc_nh3 / self.volume) + leak_amc - (chem_filt_rate * self.amc_nh3)
        self.amc_nh3 = float(np.clip(self.amc_nh3 + d_amc * dt_sec, 0.1, 40.0))

        # 5. Micro-Vibration (VC Criteria - cm/s2 zero-peak)
        # Increases slightly with high aerodynamic FFU velocity and personnel movement
        vib_aero = 0.03 * (u_ffu ** 2)
        vib_personnel = 0.03 * min(1.0, particle_gen_rate / 400.0)
        self.vibration = float(np.clip(0.02 + vib_aero + vib_personnel + 0.005 * np.random.randn(), 0.01, 0.50))

        # 6. MAU Detailed Psychrometric Coils & Supply Air Conditioning (from Hsinchu Dataset)
        mau_vfd_hz = float(np.clip(self.mau_vfd_rated_freq * u_mau, 25.0, 50.0))
        m_dot_mau = v_mau * 1.20 # kg/s

        # Dàn lạnh sơ bộ (Precool): Làm lạnh khí tươi ngoại cảnh từ 29.93C -> 17.70C
        q_mau_precool_kw = float(m_dot_mau * 1.005 * (self.outdoor_temp - self.mau_precool_outlet_temp))

        # Dàn lạnh sâu (Recool): Tách ẩm ngưng tụ từ 17.70C -> 11.06C (Điểm sương gió cấp 11.06C)
        w_in = 0.0150 # kg hơi nước / kg khí khô (tại 17.7C bão hòa)
        w_out = 0.0083 # kg hơi nước / kg khí khô (tại 11.06C điểm sương)
        q_mau_recool_kw = float(m_dot_mau * 1.005 * (self.mau_recool_inlet_temp - self.mau_recool_outlet_temp) + m_dot_mau * 2501.0 * max(0.0, w_in - w_out))

        # Dàn sưởi điều nhiệt (Heating Coil): Sấy bù từ 11.06C -> 20.99C
        q_mau_reheat_kw = float(m_dot_mau * 1.005 * (self.mau_heating_outlet_temp - self.mau_recool_outlet_temp))

        # Độ mở van nước lạnh 6°C & van nước nóng (%)
        cw_valve_pct = float(np.clip(u_mau * 100.0, 0.0, 100.0))
        hw_valve_pct = float(np.clip(u_mau * 85.0, 0.0, 100.0))

        # 7. Thermal Dynamics with HVAC Chilled Water Coil Modulation
        p_mau, p_ffu = self.compute_fan_powers(u_mau, u_ffu)
        q_fan_kw = (p_mau + p_ffu) * 0.65 / 1000.0
        q_total_kw = q_mes_kw + q_fan_kw

        max_cooling_capacity = 30.0 + 130.0 * (0.35 * u_mau + 0.65 * u_ffu)
        cooling_demand = q_total_kw + 25.0 * (self.temp - self.target_temp)
        q_cooling_actual = np.clip(cooling_demand, 0.0, max_cooling_capacity)

        d_temp = ((q_total_kw - q_cooling_actual) * 1000.0) / self.C_thermal
        self.temp = float(self.temp + d_temp * dt_sec)

        # 8. Humidity Dynamics
        rh_target = 42.5
        d_rh = -0.02 * (self.temp - 22.0) - 0.005 * (self.rh - rh_target)
        self.rh = float(np.clip(self.rh + d_rh, 40.0, 45.0))

        # 9. Wafer Yield & Defectivity Assessment (Murphy Model)
        excursion_score = 0.0
        if self.temp < self.temp_min or self.temp > self.temp_max:
            excursion_score += abs(self.temp - 22.0) * 1.5
        if self.dp < self.target_dp_min:
            excursion_score += (self.target_dp_min - self.dp) * 0.5
        if self.particle_count > self.particle_class_limit:
            excursion_score += (self.particle_count - self.particle_class_limit) / 500.0
        if self.amc_nh3 > self.amc_nh3_limit:
            excursion_score += (self.amc_nh3 - self.amc_nh3_limit) * 0.8

        instant_yield = 100.0 * np.exp(-0.015 * excursion_score)
        self.wafer_yield = float(np.clip(instant_yield, 0.0, 100.0))

        self.time_min += dt_sec / 60.0
        return {
            "temp": self.temp,
            "rh": self.rh,
            "dp": self.dp,
            "particle_count": self.particle_count,
            "amc_nh3": self.amc_nh3,
            "vibration": self.vibration,
            "wafer_yield": self.wafer_yield,
            "p_mau_kw": p_mau / 1000.0,
            "p_ffu_kw": p_ffu / 1000.0,
            "p_total_kw": (p_mau + p_ffu) / 1000.0,
            "mau_vfd_hz": mau_vfd_hz,
            "mau_filter_dp": self.mau_filter_dp,
            "mau_supply_temp": self.mau_supply_air_temp,
            "mau_supply_dewpoint": self.mau_supply_air_dewpoint,
            "mau_precool_kw": q_mau_precool_kw,
            "mau_recool_kw": q_mau_recool_kw,
            "mau_reheat_kw": q_mau_reheat_kw,
            "mau_cw_valve_pct": cw_valve_pct,
            "mau_hw_valve_pct": hw_valve_pct,
            "exhaust_acid_m3h": self.exhaust_acid_flow * 3600.0,
            "exhaust_solvent_m3h": self.exhaust_solvent_flow * 3600.0,
            "exhaust_heat_m3h": self.exhaust_heat_flow * 3600.0
        }


def get_standard_mes_scenario(n_steps=1440, seed=42):
    """
    Standardized 24-hour MES production scenario for reproducible benchmark comparison.
    """
    np.random.seed(seed)
    times_hr = np.linspace(0, 24, n_steps, endpoint=False)
    q_mes = np.zeros(n_steps)
    particle_gen = np.zeros(n_steps)
    exhaust_override = [None] * n_steps
    sensor_glitch = [False] * n_steps
    ai_fault_injection = [False] * n_steps

    for i, t in enumerate(times_hr):
        if 0.0 <= t < 6.0:
            q_base = 25.0 + 4.0 * np.sin(t * np.pi / 3.0)
            p_gen = 120.0 + 20.0 * np.random.randn()
            exh_m3h = 5000.0 + 80.0 * np.random.randn()   # Ca đêm: Thiết bị Standby, van xả nhiệt & dung môi đóng bớt (5,000 m3/h)
        elif 6.0 <= t < 8.0:
            ratio = (t - 6.0) / 2.0
            q_base = 25.0 + ratio * 65.0
            p_gen = 150.0 + ratio * 350.0 + 30.0 * np.random.randn()
            exh_m3h = 5000.0 + ratio * 3500.0             # Giao ca: Gia nhiệt & mở dần van xả 5,000 -> 8,500 m3/h
        elif 8.0 <= t < 12.0:
            q_base = 90.0 + 8.0 * np.sin(t * 2.0)
            p_gen = 480.0 + 50.0 * np.random.randn()
            exh_m3h = 8500.0 + 80.0 * np.sin(t * 2.0)     # Ca sáng: Quang khắc toàn tải 8,500 m3/h
        elif 12.0 <= t < 13.0:
            q_base = 60.0 + 5.0 * np.sin(t)
            p_gen = 280.0 + 30.0 * np.random.randn()
            exh_m3h = 6500.0 + 60.0 * np.random.randn()   # Nghỉ trưa: Bán tải 6,500 m3/h
        elif 13.0 <= t < 18.0:
            q_base = 88.0 + 7.0 * np.cos(t * 1.5)
            p_gen = 470.0 + 40.0 * np.random.randn()
            exh_m3h = 8500.0 + 80.0 * np.cos(t * 1.5)     # Ca chiều: Quang khắc ngập DUV toàn tải 8,500 m3/h
        elif 18.0 <= t < 22.0:
            q_base = 50.0 + 5.0 * np.sin(t)
            p_gen = 260.0 + 30.0 * np.random.randn()
            exh_m3h = 6200.0 + 60.0 * np.random.randn()   # Ca tối: Tráng keo Track coater 6,200 m3/h
        else:
            q_base = 28.0 + 4.0 * np.random.randn()
            p_gen = 130.0 + 20.0 * np.random.randn()
            exh_m3h = 5000.0 + 80.0 * np.random.randn()   # Ca đêm: Chế độ chờ 5,000 m3/h

        # EVENT 1: AI fault test at 03:00 - 03:15
        if 3.0 <= t <= 3.25:
            ai_fault_injection[i] = True

        # EVENT 2: Physical door disturbance at 11:30 - 11:45
        if 11.5 <= t <= 11.75:
            exh_m3h = 10200.0
            p_gen += 400.0

        # EVENT 3: Sensor EMI noise at 16:30 - 16:45
        if 16.5 <= t <= 16.75:
            sensor_glitch[i] = True

        q_mes[i] = max(15.0, q_base + 1.5 * np.random.randn())
        particle_gen[i] = max(50.0, p_gen)
        exhaust_override[i] = max(4500.0, exh_m3h) / 3600.0

    return times_hr, q_mes, particle_gen, exhaust_override, sensor_glitch, ai_fault_injection
