"""
NATE vΞ⁷·₁ — Multi-Taper Spectral Estimation

Implements spectral band power estimation using Slepian (DPSS) tapers.
Uses the Thomson (1982) multi-taper method for optimal concentration
in both time and frequency domains.

Parameters:
  - K = 7 Slepian tapers
  - Epoch: 500 ms
  - Overlap: 250 ms (50%)
  - Sampling rate: 1000 Hz

NOTE: For simulation and research purposes only.
"""

import numpy as np
from scipy import signal


def dpss_tapers(N, K, NW=3.5):
    """
    Compute Discrete Prolate Spheroidal Sequences (Slepian tapers).
    
    Args:
        N: Number of samples in the epoch
        K: Number of tapers (typically 2*NW - 1)
        NW: Time-bandwidth product (default 3.5)
        
    Returns:
        tapers: (K, N) array of taper functions
        eigenvalues: (K,) concentration ratios
    """
    tapers, eigenvalues = signal.windows.dpss(N, NW, K, return_ratios=True)
    return tapers, eigenvalues


def multitaper_psd(data, fs, K=7, NW=3.5):
    """
    Compute power spectral density using multi-taper method.
    
    Args:
        data: 1-D signal array (N samples)
        fs: Sampling frequency (Hz)
        K: Number of Slepian tapers
        NW: Time-bandwidth product
        
    Returns:
        freqs: (N_freq,) frequency axis
        psd: (N_freq,) power spectral density
    """
    N = len(data)
    tapers, eigvals = dpss_tapers(N, K, NW)
    
    # Compute tapered FFTs
    Nfft = max(N, 512)
    freqs = np.fft.rfftfreq(Nfft, 1.0 / fs)
    psd = np.zeros(len(freqs))
    
    for k in range(K):
        tapered = data * tapers[k]
        ft = np.fft.rfft(tapered, n=Nfft)
        psd += np.abs(ft) ** 2 * eigvals[k]
    
    psd /= (fs * np.sum(eigvals))
    return freqs, psd


def band_power(freqs, psd, band_low, band_high):
    """
    Compute integrated power within a frequency band.
    
    Args:
        freqs: Frequency axis from PSD
        psd: Power spectral density
        band_low: Lower band edge (Hz)
        band_high: Upper band edge (Hz)
        
    Returns:
        power: Band-integrated power (mean PSD in band)
    """
    idx = np.logical_and(freqs >= band_low, freqs <= band_high)
    if not np.any(idx):
        return 0.0
    return float(np.mean(psd[idx]))


def compute_spectral_features(data, fs, channels=None):
    """
    Compute multi-taper spectral features for all canonical bands.
    
    Args:
        data: 2-D array (n_channels, n_samples)
        fs: Sampling frequency (Hz)
        channels: Optional list of channel names
        
    Returns:
        features: dict mapping band_name -> power (or per-channel powers)
    """
    bands = {
        "delta": (0.5, 4.0),
        "theta": (4.0, 8.0),
        "alpha": (8.0, 13.0),
        "beta":  (13.0, 30.0),
        "gamma": (30.0, 100.0),
    }
    
    n_channels, n_samples = data.shape
    features = {}
    
    for ch_idx in range(n_channels):
        ch_features = {}
        for band_name, (low, high) in bands.items():
            freqs, psd = multitaper_psd(data[ch_idx], fs)
            ch_features[band_name] = band_power(freqs, psd, low, high)
        
        label = channels[ch_idx] if channels else f"ch_{ch_idx}"
        features[label] = ch_features
    
    return features
