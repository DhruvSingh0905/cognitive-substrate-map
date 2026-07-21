"""Formal target controllability: rank[CB, CWB, CW²B, …] vs |S| on small known systems."""
import numpy as np
from cognitive_map.engine import target_control as tc


def _two_chains():
    # A→B→C   and   P→Q   (P,Q unreachable from A).  W[i,j] = edge j→i
    W = np.zeros((5, 5))
    W[1, 0] = 1.0   # A→B
    W[2, 1] = 1.0   # B→C
    W[4, 3] = 1.0   # P→Q
    return W


def test_reachable_target_is_controllable():
    r, s, _ = tc.control_rank(_two_chains(), driver_idx=[0], target_idx=[2])   # drive A, target C
    assert r == 1 and s == 1


def test_unreachable_target_is_not_controllable():
    r, s, _ = tc.control_rank(_two_chains(), driver_idx=[0], target_idx=[4])   # drive A, target Q
    assert r == 0 and s == 1


def test_partial_controllability():
    r, s, _ = tc.control_rank(_two_chains(), driver_idx=[0], target_idx=[2, 4])  # C yes, Q no
    assert r == 1 and s == 2


def test_two_drivers_cover_both_chains():
    r, s, _ = tc.control_rank(_two_chains(), driver_idx=[0, 3], target_idx=[2, 4])
    assert r == 2 and s == 2
