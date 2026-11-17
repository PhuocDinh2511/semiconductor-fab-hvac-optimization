"""
run_interactive_scenarios.py
Root launcher for 03_scenario_testing interactive visualizer.
Allows seamless execution from the project root directory.
"""
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
target_dir = os.path.join(current_dir, "03_scenario_testing")
target_script = os.path.join(target_dir, "run_interactive_scenarios.py")

if __name__ == "__main__":
    import subprocess
    cmd = [sys.executable, target_script] + sys.argv[1:]
    subprocess.run(cmd, cwd=target_dir)
