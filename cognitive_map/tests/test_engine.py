"""Phase 3 engine tests — the propagation operator + steady-state solve.

Pure numeric unit tests on hand-built toy graphs (NO Neo4j, NO feedback) so every
sign is derivable by hand, plus one integration check on the real substrate against
signs read straight out of edges_regulatory.csv (CREB1->BDNF->NTRK2, AKT1->CHUK-|NFKB1).
"""
import numpy as np
import pandas as pd
import pytest

from cognitive_map.engine import operator as op
from cognitive_map.engine import propagate as pr


# ---- toy graphs (no feedback → every sign is exact & hand-derivable) ----
def _diamond():
    # A->B (+1), B->C (-1), A->C (+1)
    return pd.DataFrame({"source": ["A", "B", "A"],
                         "target": ["B", "C", "C"],
                         "sign":   [1,   -1,  1]})


def _two_chains():
    # A->B(+)->C(+)   and   P->Q(+)->R(-)
    return pd.DataFrame({"source": ["A", "B", "P", "Q"],
                         "target": ["B", "C", "Q", "R"],
                         "sign":   [1,   1,   1,   -1]})


# ---------------- operator ----------------
def test_signed_weight_matrix_orientation():
    """W[target, source] = edge sign, so (W @ x) flows source→target."""
    nodes = ["A", "B", "C"]
    W, idx = op.signed_weight_matrix(_diamond(), nodes)
    assert W[idx["B"], idx["A"]] == 1      # A->B +1
    assert W[idx["C"], idx["B"]] == -1     # B->C -1
    assert W[idx["C"], idx["A"]] == 1      # A->C +1
    assert W[idx["A"], idx["B"]] == 0      # no reverse edge


def test_column_normalization_splits_out_influence():
    """PageRank normalization: each source's outgoing |flux| sums to 1 (hub-damping)."""
    nodes = ["A", "B", "C"]
    W, idx = op.signed_weight_matrix(_diamond(), nodes)
    What = op.normalize(W)
    # A has out-strength |+1|+|+1| = 2 → its two out-edges each become 0.5
    assert np.isclose(What[idx["B"], idx["A"]], 0.5)
    assert np.isclose(What[idx["C"], idx["A"]], 0.5)
    # B has out-strength 1 → edge unchanged in magnitude, sign kept
    assert np.isclose(What[idx["C"], idx["B"]], -1.0)
    # column flux conservation
    assert np.isclose(np.abs(What[:, idx["A"]]).sum(), 1.0)


def test_dangling_column_stays_zero():
    """A sink node (no out-edges) must not divide by zero."""
    nodes = ["A", "B", "C"]
    What = op.normalize(op.signed_weight_matrix(_diamond(), nodes)[0])
    assert np.all(What[:, nodes.index("C")] == 0)   # C has no out-edges


def test_spectral_radius_bounded_by_one():
    """The convergence guarantee: ρ(Ŵ) ≤ 1 for the signed column-normalized operator."""
    What = op.normalize(op.signed_weight_matrix(_two_chains(), list("ABCPQR"))[0])
    assert op.spectral_radius(What) <= 1.0 + 1e-9


# ---------------- propagation ----------------
def test_perturbation_anchors_at_source():
    x = pr.steady_state(_two_chains(), list("ABCPQR"), {"A": 1.0}, alpha=0.15)
    assert x["A"] > 0                       # source stays positive (teleport anchor)


def test_sign_propagates_two_hops():
    """+then+ → positive downstream; +then- → negative downstream."""
    nodes = list("ABCPQR")
    x = pr.steady_state(_two_chains(), nodes, {"A": 1.0}, alpha=0.15)
    assert x["B"] > 0 and x["C"] > 0        # A->B(+)->C(+)
    xp = pr.steady_state(_two_chains(), nodes, {"P": 1.0}, alpha=0.15)
    assert xp["Q"] > 0 and xp["R"] < 0      # P->Q(+)->R(-)  net negative


def test_resolvent_matches_truncated_series():
    """Closed-form α(I-(1-α)Ŵ)⁻¹p must equal the damped power series Σ α(1-α)ᵏŴᵏp."""
    nodes = list("ABCPQR")
    W, idx = op.signed_weight_matrix(_two_chains(), nodes)
    What = op.normalize(W)
    alpha = 0.2
    p = np.zeros(len(nodes)); p[idx["A"]] = 1.0
    series = sum((1 - alpha) ** k * np.linalg.matrix_power(What, k) @ p for k in range(200)) * alpha
    closed = pr.steady_state_vector(What, p, alpha=alpha)
    assert np.allclose(series, closed, atol=1e-8)


def test_off_target_unreached_stays_zero():
    """A node on a disconnected chain must not move when we perturb the other chain."""
    x = pr.steady_state(_two_chains(), list("ABCPQR"), {"A": 1.0}, alpha=0.15)
    assert np.isclose(x["Q"], 0.0) and np.isclose(x["R"], 0.0)


def test_variance_check_flags_near_uniform():
    """Over-smoothing diagnostic: a near-uniform response is flagged, a peaked one is not."""
    assert pr.is_oversmoothed(np.array([1.0, 1.0, 1.0, 1.0]))
    assert not pr.is_oversmoothed(np.array([1.0, 0.0, 0.0, 0.0]))


# ---------------- integration: real substrate, signs from the CSV ----------------
@pytest.fixture(scope="module")
def real():
    from pathlib import Path
    out = Path(__file__).resolve().parents[1] / "output"
    nodes = pd.read_csv(out / "nodes.csv")["gene"].astype(str).tolist()
    edges = pd.read_csv(out / "edges_regulatory.csv")
    return edges, nodes


def test_real_creb1_raises_bdnf_and_trkb(real):
    """CREB1->BDNF(+1)->NTRK2(+1): perturbing CREB1 up must raise BDNF and NTRK2."""
    edges, nodes = real
    x = pr.steady_state(edges, nodes, {"CREB1": 1.0}, alpha=0.15)
    assert x["CREB1"] > 0
    assert x["BDNF"] > 0
    assert x["NTRK2"] > 0


def test_real_spectral_radius_bounded(real):
    edges, nodes = real
    What = op.normalize(op.signed_weight_matrix(edges, nodes)[0])
    assert op.spectral_radius(What) <= 1.0 + 1e-9
