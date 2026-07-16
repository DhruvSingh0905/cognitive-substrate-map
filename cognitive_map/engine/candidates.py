"""Constrained intervention set (the fix).

The optimizer may only PUSH un-defended upstream drivers — not defended hubs. A push candidate is a
druggable, actionable knob (d≠0) that can cascade (out-degree > 0) and is not heavily regulated
(in-degree ≤ IN_MAX). Defended convergence hubs like BDNF and CREB1 are things we want to MOVE
(targets/readouts), not push directly — homeostasis (their many regulators) fights a direct push.

We use the deterministic in-degree criterion rather than the Liu–Barabási driver SET, which is
non-unique (a node can be a driver in some maximum matchings and not others).
"""
from pathlib import Path
import numpy as np
import pandas as pd

from cognitive_map.engine import operator as op

OUT = Path(__file__).resolve().parents[1] / "output"
IN_MAX = 10      # > this many regulators ⇒ a defended hub, not a lever  (WE-built; tunable)
ETA = 0.1        # homeostatic-cost weight: push effort scales with (1 + ETA·in-degree)  (tunable)


def degrees():
    nodes = pd.read_csv(OUT / "nodes.csv"); edges = pd.read_csv(OUT / "edges_regulatory.csv")
    node_list = nodes["gene"].astype(str).tolist()
    W, idx = op.signed_weight_matrix(edges, node_list)
    indeg = {g: int(np.abs(W).sum(axis=1)[idx[g]]) for g in node_list}
    outdeg = {g: int(np.abs(W).sum(axis=0)[idx[g]]) for g in node_list}
    md = dict(zip(node_list, nodes["modulating_drugs"].fillna("").astype(str)))
    return indeg, outdeg, md


def constrained_knobs(target_rows, in_max=IN_MAX):
    """Gene names allowed as push candidates, plus the in-degree map (for the homeostatic cost)."""
    indeg, outdeg, md = degrees()
    keep = [r["gene"] for r in target_rows
            if r["role"] == "knob" and r["d"] != 0 and r["gene"] in indeg
            and outdeg[r["gene"]] > 0 and indeg[r["gene"]] <= in_max and len(md.get(r["gene"], "")) > 0]
    return keep, indeg
