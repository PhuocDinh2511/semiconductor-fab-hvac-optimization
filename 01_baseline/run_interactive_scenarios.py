"""
run_interactive_scenarios.py
Launcher for 03_scenario_testing interactive visualizer from within 01_baseline.
Allows seamless execution when the terminal is located inside 01_baseline.
"""
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
target_dir = os.path.abspath(os.path.join(current_dir, "..", "03_scenario_testing"))
target_script = os.path.join(target_dir, "run_interactive_scenarios.py")

if __name__ == "__main__":
    import subprocess
    cmd = [sys.executable, target_script] + sys.argv[1:]
    subprocess.run(cmd, cwd=target_dir)
