"""
NATE vΞ⁷·₁ — Dynamic Mode Decomposition with Control (DMDc)

Implements the snapshot-based DMDc formulation of Proctor et al. (2016),
which avoids the normalization pitfalls identified in the external audit.

The corrected pipeline:
  1. Center time series by subtracting temporal mean (NO normalization)
  2. Apply DMDc directly using the Proctor formulation
  3. Scale DMD modes to unit L2 norm (applied to mode shapes only)

Reference:
  Proctor, J.L., Brunton, S.L., & Kutz, J.N. (2016).
  Dynamic mode decomposition with control.
  SIAM Journal on Applied Dynamical Systems, 15(1), 142–161.
"""

import numpy as np


class DMDc:
    """
    Dynamic Mode Decomposition with Control.
    
    Solves: X' = A·X + B·U
    Where:
      X  = state snapshots (n × m-1)
      X' = shifted state snapshots (n × m-1)
      U  = control input snapshots (p × m-1)
    """

    def __init__(self, rank=None):
        """
        Args:
            rank: Truncation rank for SVD (None = full rank)
        """
        self.rank = rank
        self.A_tilde = None  # Reduced Koopman matrix
        self.B_tilde = None  # Reduced input matrix
        self.modes = None    # DMD modes (full space)
        self.eigenvalues = None  # DMD eigenvalues
        self.W = None        # Lifted basis

    def fit(self, X, X_prime, U):
        """
        Compute DMDc from snapshot data.
        
        Args:
            X: State snapshots (n × m)
            X_prime: Shifted state snapshots (n × m)
            U: Control input snapshots (p × m)
            
        Returns:
            self
        """
        # Step 1: Build augmented matrices
        # Omega = [X; U] (augmented state + control)
        Omega = np.vstack([X[:, :-1], U[:, :-1]])  # (n+p) × (m-1)
        Xp = X_prime[:, :-1]                        # n × (m-1)

        # Step 2: SVD of Omega (NOT normalizing — preserves geometric structure)
        r = self.rank if self.rank else min(Omega.shape)
        U_hat, S, Vh = np.linalg.svd(Omega, full_matrices=False)
        U_hat = U_hat[:, :r]
        S_inv = np.diag(1.0 / S[:r])
        Vh = Vh[:r, :]

        # Step 3: Project X_prime onto augmented space
        Xp_tilde = U_hat.T @ Xp  # r × (m-1)

        # Step 4: Extract A_tilde and B_tilde
        n = X.shape[0]
        A_tilde = Xp_tilde @ Vh.T @ S_inv @ U_hat[:n, :].T
        B_tilde = Xp_tilde @ Vh.T @ S_inv @ U_hat[n:, :].T

        self.A_tilde = A_tilde
        self.B_tilde = B_tilde
        self.W = U_hat

        # Step 5: Eigendecomposition of A_tilde
        eigenvalues, W_tilde = np.linalg.eig(A_tilde)

        # Step 6: Compute DMD modes in full space
        Phi = (Xp @ Vh.T @ S_inv @ W_tilde)
        # Scale modes to unit L2 norm (preserves eigenvalue interpretation)
        mode_norms = np.linalg.norm(Phi, axis=0)
        mode_norms[mode_norms == 0] = 1.0
        Phi = Phi / mode_norms

        self.modes = Phi
        self.eigenvalues = eigenvalues

        return self

    def predict(self, x0, U_sequence, n_steps):
        """
        Predict future states using the DMDc model.
        
        Args:
            x0: Initial state vector (n,)
            U_sequence: Control inputs for each step (p × n_steps)
            n_steps: Number of prediction steps
            
        Returns:
            X_pred: Predicted states (n × n_steps)
        """
        if self.A_tilde is None or self.B_tilde is None:
            raise RuntimeError("Model not fitted. Call fit() first.")

        n = x0.shape[0]
        X_pred = np.zeros((n, n_steps))
        x_tilde = self.W[:n, :].T @ x0

        for t in range(n_steps):
            x_tilde = self.A_tilde @ x_tilde + self.B_tilde @ U_sequence[:, t]
            X_pred[:, t] = self.W[:n, :] @ x_tilde

        return X_pred

    def koopman_spectrum(self):
        """
        Return the Koopman eigenvalue spectrum.
        
        Returns:
            eigenvalues: Complex array of DMD eigenvalues
            growth_rates: Real part (growth/decay rate)
            frequencies: Imaginary part / (2π·dt) — oscillation frequency
        """
        if self.eigenvalues is None:
            raise RuntimeError("Model not fitted.")
        growth_rates = np.real(self.eigenvalues)
        frequencies = np.imag(self.eigenvalues) / (2 * np.pi)
        return self.eigenvalues, growth_rates, frequencies
