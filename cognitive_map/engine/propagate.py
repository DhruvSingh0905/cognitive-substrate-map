"""APPNP steady-state solve (Phase 3 · stage 2).

Signed Personalized-PageRank fixed point under feedback:

    x* = α·p + (1−α)·Ŵ·x*      ⟹      x* = α·(I − (1−α)Ŵ)⁻¹·p

The resolvent is the steady state of the 200-node feedback core (why one-shot
propagation is wrong here); the (1−α)ᵏ decay in its series expansion is the
over-smoothing guard. x* is the deviation-from-baseline of every node.
"""
import numpy as np
import pandas as pd

from cognitive_map.engine import operator as op


def steady_state_vector(What: np.ndarray, p: np.ndarray, alpha: float = 0.15) -> np.ndarray:
    """x* = α (I − (1−α)Ŵ)⁻¹ p."""
    n = What.shape[0]
    return alpha * np.linalg.solve(np.eye(n) - (1 - alpha) * What, p)


def steady_state(edges: pd.DataFrame, nodes: list, perturbation: dict,
                 alpha: float = 0.15) -> dict:
    """Perturb {gene: magnitude}, propagate to steady state, return {gene: x*}."""
    W, idx = op.signed_weight_matrix(edges, nodes)
    What = op.normalize(W)
    p = np.zeros(len(nodes))
    for g, v in perturbation.items():
        if g in idx:
            p[idx[g]] = v
    x = steady_state_vector(What, p, alpha=alpha)
    return {g: float(x[idx[g]]) for g in nodes}


def nonlinear_steady_state_vector(What: np.ndarray, p: np.ndarray, alpha: float = 0.15,
                                  iters: int = 400) -> np.ndarray:
    """Saturating fixed point:  x = (1−α)·Ŵ·tanh(x) + α·p.

    tanh squashes each node's state before it propagates — a Hill-like ceiling. For small |x|,
    tanh(x)≈x so this reduces to the linear resolvent; for large |x| it saturates. The map is a
    contraction ((1−α)·ρ(Ŵ)<1, tanh is 1-Lipschitz), so it converges to a unique fixed point.
    """
    x = p.copy()
    for _ in range(iters):
        x = (1 - alpha) * (What @ np.tanh(x)) + alpha * p
    return x


def is_oversmoothed(x: np.ndarray, tol: float = 1e-6) -> bool:
    """Over-smoothing diagnostic: True if the response collapsed to ~uniform (lost signal)."""
    x = np.asarray(x, dtype=float)
    if x.max() - x.min() < tol:
        return True
    return bool(np.std(x) / (np.abs(x).mean() + 1e-12) < tol)
