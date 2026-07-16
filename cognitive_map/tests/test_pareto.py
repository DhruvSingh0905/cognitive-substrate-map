"""Stage-5 Pareto front — dominance logic + combination scoring by linear superposition."""
from cognitive_map.engine import pareto as pa


def test_pareto_dominance():
    pts = [{"id": "a", "benefit": 1.0, "cost": 1.0},
           {"id": "b", "benefit": 2.0, "cost": 1.0},   # dominates a (more benefit, same cost)
           {"id": "c", "benefit": 2.0, "cost": 2.0},   # dominated by b (same benefit, more cost)
           {"id": "d", "benefit": 3.0, "cost": 3.0}]   # non-dominated (highest benefit)
    front = {p["id"] for p in pa.pareto_front(pts)}
    assert front == {"b", "d"}


def test_eval_set_superposes_responses():
    # two knobs; combined x* = sum of the single-knob responses
    resp = {"A": (1.0, {"A": 0.15, "T": 0.10}),
            "B": (1.0, {"B": 0.15, "T": 0.05})}
    rows = [{"gene": "T", "d": 1.0, "w": 1.0}]        # one scored target
    B, C = pa.eval_set(["A", "B"], resp, rows, {"A", "B", "T"}, gamma=1.0)
    # combined x*_T = 0.15 → b = |1|-|0.15-1| = 0.15 ; B = 1.0*0.15
    assert abs(B - 0.15) < 1e-9
    assert abs(C - 2.0) < 1e-9                          # ||p||_1 = 2, no off-target movement
