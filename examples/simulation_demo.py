"""
NATE vΞ⁷·₁ — Simulation Demo

Demonstrates the 20-dimensional state space model and
the Pennes bioheat thermal model in a simulated scenario.

Usage:
    python simulation_demo.py

Output:
    - Console summary of state evolution
    - Thermal simulation plot saved to simulation_output.png
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.core.state_space import NATEStateSpace
from src.core.constants import ISPTA_MAX, DELTA_T_MAX
from src.safety.bioheat_model import PennesBioheatSolver


def run_state_space_demo():
    """Simulate 10 seconds of state evolution with acoustic control."""
    print("=" * 60)
    print("NATE vΞ⁷·₁ — State Space Simulation Demo")
    print("=" * 60)
    print()
    print("DISCLAIMER: This is a simulation of a SPECULATIVE framework.")
    print("Not validated for any clinical or therapeutic application.")
    print()

    ss = NATEStateSpace(dt=0.04)  # 40ms time step

    # Initialize with random EEG-like spectral powers
    ss.set_subspace("eeg", np.random.exponential(1.0, 8))
    ss.set_subspace("erp", np.array([2.5, 300.0, 1.8, 200.0]))  # amp, lat, amp, lat
    ss.set_subspace("aco", np.array([100.0, 500e3, 0.0, 40.0]))  # I, f, phi, mod
    ss.set_subspace("cpl", np.zeros(4))

    n_steps = 250  # 10 seconds at 40ms steps
    history = np.zeros((n_steps, ss.dim))

    control_input = np.array([100.0, 500e3, 0.0, 40.0])  # Constant acoustic control

    print(f"Simulating {n_steps} steps ({n_steps * 0.04:.1f}s)...")
    print(f"Initial state norm: {np.linalg.norm(ss.state):.4f}")
    print()

    for i in range(n_steps):
        history[i] = ss.step(control_input)

    print(f"Final state norm: {np.linalg.norm(ss.state):.4f}")
    print(f"EEG subspace RMS: {np.sqrt(np.mean(ss.x_eeg ** 2)):.4f}")
    print(f"ERP subspace norm: {np.linalg.norm(ss.x_erp):.4f}")
    print(f"Acoustic params: I={ss.x_aco[0]:.1f} mW/cm², f={ss.x_aco[1]/1e3:.0f} kHz")
    print(f"Coupling norm: {np.linalg.norm(ss.x_cpl):.6f}")
    print()

    # Plot state evolution
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    time_axis = np.arange(n_steps) * 0.04

    axes[0, 0].plot(time_axis, history[:, 0:8])
    axes[0, 0].set_title("EEG Spectral Subspace (8-D)")
    axes[0, 0].set_xlabel("Time (s)")
    axes[0, 0].set_ylabel("Amplitude")

    axes[0, 1].plot(time_axis, history[:, 8:12])
    axes[0, 1].set_title("ERP Feature Subspace (4-D)")
    axes[0, 1].set_xlabel("Time (s)")

    axes[1, 0].plot(time_axis, history[:, 12:16])
    axes[1, 0].set_title("Acoustic Parameter Subspace (4-D)")
    axes[1, 0].set_xlabel("Time (s)")

    axes[1, 1].plot(time_axis, history[:, 16:20])
    axes[1, 1].set_title("Coupling State Subspace (4-D)")
    axes[1, 1].set_xlabel("Time (s)")

    plt.suptitle("NATE vΞ⁷·₁ — State Space Simulation\n(Speculative Framework — Not for Clinical Use)", fontsize=11)
    plt.tight_layout()
    plt.savefig("simulation_state_output.png", dpi=150, bbox_inches="tight")
    print("State plot saved: simulation_state_output.png")
    plt.close()


def run_thermal_demo():
    """Simulate thermal response to ultrasonic exposure at regulatory limits."""
    print("=" * 60)
    print("NATE vΞ⁷·₁ — Bioheat Thermal Simulation Demo")
    print("=" * 60)
    print()

    solver = PennesBioheatSolver(length=0.04, dx=0.001, dt=0.1)

    print(f"Safety limit ISPTA: {ISPTA_MAX} mW/cm²")
    print(f"Safety limit ΔT: {DELTA_T_MAX}°C")
    print()

    # Test at FDA diagnostic limit
    print(f"Simulating exposure at {ISPTA_MAX} mW/cm², 500 kHz, 60s...")
    times, temps, max_dT = solver.simulate(ISPTA_MAX, 500e3, 60.0)

    print(f"Max temperature rise: {np.max(max_dT):.4f}°C")
    print(f"Safety status: {'PASS' if np.max(max_dT) < DELTA_T_MAX else 'FAIL'}")
    print()

    # Test at dangerous level (prior version's erroneous value)
    print("Simulating exposure at ERRONEOUS 120 J/cm² (for comparison)...")
    # 120 J/cm² over 60s = 2 J/(cm²·s) = 2e4 mW/cm² (absurdly high)
    solver2 = PennesBioheatSolver(length=0.04, dx=0.001, dt=0.01)
    try:
        times2, temps2, max_dT2 = solver2.simulate(20000.0, 500e3, 2.0)
        print(f"Max temperature rise at 120 J/cm²: {np.max(max_dT2):.1f}°C in {times2[-1]:.1f}s")
        print(f"This would cause immediate tissue damage.")
    except ValueError as e:
        print(f"Simulation diverged: {e}")
    print()

    # Plot thermal response at regulatory limit
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(times, max_dT, color="steelblue", linewidth=2)
    ax1.axhline(y=DELTA_T_MAX, color="red", linestyle="--", label=f"Safety limit ({DELTA_T_MAX}°C)")
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Max ΔT (°C)")
    ax1.set_title(f"Temperature Rise at {ISPTA_MAX} mW/cm²\n(FDA Diagnostic Limit)")
    ax1.legend(loc="best")
    ax1.grid(True, alpha=0.3)

    # Spatial profile at steady state
    ax2.plot(solver.x * 1000, temps[-1] - 273.15, color="firebrick", linewidth=2)
    ax2.axhline(y=37.0, color="gray", linestyle="--", label="Body temperature (37°C)")
    ax2.set_xlabel("Depth (mm)")
    ax2.set_ylabel("Temperature (°C)")
    ax2.set_title("Spatial Temperature Profile at t=60s")
    ax2.legend(loc="best")
    ax2.grid(True, alpha=0.3)

    plt.suptitle("NATE vΞ⁷·₁ — Pennes Bioheat Thermal Simulation\n(Speculative Framework — Not for Clinical Use)", fontsize=11)
    plt.tight_layout()
    plt.savefig("simulation_thermal_output.png", dpi=150, bbox_inches="tight")
    print("Thermal plot saved: simulation_thermal_output.png")
    plt.close()


if __name__ == "__main__":
    run_state_space_demo()
    print()
    run_thermal_demo()
    print()
    print("Done. Output files:")
    print("  simulation_state_output.png")
    print("  simulation_thermal_output.png")
