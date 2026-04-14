"""
NATE vΞ⁷·₁ — Input Validation and Bounds Checking

Ensures all parameters remain within safe operating limits.
This module implements the safety constraints from Chapter 5 of the specification.
"""

import numpy as np
from src.core.constants import (
    ISPTA_MAX, MI_MAX, TI_CRANIAL_MAX, DELTA_T_MAX,
    US_FREQ_MIN, US_FREQ_MAX, MOD_FREQ_MIN, MOD_FREQ_MAX,
    SESSION_DURATION_MAX, DUTY_CYCLE_MAX,
)


class SafetyViolation(Exception):
    """Raised when a parameter exceeds its safety limit."""
    pass


class SafetyChecker:
    """
    Validates acoustic stimulation parameters against regulatory limits.
    
    All checks implement the constraints from:
    - FDA (2008): Guidance for Industry — Diagnostic Ultrasound Transducers
    - AIUM (2020): Statement on Thermal and Mechanical Biological Effects
    - IEC 60601-2-37: Medical Ultrasonic Equipment
    """

    def __init__(self):
        self.violations = []

    def check_intensity(self, ispta_mw_cm2):
        """
        Validate ISPTA against FDA diagnostic limit.
        
        Args:
            ispta_mw_cm2: Spatial-peak temporal-average intensity (mW/cm²)
            
        Raises:
            SafetyViolation if exceeds 720 mW/cm²
        """
        if ispta_mw_cm2 < 0:
            raise SafetyViolation(f"Negative intensity: {ispta_mw_cm2}")
        if ispta_mw_cm2 > ISPTA_MAX:
            raise SafetyViolation(
                f"ISPTA {ispta_mw_cm2:.1f} mW/cm² exceeds FDA limit {ISPTA_MAX} mW/cm²"
            )
        return True

    def check_frequency(self, freq_hz):
        """
        Validate carrier frequency within tFUS range.
        
        Args:
            freq_hz: Carrier frequency in Hz
            
        Raises:
            SafetyViolation if outside [250 kHz, 700 kHz]
        """
        if freq_hz < US_FREQ_MIN or freq_hz > US_FREQ_MAX:
            raise SafetyViolation(
                f"Frequency {freq_hz/1e3:.0f} kHz outside tFUS range "
                f"[{US_FREQ_MIN/1e3:.0f}, {US_FREQ_MAX/1e3:.0f}] kHz"
            )
        return True

    def check_modulation(self, mod_freq_hz):
        """
        Validate modulation frequency.
        
        Args:
            mod_freq_hz: Modulation frequency in Hz
        """
        if mod_freq_hz < MOD_FREQ_MIN or mod_freq_hz > MOD_FREQ_MAX:
            raise SafetyViolation(
                f"Modulation frequency {mod_freq_hz:.0f} Hz outside range "
                f"[{MOD_FREQ_MIN:.0f}, {MOD_FREQ_MAX:.0f}] Hz"
            )
        return True

    def check_thermal(self, delta_T):
        """
        Validate tissue temperature rise against AIUM limit.
        
        Args:
            delta_T: Temperature rise in °C
        """
        if delta_T > DELTA_T_MAX:
            raise SafetyViolation(
                f"ΔT {delta_T:.3f}°C exceeds AIUM cranial limit {DELTA_T_MAX}°C"
            )
        return True

    def check_session_duration(self, duration_sec):
        """
        Validate total session duration.
        """
        if duration_sec > SESSION_DURATION_MAX:
            raise SafetyViolation(
                f"Session duration {duration_sec:.0f}s exceeds maximum {SESSION_DURATION_MAX:.0f}s"
            )
        return True

    def check_all(self, intensity, freq, mod_freq, delta_T, duration):
        """
        Run all safety checks simultaneously.
        
        Returns:
            dict: Results of each check
        """
        results = {}
        checks = [
            ("intensity", lambda: self.check_intensity(intensity)),
            ("frequency", lambda: self.check_frequency(freq)),
            ("modulation", lambda: self.check_modulation(mod_freq)),
            ("thermal", lambda: self.check_thermal(delta_T)),
            ("duration", lambda: self.check_session_duration(duration)),
        ]
        
        for name, check_fn in checks:
            try:
                check_fn()
                results[name] = "PASS"
            except SafetyViolation as e:
                results[name] = f"FAIL: {str(e)}"
        
        return results
