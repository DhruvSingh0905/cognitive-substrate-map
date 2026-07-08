"""Signed propagation operator (Phase 3 · stage 1).

Builds the directed signed weight matrix from `edges_regulatory.csv` and column-
normalizes it into the Personalized-PageRank transition operator that APPNP uses.

Orientation:  W[i, j] = sign of edge (source=j → target=i), so (W @ x)_i is the signed
influence flowing INTO node i from its regulators. Column-normalizing by each source's
out-strength splits a regulator's influence across its targets (hub-damping) and makes
the |·|-matrix column-stochastic, which guarantees ρ(Ŵ) ≤ 1 — so the APPNP resolvent
(I − (1−α)Ŵ)⁻¹ always converges. This is the correct APPNP operator for a *directed*
signed graph; the symmetric D^(−1/2)WD^(−1/2) form is for undirected GCN only.
"""
import numpy as np
import pandas as pd


def signed_weight_matrix(edges: pd.DataFrame, nodes: list):
    """Return (W, idx): dense N×N signed matrix and {gene: index}.

    Only edges whose source AND target are both in `nodes` are kept. W[target, source] = sign.
    """
    idx = {g: i for i, g in enumerate(nodes)}
    W = np.zeros((len(nodes), len(nodes)))
    for s, t, sign in zip(edges["source"].astype(str),
                          edges["target"].astype(str),
                          edges["sign"]):
        if s in idx and t in idx:
            W[idx[t], idx[s]] = sign
    return W, idx


def normalize(W: np.ndarray) -> np.ndarray:
    """Column-normalize by out-strength: Ŵ[i,j] = W[i,j] / Σᵢ|W[i,j]|.

    Dangling columns (sinks, no out-edges) stay all-zero. This is the signed
    Personalized-PageRank transition operator.
    """
    out_strength = np.abs(W).sum(axis=0)     # per-source column sum
    d = np.where(out_strength == 0, 1.0, out_strength)
    return W / d


def spectral_radius(M: np.ndarray) -> float:
    """Largest eigenvalue modulus ρ(M)."""
    return float(np.max(np.abs(np.linalg.eigvals(M))))
