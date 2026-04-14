# NATE vΞ⁷·₁ — System Architecture

## Overview

The NATE architecture is organized as a four-layer data processing pipeline, with a 20-dimensional state space model as its mathematical core. This document provides a deep-dive into the architectural components, their interfaces, latency budgets, and data flows.

> **Disclaimer**: This architecture describes a HYPOTHETICAL system. No implementation exists. All performance claims are design targets for a speculative framework, not measured values.

---

## 1. Architectural Philosophy

The NATE architecture follows three guiding principles that distinguish it from conventional brain-computer interface (BCI) or neurofeedback systems:

1. **Closed-loop latency dominance**: The system is designed around a total loop latency budget of 40 ms, which constrains every component in the pipeline. This budget is derived from the characteristic timescale of neural oscillations in the theta band (4–8 Hz, period 125–250 ms). The 40 ms budget ensures that the system can complete approximately 3–6 control cycles per theta cycle, enabling meaningful phase-locked modulation.

2. **Safety-first design**: The safety interlock operates at a hardware level, independent of the software control loop. No software failure, including a catastrophic bug in the state estimator or control optimizer, can result in an unsafe acoustic exposure. This architectural principle is non-negotiable and reflects the ethical constraints of any system that delivers energy to brain tissue.

3. **Separation of concerns**: The engineering control architecture (finite state machine, deterministic algorithms, measurable quantities) is strictly separated from the theoretical framework (speculative dynamics, ontological constructs, untestable hypotheses). This separation allows the engineering components to be developed, tested, and validated independently of the theoretical framework's more ambitious claims.

---

## 2. State Space Architecture

### 2.1 Unified State Vector

The core of the NATE architecture is the 20-dimensional state vector:

```
x(t) = [x_EEG(t) | x_ERP(t) | x_ACO(t) | x_CPL(t)] ∈ ℝ²⁰
```

| Subspace | Dimensions | Description | Update Rate |
|----------|-----------|-------------|-------------|
| x_EEG | 8 | Multi-taper spectral band powers (PCA-reduced from 20) | 4 Hz |
| x_ERP | 4 | Event-related potential features (P300 amp, P300 lat, MMN amp, MMN lat) | Event-driven (~0.5 Hz) |
| x_ACO | 4 | Acoustic parameters (intensity, frequency, phase, modulation) | Control loop rate |
| x_CPL | 4 | Brain-acoustic coupling state variables | Control loop rate |

### 2.2 State Space Geometry

The state space is not treated as a flat Euclidean space. The framework hypothesizes that the 20-dimensional state lives on or near a low-dimensional manifold embedded in ℝ²⁰, motivated by the observation that neural dynamics typically exhibit far fewer degrees of freedom than the number of recorded channels would suggest. The intrinsic dimensionality of this manifold is estimated via PCA to be approximately 8–12 for typical EEG recordings, consistent with the dimensionality reduction applied to the EEG subspace.

The distance metric on the state space is defined as a weighted Euclidean norm:

```
d(x₁, x₂) = √(Σᵢ wᵢ·(x₁ᵢ - x₂ᵢ)²)
```

Where the weights wᵢ reflect the relative importance of each subspace for the control objective. These weights are treated as design parameters that can be tuned during the calibration phase.

---

## 3. Four-Layer Pipeline

### 3.1 Layer 1: Acquisition (L1)

**Function**: Raw signal digitization and artifact pre-processing.

**Inputs**:
- 64-channel EEG at 1000 Hz (primary)
- Ultrasonic transducer array feedback (position, intensity, temperature sensors)

**Outputs**:
- Digitized, filtered EEG streams (64 × 1000 Hz)
- Acoustic telemetry (4 × 100 Hz)

**Processing**:
1. Anti-aliasing analog filtering (hardware, 500 Hz cutoff for EEG)
2. 24-bit ADC conversion
3. Notch filter at 50/60 Hz (power line removal)
4. Bandpass filter 0.5–100 Hz (preserves all canonical bands)
5. Common average reference (CAR) re-referencing

**Latency Budget**: < 5 ms (dominated by ADC + CAR computation)

**Critical Requirement**: The 64-channel system must use the international 10–20 extended electrode placement system, with additional electrodes at Oz, Iz, PO3, PO4, PO7, PO8, POz, FT7, FT8, TP7, TP8, CP1, CP2, CP5, CP6, FC1, FC2, FC5, FC6, and AFz for optimal coverage of regions relevant to auditory evoked potentials.

### 3.2 Layer 2: Feature Extraction (L2)

**Function**: Transform raw EEG into compact feature vectors.

**Inputs**: Digitized EEG streams from L1

**Outputs**:
- 8-dimensional spectral feature vector (updated at 4 Hz)
- 4-dimensional ERP feature vector (event-driven)

**Spectral Processing**:
1. Epoch extraction: 500 ms windows with 250 ms overlap (75% Hann taper)
2. Multi-taper spectral estimation: K=7 Slepian (DPSS) tapers, NW=3.5
3. Band power integration for 5 IFCN bands (delta, theta, alpha, beta, gamma)
4. PCA dimensionality reduction: 20 features → 8 components (≥90% variance retained)

**ERP Processing**:
1. Stimulus-locked epoch extraction (−100 to +800 ms relative to stimulus)
2. Baseline correction (−100 to 0 ms pre-stimulus interval)
3. Spatial filtering (Laplacian at Pz for P300, Cz for MMN)
4. Ensemble averaging: minimum 20 trials for P300, 200+50 for MMN
5. Peak detection: maximum amplitude in canonical latency window

**Latency Budget**: < 20 ms (dominated by multi-taper FFT)

### 3.3 Layer 3: State Estimation (L3)

**Function**: Fuse features into a coherent 20-D state estimate with uncertainty.

**Inputs**: Feature vectors from L2, acoustic telemetry from L1

**Outputs**: Full 20-D state estimate x̂(t) with covariance matrix P(t)

**Algorithm**: Robust Unscented Kalman Filter (Huang et al., 2018)
- State transition model: LPV system parameterized by theta/alpha ratio
- Measurement model: linear observation of feature subspaces
- Outlier rejection: maximum correntropy criterion with Gaussian kernel

**Stability Guarantee**: Lyapunov analysis via LMI at parameter space vertices (θ/α ∈ {0.5, 2.25, 4.0}) confirms existence of common quadratic Lyapunov function.

**Latency Budget**: < 10 ms (UKF prediction + update with 41 sigma points in 20-D)

### 3.4 Layer 4: Acoustic Control (L4)

**Function**: Compute optimal acoustic parameters subject to safety constraints.

**Inputs**: State estimate from L3, reference trajectory from operator

**Outputs**: 4-D acoustic parameter vector a = [I, f, φ, f_mod]

**Optimization**:
- Objective: minimize d(x̂, x_ref) subject to safety constraints
- Method: constrained quadratic programming (QP) with ISPTA, MI, TI bounds
- Safety interlock: hardwired hardware check independently of software output

**Latency Budget**: < 5 ms (QP solve in 4-D with 3 inequality constraints)

---

## 4. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      NATE vΞ⁷·₁ Architecture                     │
│                                                                   │
│  ┌──────┐    ┌──────────┐    ┌──────────┐    ┌──────────────┐   │
│  │ L1   │───▶│ L2       │───▶│ L3       │───▶│ L4           │   │
│  │ Acq  │    │ Features │    │ Estimate │    │ Control      │   │
│  │      │    │          │    │          │    │              │   │
│  │64-ch │    │Multi-    │    │Robust   │    │Safety-       │   │
│  │EEG   │    │taper +   │    │UKF      │    │constrained   │   │
│  │1000Hz│    │ERP       │    │LPV      │    │QP optimizer  │   │
│  │      │    │          │    │          │    │              │   │
│  │<5ms  │    │<20ms     │    │<10ms     │    │<5ms         │   │
│  └──┬───┘    └──────────┘    └──────────┘    └──────┬───────┘   │
│     │                                              │            │
│     │         ┌────────────────────────────────────┘            │
│     │         │                                                  │
│     │         ▼                                                  │
│     │    ┌──────────────┐                                        │
│     └───▶│  Ultrasonic  │◀──── HARDWARE SAFETY INTERLOCK ────┐  │
│          │  Transducer  │    (ISPTA, MI, TI, ΔT monitoring)  │  │
│          │  Array       │    Response time: <1 ms             │  │
│          └──────────────┘                                    │  │
│                                                              │  │
│  Total closed-loop latency: < 40 ms                        │  │
│  Independent safety response: < 1 ms ◀─────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Interface Specifications

### 5.1 L1 → L2 Interface

| Signal | Type | Rate | Channels |
|--------|------|------|----------|
| Filtered EEG | float32 | 1000 Hz | 64 |
| Channel labels | string[] | static | 64 |
| Sampling metadata | struct | static | fs, gain, ref |

### 5.2 L2 → L3 Interface

| Signal | Type | Rate | Dimensions |
|--------|------|------|-----------|
| Spectral features | float32 | 4 Hz | 8 |
| ERP features | float32 | event | 4 |
| Feature timestamps | float64 | matched | — |
| Confidence scores | float32 | matched | 2 (P300, MMN) |

### 5.3 L3 → L4 Interface

| Signal | Type | Rate | Dimensions |
|--------|------|------|-----------|
| State estimate | float32 | 25 Hz | 20 |
| State covariance | float32 | 25 Hz | 20×20 |
| Innovation | float32 | 25 Hz | 12 |
| Lyapunov margin | float32 | 25 Hz | 1 |

### 5.4 L4 → Transducer Interface

| Parameter | Range | Resolution | Unit |
|-----------|-------|-----------|------|
| Intensity (I) | 0–720 | 1 | mW/cm² |
| Frequency (f) | 250–700 | 1 | kHz |
| Phase (φ) | 0–360 | 0.1 | degrees |
| Mod freq (f_mod) | 1–1000 | 0.1 | Hz |

---

## 6. Non-Functional Requirements

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| Loop latency | < 40 ms total | ~3–6 cycles per theta oscillation |
| Safety response | < 1 ms hardware | IEC 62304 Class C |
| Uptime | > 99.5% session | Clinical-grade reliability |
| Data logging | All channels, full rate | Audit trail + post-hoc analysis |
| Calibration time | < 10 min | Practical usability |
| Power consumption | < 500 W | Standard medical device range |
| Weight | < 15 kg | Mountable on patient chair/bed |

---

*This architecture is a conceptual design for a SPECULATIVE framework. No hardware implementation exists.*
