"""Formal target controllability — can the constrained drivers actually STEER the target state?

For the linear system ẋ = Ŵx + Bu with outputs y = Cx (the scored targets), the target set S is
fully controllable iff the target-controllability matrix has full row rank:

    rank[ CB, CŴB, CŴ²B, …, CŴ^{N-1}B ] = |S|          (Kalman/output form; Gao et al. 2014)

rank < |S| means only a rank-dimensional *subspace* of the target state is independently steerable —
the honest answer to "can we steer it, or only nudge it?".

Numerics: Ŵ^k decays (ρ(Ŵ)=0.544), so deep blocks underflow. Each block's columns are normalized
before stacking — scaling columns doesn't change the span, so the rank is preserved and stabilized.
"""
from pathlib import Path
import numpy as np
import pandas as pd

from cognitive_map.engine import operator as op
from cognitive_map.engine.target_vector import build_target

OUT = Path(__file__).resolve().parents[1] / "output"


def control_rank(W, driver_idx, target_idx, max_k=None, tol=1e-9, stall=4):
    """Return (rank, |S|, blocks_used) for the target-controllability matrix."""
    N = W.shape[0]
    m, s = len(driver_idx), len(target_idx)
    B = np.zeros((N, m))
    for j, i in enumerate(driver_idx):
        B[i, j] = 1.0
    C = np.zeros((s, N))
    for j, i in enumerate(target_idx):
        C[j, i] = 1.0
    blocks, Mk, rank, flat, k = [], B.copy(), 0, 0, 0
    K = max_k or min(N, 80)
    for k in range(1, K + 1):
        blk = C @ Mk
        norms = np.linalg.norm(blk, axis=0)
        keep = norms > 1e-12
        if keep.any():
            blocks.append(blk[:, keep] / norms[keep])      # column-normalize: span-preserving
        new = int(np.linalg.matrix_rank(np.hstack(blocks), tol=tol)) if blocks else 0
        if new >= s:
            return new, s, k
        flat = flat + 1 if new == rank else 0
        rank = new
        if flat >= stall:
            break
        Mk = W @ Mk
    return rank, s, k


def _setup():
    from cognitive_map.engine.candidates import constrained_knobs
    nodes = pd.read_csv(OUT / "nodes.csv"); edges = pd.read_csv(OUT / "edges_regulatory.csv")
    node_list = nodes["gene"].astype(str).tolist()
    W, idx = op.signed_weight_matrix(edges, node_list)
    What = op.normalize(W)
    rows = build_target()
    targets = [r["gene"] for r in rows if r["w"] > 0 and r["gene"] in idx]
    constrained = constrained_knobs(rows)[0]
    md = dict(zip(node_list, nodes["modulating_drugs"].fillna("").astype(str)))
    all_knobs = [r["gene"] for r in rows if r["role"] == "knob" and r["d"] != 0
                 and r["gene"] in idx and len(md.get(r["gene"], "")) > 0]
    return idx, What, node_list, targets, constrained, all_knobs


def main():
    idx, What, node_list, targets, constrained, all_knobs = _setup()
    tgt_idx = [idx[g] for g in targets]
    cases = [("constrained drivers (un-defended)", constrained),
             ("all druggable knobs (unconstrained)", all_knobs),
             ("every node (graph ceiling)", node_list)]
    results = []
    for label, drivers in cases:
        didx = [idx[g] for g in drivers]
        r, s, k = control_rank(What, didx, tgt_idx)
        results.append({"label": label, "m": len(drivers), "rank": r, "s": s, "k": k})
        print(f"{label:38} inputs={len(drivers):>3}  rank {r:>3} / {s}  ({100*r/s:.0f}% of target dims, k={k})")
    build_report(results)
    return results


def build_report(results):
    rows_html = "".join(
        f'<tr><td>{r["label"]}</td><td class="n">{r["m"]}</td><td class="n">{r["rank"]} / {r["s"]}</td>'
        f'<td class="n">{100*r["rank"]/r["s"]:.0f}%</td></tr>' for r in results)
    c = results[0]
    html = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Target controllability</title><style>
:root{{--bg:#0f1115;--panel:#171a21;--ink:#e8eaed;--muted:#9aa3b2;--line:#2a2f3a}}
*{{box-sizing:border-box}} body{{margin:0;background:#0f1115;color:var(--ink);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:30px}}
.wrap{{max-width:820px;margin:0 auto}} h1{{font-size:22px;margin:0 0 4px}} .sub{{color:var(--muted);margin:0 0 14px}}
.lead{{background:rgba(240,162,60,.08);border-left:3px solid #f0a23c;border-radius:8px;padding:10px 16px;margin:12px 0;font-size:14px;color:#e6dcc4}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin-top:10px}} td,th{{padding:6px 10px;border-bottom:1px solid var(--line);text-align:left}}
th{{color:var(--muted);font-weight:600}} .n{{font-family:ui-monospace,Menlo,monospace}}
code{{background:#1d212b;padding:1px 6px;border-radius:4px}}
</style></head><body><div class="wrap">
<h1>Formal target controllability</h1>
<p class="sub">rank[ CB, CŴB, CŴ²B, … ] vs |S| — how many of the target dimensions are <i>independently steerable</i>.</p>
<div class="lead">The constrained (un-defended) drivers span <b>{c['rank']} of {c['s']}</b> target dimensions
({100*c['rank']/c['s']:.0f}%). Anything below 100% means we can <i>nudge</i> the target state along that subspace but
cannot drive it to an arbitrary configuration — the honest limit on the claim.</div>
<table><tr><th>input set</th><th>inputs</th><th>rank / |S|</th><th>coverage</th></tr>{rows_html}</table>
<p style="color:var(--muted);font-size:12px;margin-top:16px;border-top:1px solid var(--line);padding-top:10px">
System matrix = the column-normalized Ŵ used by the propagation engine. Blocks are column-normalized before stacking
(span-preserving) so the exponentially-decaying deep blocks stay numerically meaningful.</p>
</div></body></html>"""
    (OUT / "target_control.html").write_text(html)
    md = ["# Formal target controllability", "",
          f"Constrained drivers span **{c['rank']} / {c['s']}** target dimensions "
          f"({100*c['rank']/c['s']:.0f}%).", "",
          "| input set | inputs | rank / \\|S\\| | coverage |", "|---|---|---|---|"]
    for r in results:
        md.append(f"| {r['label']} | {r['m']} | {r['rank']} / {r['s']} | {100*r['rank']/r['s']:.0f}% |")
    (OUT / "target_control.md").write_text("\n".join(md) + "\n")


if __name__ == "__main__":
    main()
