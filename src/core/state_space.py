"""
NATE vΞ⁷·₁ — 20-Dimensional State Space Model

Implements the unified state vector for the NATE framework:
  x(t) = [x_EEG(t) | x_ERP(t) | x_ACO(t) | x_CPL(t)] ∈ ℝ²⁰

Subspaces:
  x_EEG (8-D): Multi-taper spectral band powers (PCA-reduced)
  x_ERP (4-D): Event-related potential features
  x_ACO (4-D): Acoustic stimulation parameters
  x_CPL (4-D): Brain-acoustic coupling state

NOTE: This is a SIMULATION MODEL for a SPECULATIVE framework.
      Not validated for any clinical or therapeutic application.
"""

import numpy as np
from .constants import (
    DIM_EEG, DIM_ERP, DIM_ACO, DIM_CPL, DIM_STATE,
    FREQ_BANDS, LAT_LOOP,
)


class NATEStateSpace:
    """
    20-dimensional state space for the NATE framework.
    
    State vector layout:
      [0:8]   x_EEG  — EEG spectral features (PCA-reduced)
      [8:12]  x_ERP  — ERP amplitude/latency features
      [12:16] x_ACO  — Acoustic parameters [I, f, phi, mod_freq]
      [16:20] x_CPL  — Coupling state variables
    """

    def __init__(self, dt=0.04):
        """
        Args:
            dt: Time step in seconds (default: 40ms = closed-loop latency)
        """
        self.dt = dt
        self.dim = DIM_STATE
        self.state = np.zeros(DIM_STATE)

        # Subspace dimension tracking
        self._slices = {
            "eeg": slice(0, DIM_EEG),
            "erp": slice(DIM_EEG, DIM_EEG + DIM_ERP),
            "aco": slice(DIM_EEG + DIM_ERP, DIM_EEG + DIM_ERP + DIM_ACO),
            "cpl": slice(DIM_EEG + DIM_ERP + DIM_ACO, DIM_STATE),
        }

    @property
    def x_eeg(self):
        """EEG spectral subspace (8-D)."""
        return self.state[self._slices["eeg"]]

    @property
    def x_erp(self):
        """ERP feature subspace (4-D)."""
        return self.state[self._slices["erp"]]

    @property
    def x_aco(self):
        """Acoustic parameter subspace (4-D): [intensity, frequency, phase, mod_freq]."""
        return self.state[self._slices["aco"]]

    @property
    def x_cpl(self):
        """Coupling state subspace (4-D)."""
        return self.state[self._slices["cpl"]]

    def set_subspace(self, name, values):
        """
        Set a subspace by name.
        
        Args:
            name: One of 'eeg', 'erp', 'aco', 'cpl'
            values: Array of appropriate dimensionality
        """
        if name not in self._slices:
            raise ValueError(f"Unknown subspace: {name}. Must be one of {list(self._slices.keys())}")
        values = np.asarray(values)
        sl = self._slices[name]
        if values.shape != (sl.stop - sl.start,):
            raise ValueError(
                f"Dimension mismatch for '{name}': expected {sl.stop - sl.start}, got {values.shape[0]}"
            )
        self.state[sl] = values

    def step(self, control_input=None):
        """
        Advance state by one time step using a simplified linear dynamics model.
        
        This is a HYPOTHETICAL model for simulation purposes only.
        Real brain dynamics are nonlinear, stochastic, and far more complex.
        
        Args:
            control_input: Optional 4-D acoustic control vector
            
        Returns:
            Updated state vector
        """
        # Simplified state transition (identity + small perturbation)
        # In a real implementation, this would use the LPV-UKF state estimate
        noise = np.random.randn(DIM_STATE) * 0.01
        self.state = self.state + noise * np.sqrt(self.dt)
        
        # Apply acoustic coupling (simplified linear mixing)
        if control_input is not None:
            u = np.asarray(control_input)
            if u.shape[0] != DIM_ACO:
                raise ValueError(f"Control input must be {DIM_ACO}-D, got {u.shape[0]}")
            # Coupling: acoustic parameters influence coupling state
            coupling_strength = 0.1 * self.dt
            self.x_cpl[:] += coupling_strength * u
        
        return self.state.copy()

    def get_full_state(self):
        """Return a copy of the full 20-D state vector."""
        return self.state.copy()

    def state_dict(self):
        """Return state as a dictionary with subspace labels."""
        return {
            "eeg": self.x_eeg.copy(),
            "erp": self.x_erp.copy(),
            "aco": self.x_aco.copy(),
            "cpl": self.x_cpl.copy(),
        }

    @staticmethod
    def state_distance(s1, s2):
        """
        Euclidean distance between two state vectors.
        
        Args:
            s1, s2: State vectors (20-D arrays)
            
        Returns:
            Euclidean distance (float)
        """
        s1 = np.asarray(s1)
        s2 = np.asarray(s2)
        if s1.shape != s2.shape or s1.shape[0] != DIM_STATE:
            raise ValueError(f"Both states must be {DIM_STATE}-D vectors")
        return float(np.linalg.norm(s1 - s2))
