"""
NATE vΞ⁷·₁ — Core Physical and Physiological Constants

All values sourced from peer-reviewed literature.
Units are SI unless otherwise noted.

Sources:
  - FDA (2008): Guidance for Industry — Diagnostic Ultrasound Transducers
  - AIUM (2020): Statement on Thermal and Mechanical Biological Effects
  - Hasgall et al. (2015): IT'IS Database for Thermal and EM Parameters
  - IFCN: International Federation of Clinical Neurophysiology
"""

import numpy as np


# ══════════════════════════════════════════════
# Physical Constants
# ══════════════════════════════════════════════
PLANCK_CONSTANT = 6.62607015e-34       # J·s
BOLTZMANN_CONSTANT = 1.380649e-23      # J/K
SPEED_OF_SOUND_WATER = 1480.0          # m/s at ~37°C
SPEED_OF_SOUND_BRAIN = 1550.0          # m/s (average brain tissue)
ABSORPTION_COEFF_BRAIN = 0.5           # dB/(cm·MHz) average brain tissue

# ══════════════════════════════════════════════
# Thermal Parameters (Brain Tissue)
# ══════════════════════════════════════════════
BRAIN_DENSITY = 1040.0                 # kg/m³
BRAIN_SPECIFIC_HEAT = 3600.0           # J/(kg·K)
BRAIN_THERMAL_CONDUCTIVITY = 0.5       # W/(m·K)
BRAIN_BLOOD_PERFUSION_RATE = 0.8e-3    # 1/s (~0.8 mL/min/g)
ARTERIAL_BLOOD_TEMP = 310.15           # K (37°C)
METABOLIC_HEAT_GEN = 10000.0           # W/m³ average brain metabolism

# ══════════════════════════════════════════════
# Regulatory Safety Limits (FDA / AIUM / IEC)
# ══════════════════════════════════════════════
ISPTA_MAX = 720.0                      # mW/cm² (FDA 2008, diagnostic)
ISPPA_MAX = 190.0                      # W/cm² (IEC 60601-2-37)
MI_MAX = 1.9                           # Mechanical Index (FDA 2008)
TI_CRANIAL_MAX = 6.0                   # Thermal Index, cranial (AIUM 2020)
DELTA_T_MAX = 1.0                      # °C max tissue temperature rise
SESSION_DURATION_MAX = 1800.0          # seconds (30 min)
DUTY_CYCLE_MAX = 0.5                   # 50% pulsed mode

# ══════════════════════════════════════════════
# EEG Acquisition Parameters
# ══════════════════════════════════════════════
EEG_MIN_CHANNELS = 64
EEG_SAMPLING_RATE = 1000               # Hz
EEG_EPOCH_SEC = 0.5
EEG_EPOCH_OVERLAP_SEC = 0.25
SLEPIAN_K = 7                          # number of tapers
ERP_P300_MIN_TRIALS = 20
ERP_P300_MIN_CHANNELS = 32
MMN_STANDARD_TRIALS = 200
MMN_DEVIANT_TRIALS = 50
MMN_LATENCY_WINDOW = (0.150, 0.250)    # seconds

# ══════════════════════════════════════════════
# IFCN Frequency Bands (Hz)
# ══════════════════════════════════════════════
FREQ_BANDS = {
    "delta": (0.5, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta":  (13.0, 30.0),
    "gamma": (30.0, 100.0),
}

# ══════════════════════════════════════════════
# Electrode Clusters
# ══════════════════════════════════════════════
ELECTRODE_CLUSTERS = {
    "frontal": ["F3", "F4", "Fz"],
    "central": ["C3", "C4", "Cz"],
    "parietal": ["P3", "P4", "Pz"],
    "temporal": ["T7", "T8"],
}

# ══════════════════════════════════════════════
# Ultrasonic Parameters
# ══════════════════════════════════════════════
US_FREQ_MIN = 250e3                    # Hz (250 kHz)
US_FREQ_MAX = 700e3                    # Hz (700 kHz)
US_MOD_FREQ_MIN = 1.0                  # Hz
US_MOD_FREQ_MAX = 1000.0               # Hz

# ══════════════════════════════════════════════
# State Space Dimensions
# ══════════════════════════════════════════════
DIM_EEG = 8
DIM_ERP = 4
DIM_ACO = 4
DIM_CPL = 4
DIM_STATE = DIM_EEG + DIM_ERP + DIM_ACO + DIM_CPL  # 20

# ══════════════════════════════════════════════
# Latency Targets (seconds)
# ══════════════════════════════════════════════
LAT_L1 = 0.005     # Acquisition
LAT_L2 = 0.020     # Feature extraction
LAT_L3 = 0.010     # State estimation
LAT_L4 = 0.005     # Acoustic control
LAT_LOOP = 0.040   # Total closed-loop
