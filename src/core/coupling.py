"""
NATE vΞ⁷·₁ — Stuart-Landau Oscillator Coupling (Corrected)

Implements coupled Stuart-Landau oscillators in polar coordinates,
preserving SO(2) rotational symmetry as required by the audit correction.

The corrected equations:
    dr_i/dt = (α_i - r_i²)·r_i + Σ_j K_ij·r_j·cos(θ_j - θ_i)
    dθ_i/dt = ω_i + Σ_j K_ij·(r_j/r_i)·sin(θ_j - θ_i)

Key properties:
    - Coupling depends ONLY on phase differences → SO(2) symmetry preserved
    - Reduces to Kuramoto model for fixed amplitudes (r → 1)
    - Suitable for modeling coupled neural oscillators

Reference:
    Acebron, J.A. et al. (2005). The Kuramoto model. Reviews of Modern Physics, 77(1).
"""

import numpy as np
from scipy.integrate import solve_ivp


class StuartLandauNetwork:
    """
    Network of coupled Stuart-Landau oscillators in polar coordinates.
    """

    def __init__(self, n_oscillators, alpha=None, omega=None, K=None):
        """
        Args:
            n_oscillators: Number of oscillators
            alpha: Bifurcation parameters (n,) — positive = limit cycle
            omega: Natural frequencies (n,) in rad/s
            K: Coupling matrix (n, n) — K[i,j] = coupling from j to i
        """
        self.n = n_oscillators

        if alpha is None:
            alpha = np.ones(n_oscillators) * 1.0  # All in limit cycle regime
        self.alpha = np.asarray(alpha)

        if omega is None:
            # Neural frequency bands: theta (6 Hz), alpha (10 Hz)
            omega = np.linspace(2 * np.pi * 4, 2 * np.pi * 12, n_oscillators)
        self.omega = np.asarray(omega)

        if K is None:
            K = np.zeros((n_oscillators, n_oscillators))
        self.K = np.asarray(K)

    def _derivatives(self, t, y):
        """
        Compute time derivatives in polar coordinates.
        
        State vector: y = [r_1, ..., r_n, θ_1, ..., θ_n]
        """
        r = y[:self.n]
        theta = y[self.n:]

        drdt = np.zeros(self.n)
        dthetadt = np.zeros(self.n)

        for i in range(self.n):
            # Amplitude dynamics
            drdt[i] = (self.alpha[i] - r[i] ** 2) * r[i]

            # Phase dynamics (natural frequency)
            dthetadt[i] = self.omega[i]

            # Coupling terms (SO(2)-symmetric: depend only on phase differences)
            for j in range(self.n):
                if i == j or self.K[i, j] == 0:
                    continue
                dtheta = theta[j] - theta[i]
                cos_dtheta = np.cos(dtheta)
                sin_dtheta = np.sin(dtheta)

                # Amplitude coupling
                drdt[i] += self.K[i, j] * r[j] * cos_dtheta

                # Phase coupling (with amplitude normalization)
                if r[i] > 1e-10:
                    dthetadt[i] += self.K[i, j] * (r[j] / r[i]) * sin_dtheta

        return np.concatenate([drdt, dthetadt])

    def simulate(self, t_span, y0=None, max_step=0.01):
        """
        Integrate the coupled oscillator system.
        
        Args:
            t_span: (t_start, t_end) in seconds
            y0: Initial state (2n,) — [r, theta]
            max_step: Maximum integration step size
            
        Returns:
            t: Time array
            r: Amplitudes (n, n_t)
            theta: Phases (n, n_t)
        """
        if y0 is None:
            y0 = np.zeros(2 * self.n)
            y0[:self.n] = np.sqrt(self.alpha)  # Start at limit cycle amplitude
            y0[self.n:] = np.random.uniform(0, 2 * np.pi, self.n)

        sol = solve_ivp(
            self._derivatives, t_span, y0,
            method="RK45",
            max_step=max_step,
            dense_output=True,
        )

        r = sol.y[:self.n]
        theta = sol.y[self.n:]
        return sol.t, r, theta

    def order_parameter(self, theta):
        """
        Compute Kuramoto order parameter r = |1/N · Σ exp(iθ)|.
        
        Args:
            theta: Phase array (n, n_t) or (n,)
            
        Returns:
            r: Order parameter magnitude in [0, 1]
        """
        if theta.ndim == 1:
            z = np.mean(np.exp(1j * theta))
            return np.abs(z)
        else:
            return np.abs(np.mean(np.exp(1j * theta), axis=0))

    def set_coupling(self, K):
        """Set the coupling matrix."""
        self.K = np.asarray(K)
