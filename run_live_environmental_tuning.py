"""
run_live_environmental_tuning.py (Root Launcher)
Khởi chạy Bảng điều khiển tương tác trực tiếp các tham số ngoại cảnh & mô phỏng thời gian thực.
"""
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
target_dir = os.path.join(current_dir, "03_scenario_testing")
sys.path.insert(0, target_dir)

from run_live_environmental_tuning import create_live_tuning_app

if __name__ == "__main__":
    create_live_tuning_app()
