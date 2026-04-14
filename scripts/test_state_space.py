"""Tests for NATE vΞ⁷·₁ — State Space Model"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np
from src.core.state_space import NATEStateSpace
from src.core.constants import DIM_STATE, DIM_EEG, DIM_ERP, DIM_ACO, DIM_CPL


def test_initialization():
    ss = NATEStateSpace()
    assert ss.state.shape == (DIM_STATE,)
    assert np.allclose(ss.state, 0.0)


def test_dimensionality():
    ss = NATEStateSpace()
    assert DIM_STATE == DIM_EEG + DIM_ERP + DIM_ACO + DIM_CPL
    assert DIM_STATE == 20


def test_set_subspace_eeg():
    ss = NATEStateSpace()
    vals = np.random.randn(DIM_EEG)
    ss.set_subspace("eeg", vals)
    assert np.allclose(ss.x_eeg, vals)


def test_set_subspace_dimension_mismatch():
    ss = NATEStateSpace()
    with pytest.raises(ValueError):
        ss.set_subspace("eeg", np.zeros(DIM_EEG + 1))


def test_set_subspace_invalid_name():
    ss = NATEStateSpace()
    with pytest.raises(ValueError):
        ss.set_subspace("invalid", np.zeros(5))


def test_step_returns_array():
    ss = NATEStateSpace()
    state = ss.step()
    assert state.shape == (DIM_STATE,)


def test_step_with_control():
    ss = NATEStateSpace()
    control = np.array([100.0, 500e3, 0.0, 40.0])
    state_before = ss.x_cpl.copy()
    ss.step(control)
    # Coupling state should change
    assert not np.allclose(ss.x_cpl, state_before)


def test_control_dimension_mismatch():
    ss = NATEStateSpace()
    with pytest.raises(ValueError):
        ss.step(np.zeros(DIM_ACO + 1))


def test_state_distance():
    s1 = np.random.randn(DIM_STATE)
    s2 = np.random.randn(DIM_STATE)
    d = NATEStateSpace.state_distance(s1, s2)
    assert d >= 0.0
    assert np.isclose(d, np.linalg.norm(s1 - s2))


def test_state_distance_zero():
    s = np.random.randn(DIM_STATE)
    d = NATEStateSpace.state_distance(s, s)
    assert np.isclose(d, 0.0)


def test_state_dict():
    ss = NATEStateSpace()
    ss.set_subspace("eeg", np.ones(DIM_EEG))
    ss.set_subspace("erp", np.ones(DIM_ERP) * 2)
    d = ss.state_dict()
    assert set(d.keys()) == {"eeg", "erp", "aco", "cpl"}


def test_get_full_state_copy():
    ss = NATEStateSpace()
    s1 = ss.get_full_state()
    s1[0] = 999.0
    assert ss.state[0] != 999.0  # Should be a copy


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
