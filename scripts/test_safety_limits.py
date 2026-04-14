"""Tests for NATE vΞ⁷·₁ — Safety Limits"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np
from src.utils.validation import SafetyChecker, SafetyViolation
from src.core.constants import ISPTA_MAX, DELTA_T_MAX, US_FREQ_MIN, US_FREQ_MAX


def test_intensity_pass():
    checker = SafetyChecker()
    assert checker.check_intensity(ISPTA_MAX * 0.5) is True


def test_intensity_fail():
    checker = SafetyChecker()
    with pytest.raises(SafetyViolation):
        checker.check_intensity(ISPTA_MAX * 1.1)


def test_intensity_negative():
    checker = SafetyChecker()
    with pytest.raises(SafetyViolation):
        checker.check_intensity(-10.0)


def test_frequency_pass():
    checker = SafetyChecker()
    assert checker.check_frequency(500e3) is True


def test_frequency_fail_low():
    checker = SafetyChecker()
    with pytest.raises(SafetyViolation):
        checker.check_frequency(100e3)


def test_frequency_fail_high():
    checker = SafetyChecker()
    with pytest.raises(SafetyViolation):
        checker.check_frequency(1e6)


def test_thermal_pass():
    checker = SafetyChecker()
    assert checker.check_thermal(DELTA_T_MAX * 0.5) is True


def test_thermal_fail():
    checker = SafetyChecker()
    with pytest.raises(SafetyViolation):
        checker.check_thermal(DELTA_T_MAX * 1.5)


def test_check_all_pass():
    checker = SafetyChecker()
    results = checker.check_all(
        intensity=100.0, freq=500e3, mod_freq=40.0,
        delta_T=0.3, duration=600.0
    )
    assert all(v == "PASS" for v in results.values())


def test_check_all_fail():
    checker = SafetyChecker()
    results = checker.check_all(
        intensity=10000.0, freq=500e3, mod_freq=40.0,
        delta_T=5.0, duration=10000.0
    )
    assert results["intensity"].startswith("FAIL")
    assert results["thermal"].startswith("FAIL")
    assert results["duration"].startswith("FAIL")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
