"""Scoring objective (Stage 3): benefit, weighted aggregate, cost, and the single-knob ranking.

benefit    b_i = |d_i| − |x*_i − d_i|      (reward moving toward d, penalize setpoint drift/overshoot)
aggregate  B(x) = Σ_i w_i b_i              (over scored targets; readouts w=0 skipped)
cost       C(p,x) = ‖p‖_1 + γ · Σ_{off-target} |x*_j|
"""
from cognitive_map.engine import propagate as pr


def node_benefit(xi: float, d: float) -> float:
    return abs(d) - abs(xi - d)


def aggregate_benefit(x: dict, target_rows: list, exclude=None) -> float:
    excl = set() if exclude is None else ({exclude} if isinstance(exclude, str) else set(exclude))
    total = 0.0
    for r in target_rows:
        if r["w"] == 0 or r["gene"] in excl:
            continue
        xi = x.get(r["gene"])
        if xi is None:
            continue
        total += r["w"] * node_benefit(xi, r["d"])
    return total


def cost(p: dict, x: dict, target_genes: set, indeg: dict = None, eta: float = 0.1,
         gamma: float = 1.0) -> float:
    if indeg is not None:                                  # homeostatic: harder to push a defended node
        effort = sum(abs(v) * (1.0 + eta * indeg.get(g, 0)) for g, v in p.items())
    else:
        effort = sum(abs(v) for v in p.values())
    offtarget = sum(abs(v) for g, v in x.items() if g not in target_genes)
    return effort + gamma * offtarget


def score_knob(edges, nodes, gene, d, target_rows, target_genes, indeg=None, alpha=0.15, gamma=1.0):
    """Push `gene` by its target direction d, propagate, score the whole-state effect."""
    p = {gene: d}
    x = pr.steady_state(edges, nodes, p, alpha=alpha)
    return {
        "gene": gene, "d": d,
        "B_total": aggregate_benefit(x, target_rows),
        "B_downstream": aggregate_benefit(x, target_rows, exclude=gene),
        "cost": cost(p, x, target_genes, indeg=indeg, gamma=gamma),
    }


def rank_single_knobs(edges, nodes, target_rows, alpha=0.15, gamma=1.0):
    """Rank the CONSTRAINED knobs (un-defended upstream drivers) by downstream benefit."""
    from cognitive_map.engine.candidates import constrained_knobs
    target_genes = {r["gene"] for r in target_rows}
    keep, indeg = constrained_knobs(target_rows)
    keepset = set(keep)
    candidates = [r for r in target_rows if r["gene"] in keepset]
    scored = [score_knob(edges, nodes, r["gene"], r["d"], target_rows, target_genes, indeg, alpha, gamma)
              for r in candidates]
    scored.sort(key=lambda s: -s["B_downstream"])
    return scored
