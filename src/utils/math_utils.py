"""
NATE vΞ⁷·₁ — Math Utility Functions

Common mathematical operations used across the NATE framework.
"""

import numpy as np
from scipy.special import erf


def wkb_tunneling(V, E, m, x_grid):
    """
    Compute WKB tunneling transmission coefficient.
    
    T = exp(-2 · ∫√(2m(V(x)-E)/ℏ²) dx)
    
    ALWAYS produces T ∈ [0, 1] by construction.
    
    Args:
        V: Potential barrier array (same shape as x_grid)
        E: Particle energy (scalar)
        m: Effective mass (scalar)
        x_grid: Position grid (for integration)
        
    Returns:
        T: Transmission coefficient in [0, 1]
    """
    hbar = 1.0546e-34  # J·s
    
    # Classical turning points
    classically_forbidden = V > E
    if not np.any(classically_forbidden):
        return 1.0  # No barrier — full transmission
    
    # Integrate through forbidden region
    integrand = np.sqrt(np.maximum(2 * m * (V[classically_forbidden] - E) / hbar**2, 0))
    dx = np.diff(x_grid[classically_forbidden])
    integral = np.sum(0.5 * (integrand[:-1] + integrand[1:]) * dx)
    
    T = np.exp(-2 * integral)
    return float(np.clip(T, 0.0, 1.0))


def phase_locking_value(phase1, phase2):
    """
    Compute Phase Locking Value (PLV) between two phase time series.
    
    PLV = |1/N · Σ exp(i(φ₁ - φ₂))|
    
    Args:
        phase1: Phase time series (N,)
        phase2: Phase time series (N,)
        
    Returns:
        plv: Value in [0, 1] (1 = perfect phase locking)
    """
    phase_diff = phase1 - phase2
    plv = np.abs(np.mean(np.exp(1j * phase_diff)))
    return float(plv)


def coherence_coefficient(sig1, sig2, fs, nperseg=256):
    """
    Compute magnitude-squared coherence between two signals.
    
    Args:
        sig1, sig2: Signal arrays (same length)
        fs: Sampling frequency (Hz)
        nperseg: Segment length for Welch's method
        
    Returns:
        freqs: Frequency array
        Cxy: Coherence array [0, 1]
    """
    from scipy import signal
    freqs, Pxy = signal.cohere(sig1, sig2, fs=fs, nperseg=nperseg)
    return freqs, Pxy


def lyapunov_exponent_1d(f, x0, dt, n_steps=10000, transient=1000):
    """
    Estimate the largest Lyapunov exponent for a 1D map.
    
    Args:
        f: Function f(x) mapping state to next state
        x0: Initial condition
        dt: Time step
        n_steps: Total integration steps
        transient: Steps to skip (transient removal)
        
    Returns:
        lambda_1: Estimated largest Lyapunov exponent
    """
    x = x0
    lyap_sum = 0.0
    
    for i in range(n_steps):
        x_new = f(x)
        df = (x_new - x)
        if abs(x) > 1e-15:
            lyap_sum += np.log(abs(df / x))
        x = x_new
    
    if n_steps > transient:
        lambda_1 = lyap_sum / ((n_steps - transient) * dt)
    else:
        lambda_1 = lyap_sum / (n_steps * dt)
    
    return float(lambda_1)


def information_entropy(probabilities):
    """
    Compute Shannon entropy H = -Σ p·log2(p).
    
    Args:
        probabilities: Probability array (must sum to ~1)
        
    Returns:
        H: Entropy in bits
    """
    p = np.asarray(probabilities)
    p = p[p > 0]  # Remove zero probabilities
    return float(-np.sum(p * np.log2(p)))


def fisher_information(probabilities, theta_derivative):
    """
    Compute Fisher information I(θ) = Σ (dp/dθ)² / p.
    
    Args:
        probabilities: Probability distribution p(x|θ)
        theta_derivative: Derivative dp/dθ
        
    Returns:
        I: Fisher information (scalar)
    """
    p = np.asarray(probabilities)
    dp = np.asarray(theta_derivative)
    mask = p > 1e-15
    return float(np.sum(dp[mask] ** 2 / p[mask]))
