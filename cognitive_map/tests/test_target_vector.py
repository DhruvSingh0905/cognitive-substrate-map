"""Stage-3 objective inputs: the numeric target-deviation vector d + confidence weights w."""
from cognitive_map.engine.target_vector import build_target


def _by_gene():
    return {r["gene"]: r for r in build_target()}


def test_covers_all_94():
    assert len(build_target()) == 94


def test_direction_maps_to_d():
    m = _by_gene()
    assert m["CREB1"]["d"] == 1.0      # up
    assert m["IL1B"]["d"] == -1.0      # down
    assert m["MTOR"]["d"] == 0.0       # setpoint -> hold at baseline
    assert m["RASGRF1"]["d"] == 0.0    # uncertain -> no target


def test_readouts_are_gauges_weight_zero():
    m = _by_gene()
    assert m["FOS"]["w"] == 0.0 and m["FOS"]["scored"] is False    # IEG marker
    assert m["APP"]["w"] == 0.0 and m["APP"]["scored"] is False     # disease readout


def test_confidence_to_weight():
    m = _by_gene()
    assert m["CREB1"]["w"] == 1.0                       # high
    assert m["RASGRF1"]["w"] == 0.3                     # low
    assert m["CHRNA7"]["w"] == 0.6                      # medium
    assert m["CREB1"]["w_lo"] == 0.9 and m["CREB1"]["w_hi"] == 1.0   # band interval


def test_exactly_13_readouts_unscored():
    rows = build_target()
    assert sum(1 for r in rows if not r["scored"]) == 13
    assert sum(1 for r in rows if r["scored"]) == 81
