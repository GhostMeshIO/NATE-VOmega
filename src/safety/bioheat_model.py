"""
NATE vΞ⁷·₁ — Pennes Bioheat Equation Solver

Solves the thermal model for ultrasonic exposure to brain tissue using
the full Pennes bioheat equation with blood perfusion term:

    ρ·c·(∂T/∂t) = ∇·(k·∇T) + ω_b·ρ_b·c_b·(T_a - T) + Q_met + Q_ac

This corrects the prior version's omission of the perfusion cooling term,
which was identified as a CRITICAL safety deficiency in the external audit.

Sources:
  - Pennes, H.H. (1948). Analysis of tissue and arterial blood temperatures
  - Hasgall et al. (2015). IT'IS Database v3.0
  - AIUM (2020). Statement on Thermal Biological Effects

NOTE: Simulation model for research only. NOT for clinical use.
"""

import numpy as np
from .constants import (
    BRAIN_DENSITY, BRAIN_SPECIFIC_HEAT, BRAIN_THERMAL_CONDUCTIVITY,
    BRAIN_BLOOD_PERFUSION_RATE, ARTERIAL_BLOOD_TEMP,
    METABOLIC_HEAT_GEN, DELTA_T_MAX,
)


class PennesBioheatSolver:
    """
    1D Pennes bioheat equation solver for ultrasound exposure.
    
    Models the temperature distribution along the acoustic beam axis
    through brain tissue, accounting for:
    - Thermal conduction (k·∇²T)
    - Blood perfusion cooling (ω_b·ρ_b·c_b·(T_a - T))
    - Metabolic heat generation (Q_met)
    - Acoustic absorption (Q_ac)
    """

    def __init__(
        self,
        length=0.04,         # 4 cm tissue domain
        dx=0.001,            # 1 mm spatial resolution
        dt=0.1,              # 0.1 s time step
    ):
        self.L = length
        self.dx = dx
        self.dt = dt
        self.nx = int(length / dx) + 1
        self.x = np.linspace(0, length, self.nx)

        # Tissue properties (from constants)
        self.rho = BRAIN_DENSITY
        self.c = BRAIN_SPECIFIC_HEAT
        self.k = BRAIN_THERMAL_CONDUCTIVITY
        self.omega_b = BRAIN_BLOOD_PERFUSION_RATE
        self.T_a = ARTERIAL_BLOOD_TEMP
        self.Q_met = METABOLIC_HEAT_GEN

        # Blood properties
        self.rho_b = 1060.0       # kg/m³
        self.c_b = 3770.0         # J/(kg·K)

        # State
        self.T = np.ones(self.nx) * ARTERIAL_BLOOD_TEMP  # Initial = body temp

    def _acoustic_heating(self, ispta_mw_cm2, freq_hz, beam_center_idx):
        """
        Compute volumetric acoustic power absorption Q_ac (W/m³).
        
        Args:
            ispta_mw_cm2: Spatial-peak temporal-average intensity (mW/cm²)
            freq_hz: Ultrasonic frequency (Hz)
            beam_center_idx: Index of beam focal center
            
        Returns:
            Q_ac: (nx,) array of volumetric heating (W/m³)
        """
        # Convert mW/cm² to W/m²
        I = ispta_mw_cm2 * 1e-3 * 1e4  # mW/cm² -> W/m²
        
        # Absorption coefficient: α = 0.5 dB/(cm·MHz) for brain tissue
        alpha_db_cm_mhz = 0.5
        alpha_npm = alpha_db_cm_mhz * (freq_hz / 1e6) * 100 / 8.686  # Np/m
        
        # Gaussian beam profile (FWHM ≈ 2mm at focus)
        sigma = 0.002  # 2mm beam width
        beam_profile = np.exp(-0.5 * ((self.x - self.x[beam_center_idx]) / sigma) ** 2)
        
        Q_ac = 2 * alpha_npm * I * beam_profile
        return Q_ac

    def step(self, ispta_mw_cm2=0.0, freq_hz=500e3):
        """
        Advance temperature by one time step using explicit finite differences.
        
        Args:
            ispta_mw_cm2: Current acoustic intensity (mW/cm²)
            freq_hz: Current acoustic frequency (Hz)
            
        Returns:
            T: Updated temperature array
            max_delta_T: Maximum temperature rise above baseline
        """
        T = self.T.copy()
        r = self.k * self.dt / (self.rho * self.c * self.dx ** 2)

        # Stability check for explicit scheme
        if r > 0.5:
            raise ValueError(f"CFL condition violated: r = {r:.4f} > 0.5. Reduce dt or increase dx.")

        # Compute acoustic heating at beam center
        Q_ac = self._acoustic_heating(ispta_mw_cm2, freq_hz, self.nx // 2)

        # Perfusion coefficient
        perf_coeff = self.omega_b * self.rho_b * self.c_b / (self.rho * self.c)

        # Finite difference update (interior points)
        T_new = T.copy()
        for i in range(1, self.nx - 1):
            conduction = r * (T[i + 1] - 2 * T[i] + T[i - 1])
            perfusion = perf_coeff * self.dt * (self.T_a - T[i])
            metabolic = self.Q_met * self.dt / (self.rho * self.c)
            acoustic = Q_ac[i] * self.dt / (self.rho * self.c)
            T_new[i] = T[i] + conduction + perfusion + metabolic + acoustic

        # Boundary conditions: fixed at body temperature
        T_new[0] = self.T_a
        T_new[-1] = self.T_a

        self.T = T_new
        max_dT = float(np.max(self.T - self.T_a))
        return self.T.copy(), max_dT

    def simulate(self, ispta_mw_cm2, freq_hz, duration_sec):
        """
        Run full simulation for a given exposure duration.
        
        Args:
            ispta_mw_cm2: Acoustic intensity (mW/cm²)
            freq_hz: Frequency (Hz)
            duration_sec: Total simulation time (seconds)
            
        Returns:
            times: (n_steps,) array
            temperatures: (n_steps, nx) array
            max_delta_T_history: (n_steps,) array
        """
        n_steps = int(duration_sec / self.dt)
        times = np.zeros(n_steps)
        temperatures = np.zeros((n_steps, self.nx))
        max_dT_history = np.zeros(n_steps)

        for i in range(n_steps):
            T, dT = self.step(ispta_mw_cm2, freq_hz)
            times[i] = i * self.dt
            temperatures[i] = T
            max_dT_history[i] = dT

            # Safety check
            if dT > DELTA_T_MAX:
                print(f"WARNING: ΔT = {dT:.3f}°C exceeds safety limit at t = {times[i]:.1f}s")

        return times, temperatures, max_dT_history
