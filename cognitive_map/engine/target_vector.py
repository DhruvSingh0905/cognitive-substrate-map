"""Numeric target-deviation vector d and confidence weights w (Stage 3 · objective inputs).

WE-built numbers — hand-verify before the objective consumes them.

  d_i : desired signed deviation from baseline.
        up -> +1, down -> -1, setpoint/uncertain/marker -> 0 (hold at baseline).
  w_i : confidence weight in the objective.
        readouts (gauges) -> 0 (measured, never optimized, never a knob);
        else  high -> 1.0, medium -> 0.6, low -> 0.3.
        Interval form (for the Monte-Carlo band): high [.9,1], medium [.5,.7], low [.2,.4].
"""
from cognitive_map.target_state import TARGET_STATE

D_BY_DIR = {"up": 1.0, "down": -1.0, "setpoint": 0.0, "uncertain": 0.0, "marker": 0.0}
W_POINT = {"high": 1.0, "medium": 0.6, "low": 0.3}
W_INTERVAL = {"high": (0.9, 1.0), "medium": (0.5, 0.7), "low": (0.2, 0.4)}


def build_target():
    """Return a list of per-gene dicts with d, w (point + interval), and scored flag."""
    rows = []
    for gene, system, role, direction, shape, conf, note in TARGET_STATE:
        if role == "readout":                       # gauges: measured, not optimized
            w, wlo, whi = 0.0, 0.0, 0.0
        else:
            w = W_POINT[conf]; wlo, whi = W_INTERVAL[conf]
        rows.append({
            "gene": gene, "system": system, "role": role, "direction": direction,
            "shape": shape, "confidence": conf,
            "d": D_BY_DIR[direction], "w": w, "w_lo": wlo, "w_hi": whi,
            "scored": w > 0, "note": note,
        })
    return rows
