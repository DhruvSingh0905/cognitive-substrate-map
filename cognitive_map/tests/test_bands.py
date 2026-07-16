"""Stage-4 Monte-Carlo bands — invariants on the real substrate."""
from pathlib import Path
import pandas as pd
from cognitive_map.engine import bands as bd
from cognitive_map.engine.target_vector import build_target

OUT = Path(bd.__file__).resolve().parents[1] / "output"


def test_band_invariants():
    nodes = pd.read_csv(OUT / "nodes.csv")["gene"].astype(str).tolist()
    edges = pd.read_csv(OUT / "edges_regulatory.csv")
    res = bd.montecarlo_bands(edges, nodes, build_target(), M=300, seed=1)
    for b in res:
        assert b["lo"] <= b["median"] <= b["hi"]        # band brackets the median
    assert abs(sum(b["p_top"] for b in res) - 1.0) < 1e-9   # exactly one #1 per draw
    assert res[0]["gene"] == "CAMK2B"                    # top of the constrained (un-defended driver) set
