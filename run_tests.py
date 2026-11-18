"""
Standalone Test Runner for Bay 1 Cleanroom HVAC & AI-CDCV Solution.
Runs all test cases from tests/test_bay1.py with built-in pytest mocks.
"""
import sys
import math
import types
from pathlib import Path

# Add project root and subdirectories to sys.path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "02_ai_solution"))
sys.path.insert(0, str(ROOT / "01_baseline"))

# Provide a lightweight pytest shim if pytest is not installed in the environment
try:
    import pytest
except ImportError:
    pytest = types.ModuleType("pytest")
    
    class Approx:
        def __init__(self, expected, rel=1e-5, abs=1e-9):
            self.expected = expected
            self.rel = rel
            self.abs = abs
        def __eq__(self, actual):
            if hasattr(self.expected, '__iter__') and not isinstance(self.expected, (str, bytes)):
                return all(Approx(e, self.rel, self.abs) == a for e, a in zip(self.expected, actual))
            diff = abs(actual - self.expected)
            tol = max(self.rel * abs(self.expected), self.abs)
            return diff <= tol
        def __repr__(self):
            return f"approx({self.expected} ± {self.abs})"
            
    def approx(expected, rel=1e-5, abs=1e-9):
        return Approx(expected, rel=rel, abs=abs)
        
    def fail(msg=""):
        raise AssertionError(f"pytest.fail: {msg}")
        
    class RaisesContext:
        def __init__(self, expected_exc, match=None):
            self.expected_exc = expected_exc
            self.match = match
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                raise AssertionError(f"Expected exception {self.expected_exc.__name__} was not raised")
            if not issubclass(exc_type, self.expected_exc):
                return False
            if self.match and self.match not in str(exc_val):
                raise AssertionError(f"Exception message '{exc_val}' does not match pattern '{self.match}'")
            return True
            
    def raises(expected_exc, match=None):
        return RaisesContext(expected_exc, match=match)
        
    class Mark:
        @staticmethod
        def parametrize(argnames, argvalues):
            def decorator(fn):
                fn._parametrize = (argnames, argvalues)
                return fn
            return decorator
            
    pytest.approx = approx
    pytest.fail = fail
    pytest.raises = raises
    pytest.mark = Mark()
    sys.modules["pytest"] = pytest

class MonkeyPatch:
    def __init__(self):
        self._undo = []
    def setattr(self, target, name_or_val, value=None):
        if value is None:
            # target is string like "bay1_gpr.load_model"
            mod_name, attr_name = target.rsplit(".", 1)
            mod = sys.modules[mod_name]
            val = name_or_val
        else:
            mod = target
            attr_name = name_or_val
            val = value
        old = getattr(mod, attr_name)
        self._undo.append((mod, attr_name, old))
        setattr(mod, attr_name, val)
    def undo(self):
        for mod, attr, old in reversed(self._undo):
            setattr(mod, attr, old)
        self._undo.clear()

def run_all_tests():
    import tests.test_bay1 as tb
    
    test_functions = [
        ("test_physics_units_and_fan_table", tb.test_physics_units_and_fan_table, False),
        ("test_gate_filters_bad_inputs_with_slew_limits", tb.test_gate_filters_bad_inputs_with_slew_limits, True),
        ("test_gate_enforces_environment_and_requires_recovery_samples", tb.test_gate_enforces_environment_and_requires_recovery_samples, False),
        ("test_door_infeasibility_is_reported", tb.test_door_infeasibility_is_reported, False),
        ("test_gpr_corrects_pressure_and_particles_and_falls_back_outside_domain", tb.test_gpr_corrects_pressure_and_particles_and_falls_back_outside_domain, False),
        ("test_mpc_uses_gpr_bounds_and_plc_checks_physical_transition", tb.test_mpc_uses_gpr_bounds_and_plc_checks_physical_transition, "monkeypatch"),
        ("test_missing_gpr_checkpoint_uses_physics", tb.test_missing_gpr_checkpoint_uses_physics, "monkeypatch"),
        ("test_invalid_control_period_is_rejected_before_forecasting", tb.test_invalid_control_period_is_rejected_before_forecasting, False),
        ("test_ai_sends_one_pair_to_plc_without_running_mpc", tb.test_ai_sends_one_pair_to_plc_without_running_mpc, "monkeypatch"),
        ("test_plc_rejects_stale_command_and_duplicate_recovery_samples", tb.test_plc_rejects_stale_command_and_duplicate_recovery_samples, False),
        ("test_direct_ai_prepares_for_scheduled_exhaust_increase", tb.test_direct_ai_prepares_for_scheduled_exhaust_increase, False),
        ("test_absent_policy_runs_plc_fallback", tb.test_absent_policy_runs_plc_fallback, "monkeypatch"),
        ("test_full_day_benchmark_and_scenarios", tb.test_full_day_benchmark_and_scenarios, False),
        ("test_variable_step_is_used_for_energy_and_timestamps", tb.test_variable_step_is_used_for_energy_and_timestamps, False)
    ]

    print("=" * 70)
    print("  RUNNING COMPREHENSIVE AI-CDCV & BAY 1 VERIFICATION SUITE")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for name, fn, flag in test_functions:
        try:
            if flag == "monkeypatch":
                mp = MonkeyPatch()
                try:
                    fn(mp)
                finally:
                    mp.undo()
            elif flag is True and hasattr(fn, "_parametrize"):
                argname, argvalues = fn._parametrize
                for val in argvalues:
                    fn(val)
            else:
                fn()
            print(f" [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f" [FAIL] {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("=" * 70)
    print(f"  TEST SUMMARY: {passed} PASSED, {failed} FAILED (Total: {len(test_functions)})")
    print("=" * 70)
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
