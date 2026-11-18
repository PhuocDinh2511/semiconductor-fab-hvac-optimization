"""
run_interactive_sac_solution.py
Root launcher for 04_sac_solution interactive visualizer.
Allows seamless execution from the project root directory.
"""
import os
import sys
import importlib.util

current_dir = os.path.dirname(os.path.abspath(__file__))
target_dir = os.path.join(current_dir, "04_sac_solution")
target_script = os.path.join(target_dir, "run_interactive_sac_solution.py")

if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if target_dir not in sys.path:
    sys.path.insert(0, target_dir)

spec = importlib.util.spec_from_file_location("target_sac_module", target_script)
real_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(real_mod)

for attr in dir(real_mod):
    if not attr.startswith("__"):
        globals()[attr] = getattr(real_mod, attr)

if __name__ == "__main__":
    speed = 10
    if len(sys.argv) > 1:
        try:
            speed = int(sys.argv[1])
        except ValueError:
            pass
    real_mod.run_interactive_sac_simulation(speed_factor=speed)
