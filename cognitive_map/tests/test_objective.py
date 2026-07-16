"""Stage-3 objective: per-node benefit, confidence-weighted aggregate, cost."""
from cognitive_map.engine import objective as ob


def test_node_benefit_distance_reduction():
    assert ob.node_benefit(0.5, 1.0) == 0.5     # d=+1, moved toward it → 1−|0.5−1|
    assert abs(ob.node_benefit(-0.3, 1.0) - (-0.3)) < 1e-12   # d=+1, wrong way → penalty
    assert ob.node_benefit(0.0, 1.0) == 0.0     # unmoved → 0 (most nodes)
    assert ob.node_benefit(0.2, 0.0) == -0.2    # setpoint moved → penalty
    assert abs(ob.node_benefit(-0.4, -1.0) - 0.4) < 1e-12     # d=−1, moved down → reward


def test_aggregate_weights_and_skips_readouts():
    x = {"A": 0.5, "B": 0.2, "R": 0.9}
    rows = [{"gene": "A", "d": 1.0, "w": 1.0},   # 1.0*(1-0.5)=0.5
            {"gene": "B", "d": 0.0, "w": 0.5},   # 0.5*(0-0.2)=-0.1
            {"gene": "R", "d": -1.0, "w": 0.0}]  # w=0 → skipped
    assert abs(ob.aggregate_benefit(x, rows) - 0.4) < 1e-9
    assert abs(ob.aggregate_benefit(x, rows, exclude="A") - (-0.1)) < 1e-9   # downstream only


def test_cost_effort_plus_offtarget():
    p = {"A": 1.0}
    x = {"A": 0.15, "B": 0.02, "Z": 0.03}       # Z is off-target
    assert abs(ob.cost(p, x, {"A", "B"}, gamma=1.0) - 1.03) < 1e-9   # |p|=1 + 1*|x_Z|
