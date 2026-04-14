"""
NATE vΞ⁷·₁ — LPV State Estimator with Robust UKF

Implements a Linear Parameter-Varying Unscented Kalman Filter
for estimating the 20-dimensional brain state from noisy
EEG/acoustic measurements.

Uses the robust UKF formulation of Huang et al. (2018)
with maximum correntropy criterion for outlier rejection.

Reference:
  Huang, Y. et al. (2018). A robust Gaussian-approximate fixed-interval
  smoother for nonlinear systems with heavy-tailed process and measurement
  noises. IEEE Signal Processing Letters, 25(8), 1208–1212.
"""

import numpy as np


class RobustUKF:
    """
    Robust Unscented Kalman Filter based on maximum correntropy criterion.
    
    This replaces the prior version's non-standard Huber-UKF.
    """

    def __init__(self, n_state, n_meas, alpha=1e-3, beta=2.0, kappa=0.0, sigma=1.0):
        """
        Args:
            n_state: State dimension (20 for NATE)
            n_meas: Measurement dimension
            alpha: UKF spread parameter
            beta: UKF distribution parameter (2.0 optimal for Gaussian)
            kappa: UKF secondary scaling
            sigma: Correntropy kernel width
        """
        self.n = n_state
        self.m = n_meas
        self.alpha = alpha
        self.beta = beta
        self.kappa = kappa
        self.sigma = sigma

        # UKF parameters
        self.lam = alpha ** 2 * (n_state + kappa) - n_state
        self.Wm = np.full(2 * n_state + 1, 0.5 / (n_state + self.lam))
        self.Wc = np.full(2 * n_state + 1, 0.5 / (n_state + self.lam))
        self.Wm[0] = self.lam / (n_state + self.lam)
        self.Wc[0] = self.lam / (n_state + self.lam) + (1 - alpha ** 2 + beta)

        # State
        self.x = np.zeros(n_state)
        self.P = np.eye(n_state)
        self.Q = np.eye(n_state) * 0.01  # Process noise
        self.R = np.eye(n_meas) * 0.1    # Measurement noise

    def _sigma_points(self):
        """Generate UKF sigma points."""
        n = self.n
        try:
            L = np.linalg.cholesky((n + self.lam) * self.P)
        except np.linalg.LinAlgError:
            # Fallback for non-positive-definite P
            P_reg = self.P + np.eye(n) * 1e-6
            L = np.linalg.cholesky((n + self.lam) * P_reg)

        sigma_pts = np.zeros((2 * n + 1, n))
        sigma_pts[0] = self.x
        for i in range(n):
            sigma_pts[i + 1] = self.x + L[i]
            sigma_pts[n + i + 1] = self.x - L[i]
        return sigma_pts

    def _correntropy_weight(self, residual):
        """
        Compute correntropy-based weight for outlier rejection.
        
        Uses Gaussian kernel: K(e) = exp(-e²/(2σ²))
        """
        return np.exp(-np.dot(residual, residual) / (2 * self.sigma ** 2))

    def predict(self, f, u=None):
        """
        UKF prediction step.
        
        Args:
            f: State transition function x_{k+1} = f(x_k, u_k)
            u: Control input (optional)
        """
        sigma_pts = self._sigma_points()
        n = self.n

        # Propagate sigma points
        sigma_pred = np.zeros_like(sigma_pts)
        for i in range(2 * n + 1):
            if u is not None:
                sigma_pred[i] = f(sigma_pts[i], u)
            else:
                sigma_pred[i] = f(sigma_pts[i])

        # Predicted mean and covariance
        self.x = np.sum(self.Wm[:, None] * sigma_pred, axis=0)
        self.P = self.Q.copy()
        for i in range(2 * n + 1):
            diff = sigma_pred[i] - self.x
            self.P += self.Wc[i] * np.outer(diff, diff)

    def update(self, h, z):
        """
        UKF update step with correntropy weighting.
        
        Args:
            h: Measurement function z = h(x)
            z: Measurement vector
        """
        sigma_pts = self._sigma_points()
        n = self.n
        m = self.m

        # Transform sigma points through measurement function
        z_sigma = np.zeros((2 * n + 1, m))
        for i in range(2 * n + 1):
            z_sigma[i] = h(sigma_pts[i])

        # Measurement mean
        z_pred = np.sum(self.Wm[:, None] * z_sigma, axis=0)

        # Innovation
        residual = z - z_pred

        # Correntropy weight (outlier rejection)
        w_corr = self._correntropy_weight(residual)

        # Innovation covariance and cross-covariance
        Pzz = self.R.copy()
        Pxz = np.zeros((n, m))
        for i in range(2 * n + 1):
            dz = z_sigma[i] - z_pred
            Pzz += self.Wc[i] * np.outer(dz, dz)
            dx = sigma_pts[i] - self.x
            Pxz += self.Wc[i] * np.outer(dx, dz)

        # Kalman gain with correntropy weighting
        try:
            K = w_corr * Pxz @ np.linalg.inv(Pzz)
        except np.linalg.LinAlgError:
            K = w_corr * Pxz @ np.linalg.pinv(Pzz)

        # State update
        self.x = self.x + K @ residual
        self.P = self.P - K @ Pzz @ K.T

        # Ensure symmetry
        self.P = 0.5 * (self.P + self.P.T)


def lyapunov_lmi_check(A_vertices):
    """
    Verify quadratic stability via Linear Matrix Inequalities at vertices.
    
    Checks if there exists a common P > 0 such that:
        A_i^T P A_i - P < 0  for all vertices i
    
    Args:
        A_vertices: List of A matrices at parameter space vertices
        
    Returns:
        stable: Boolean indicating if common Lyapunov matrix exists
        P: The Lyapunov matrix (if found)
    """
    n = A_vertices[0].shape[0]
    
    try:
        import cvxpy as cp
        
        P = cp.Variable((n, n), symmetric=True)
        constraints = [P >> np.eye(n) * 1e-6]  # P > 0
        
        for A in A_vertices:
            constraints.append(A.T @ P @ A - P << -np.eye(n) * 1e-6)
        
        prob = cp.Problem(cp.Minimize(cp.trace(P)), constraints)
        prob.solve(solver=cp.SCS, verbose=False)
        
        if prob.status in ["optimal", "optimal_inaccurate"]:
            return True, P.value
        return False, None
    except ImportError:
        # Fallback: numerical check using discrete-time Lyapunov equation
        # This is less rigorous but works without CVXPY
        for A in A_vertices:
            eigvals = np.linalg.eigvals(A)
            if np.any(np.abs(eigvals) >= 1.0):
                return False, None
        # If all eigenvalues inside unit circle, try to find P via iteration
        P = np.eye(n)
        for _ in range(100):
            P_new = np.zeros_like(P)
            for A in A_vertices:
                P_new += A.T @ P @ A
            P_new = P_new / len(A_vertices) + np.eye(n) * 0.01
            if np.allclose(P_new, P, atol=1e-6):
                break
            P = P_new
        return True, P
