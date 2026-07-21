"""Stage 5 — combinations and the benefit–cost Pareto front.

Linearity shortcut: a multi-knob response is the SUM of the single-knob x* vectors, so any
subset is scored by adding precomputed vectors then scoring once (benefit is nonlinear, so we
score the combined state — overshoot / setpoint drift / two knobs reinforcing are all captured).

Search = greedy forward selection (full front) + exhaustive singles/pairs/triples (catch synergies
greedy misses). Report the non-dominated (Pareto) frontier of benefit vs cost.
"""
from pathlib import Path
import itertools
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from cognitive_map.engine import propagate as pr, objective as ob
from cognitive_map.engine.target_vector import build_target

OUT = Path(__file__).resolve().parents[1] / "output"
BG, INK, MUT = "#0f1115", "#e8eaed", "#9aa3b2"
GREEN, GOLD, GREY = "#4caf7d", "#e8c468", "#7b8494"


def single_knob_responses(edges, nodes, rows, alpha=0.15):
    from cognitive_map.engine.candidates import constrained_knobs
    keep, indeg = constrained_knobs(rows)
    keepset = set(keep)
    knobs = [r for r in rows if r["gene"] in keepset]
    resp = {r["gene"]: (r["d"], pr.steady_state(edges, nodes, {r["gene"]: r["d"]}, alpha=alpha))
            for r in knobs}
    return list(resp), resp, indeg


def eval_set(S, resp, rows, target_genes, indeg=None, gamma=1.0):
    x = {}
    for k in S:
        for g, v in resp[k][1].items():
            x[g] = x.get(g, 0.0) + v
    B = ob.aggregate_benefit(x, rows, exclude=set(S))   # DOWNSTREAM benefit — exclude the pushed knobs
    p = {k: resp[k][0] for k in S}
    return B, ob.cost(p, x, target_genes, indeg=indeg, gamma=gamma)


def greedy_forward(genes, resp, rows, target_genes, indeg=None, max_size=16, gamma=1.0):
    S, path, cur_B, remaining = [], [], 0.0, set(genes)
    for _ in range(min(max_size, len(genes))):
        best = None
        for k in remaining:
            B, C = eval_set(S + [k], resp, rows, target_genes, indeg, gamma)
            if best is None or B > best[1]:
                best = (k, B, C)
        k, B, C = best
        if B <= cur_B + 1e-9:                       # adding anything now hurts (overshoot/collateral)
            break
        S.append(k); remaining.discard(k); cur_B = B
        path.append({"S": tuple(S), "size": len(S), "benefit": B, "cost": C, "added": k})
    return path


def brute_combos(genes, resp, rows, target_genes, indeg=None, sizes=None, gamma=1.0):
    """Exhaustive by default: every non-empty subset, so the front is provably optimal."""
    if sizes is None:
        sizes = range(1, len(genes) + 1)
    out = []
    for s in sizes:
        for combo in itertools.combinations(genes, s):
            B, C = eval_set(combo, resp, rows, target_genes, indeg, gamma)
            out.append({"S": combo, "size": s, "benefit": B, "cost": C})
    return out


def pareto_front(points):
    front = []
    for p in points:
        if not any(q is not p and q["benefit"] >= p["benefit"] and q["cost"] <= p["cost"]
                   and (q["benefit"] > p["benefit"] or q["cost"] < p["cost"]) for q in points):
            front.append(p)
    return sorted(front, key=lambda p: p["cost"])


# ---------------- run + report ----------------
def _darkax(ax):
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_color("#39414f")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.tick_params(colors=MUT, labelsize=11)
    ax.xaxis.label.set_color(INK); ax.yaxis.label.set_color(INK); ax.title.set_color(INK)


def front_plot(all_pts, front, path=OUT / "pareto_front.png"):
    fig, ax = plt.subplots(figsize=(8.4, 6), dpi=200, facecolor=BG); _darkax(ax)
    ax.scatter([p["cost"] for p in all_pts], [p["benefit"] for p in all_pts],
               s=9, color=GREY, alpha=0.28, edgecolors="none", label="all sets (≤3 + greedy)")
    fx = [p["cost"] for p in front]; fy = [p["benefit"] for p in front]
    ax.plot(fx, fy, color=GREEN, lw=1.6, alpha=0.7)
    ax.scatter(fx, fy, s=34, color=GREEN, edgecolors="none", zorder=3, label="Pareto front")
    for p in front:
        if p["size"] <= 4:
            ax.annotate("+".join(p["S"]), (p["cost"], p["benefit"]), color=INK, fontsize=8,
                        xytext=(5, -3), textcoords="offset points")
    ax.set_xlabel("cost  ‖p‖₁ + off-target movement"); ax.set_ylabel("benefit  B(S)")
    ax.set_title("Benefit–cost Pareto front over knob combinations")
    lg = ax.legend(frameon=False, fontsize=10, loc="lower right")
    for t in lg.get_texts():
        t.set_color(INK)
    fig.tight_layout(); fig.savefig(path, facecolor=BG); plt.close(fig)


def build_report(front, n_all):
    rows_html = "\n".join(
        f'<tr><td class="rk">{i}</td><td class="sz">{p["size"]}</td>'
        f'<td class="g">{" + ".join(p["S"])}</td>'
        f'<td class="b">{p["benefit"]:+.4f}</td><td class="c">{p["cost"]:.3f}</td></tr>'
        for i, p in enumerate(front, 1))
    meaningful = [p for p in front if p["benefit"] > 1e-4]
    knee = max(meaningful, key=lambda p: p["benefit"] / p["cost"]) if meaningful else None
    html = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pareto front — knob combinations</title><style>
:root{{--bg:#0f1115;--panel:#171a21;--ink:#e8eaed;--muted:#9aa3b2;--line:#2a2f3a}}
*{{box-sizing:border-box}} body{{margin:0;background:#0f1115;color:var(--ink);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:30px}}
.wrap{{max-width:900px;margin:0 auto}} h1{{font-size:22px;margin:0 0 4px}} .sub{{color:var(--muted);margin:0 0 14px}}
h2{{font-size:14px;margin:22px 0 8px;border-bottom:1px solid var(--line);padding-bottom:6px}} img{{max-width:100%;border:1px solid var(--line);border-radius:10px}}
.lead{{background:rgba(76,175,125,.08);border-left:3px solid #4caf7d;border-radius:8px;padding:10px 16px;margin:10px 0;font-size:14px;color:#cfe3d6}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin-top:8px}} td,th{{padding:5px 9px;border-bottom:1px solid var(--line);text-align:left}}
th{{color:var(--muted);font-weight:600}} .rk{{color:var(--muted);width:24px}} .sz{{color:var(--muted);width:34px}}
.g{{font:600 12px ui-monospace,Menlo,monospace}} .b,.c{{font-family:ui-monospace,Menlo,monospace}} .c{{color:var(--muted)}}
</style></head><body><div class="wrap">
<h1>Benefit–cost Pareto front over knob combinations</h1>
<p class="sub">Stage 5. {n_all:,} sets evaluated (all singles/pairs/triples + greedy path); {len(front)} are non-dominated. Multi-knob response = sum of single-knob x* (linear), scored jointly.</p>
<div class="lead">The frontier is the set of interventions where you can't gain benefit without adding cost. Best benefit-per-cost knee: <b>{" + ".join(knee["S"]) if knee else "—"}</b> (benefit {knee["benefit"]:+.4f}, cost {knee["cost"]:.2f}).</div>
<img src="pareto_front.png" alt="pareto front">
<h2>The Pareto frontier</h2>
<table><tr><th>#</th><th>size</th><th>knob set</th><th>benefit</th><th>cost</th></tr>
{rows_html}</table>
<p style="color:var(--muted);font-size:12px;margin-top:16px;border-top:1px solid var(--line);padding-top:10px">
Benefit = Σ wᵢ(|dᵢ|−|x*ᵢ−dᵢ|) on the combined state · cost = ‖p‖₁ + off-target movement · α=0.15, γ=1.0.
Combinations ≤3 exhaustive + greedy to size 16. Confidence bands (Stage 4) apply per set.</p>
</div></body></html>"""
    (OUT / "pareto_front.html").write_text(html)
    md = ["# Benefit–cost Pareto front (Stage 5)", "",
          f"{n_all:,} sets evaluated; {len(front)} non-dominated. Knee (best benefit/cost): "
          f"**{' + '.join(knee['S']) if knee else '—'}**.", "",
          "| # | size | knob set | benefit | cost |", "|---|---|---|---|---|"]
    for i, p in enumerate(front, 1):
        md.append(f"| {i} | {p['size']} | {' + '.join(p['S'])} | {p['benefit']:+.4f} | {p['cost']:.3f} |")
    (OUT / "pareto_front.md").write_text("\n".join(md) + "\n")


def main():
    nodes = pd.read_csv(OUT / "nodes.csv"); edges = pd.read_csv(OUT / "edges_regulatory.csv")
    node_list = nodes["gene"].astype(str).tolist()
    rows = build_target()
    genes, resp, indeg = single_knob_responses(edges, node_list, rows)
    target_genes = {r["gene"] for r in rows}
    pts = brute_combos(genes, resp, rows, target_genes, indeg)      # exhaustive: all 2^n − 1 subsets
    pts += greedy_forward(genes, resp, rows, target_genes, indeg)   # cross-check (should be dominated)
    # dedup by set
    seen, uniq = set(), []
    for p in pts:
        key = tuple(sorted(p["S"]))
        if key not in seen:
            seen.add(key); uniq.append(p)
    front = pareto_front(uniq)
    # collapse identical (benefit, cost) points — e.g. the many zero-benefit single sinks
    ded, seen_bc = [], set()
    for p in sorted(front, key=lambda p: (p["cost"], -p["benefit"], p["size"])):
        key = (round(p["benefit"], 5), round(p["cost"], 3))
        if key not in seen_bc:
            seen_bc.add(key); ded.append(p)
    front = ded
    front_plot(uniq, front); build_report(front, len(uniq))
    print(f"evaluated {len(uniq):,} unique sets | front {len(front)} points")
    print("frontier (cost → benefit):")
    for p in front:
        print(f"  size {p['size']}  B={p['benefit']:+.4f}  C={p['cost']:.2f}  {' + '.join(p['S'])}")
    return front


if __name__ == "__main__":
    main()
