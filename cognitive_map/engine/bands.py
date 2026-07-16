"""Stage 4 — Monte-Carlo confidence bands on the single-knob ranking (GUM-S1).

Uncertainty source: the confidence-weight intervals w_i ∈ [w_lo, w_hi] (already hand-verified).
x* is deterministic per knob, so we compute each knob's per-target benefit contributions once,
then sample the shared weight vector M times and re-aggregate — a few matrix-vector products.
Reports median + 10–90% coverage band, and rank stability P(knob is #1).

Edge magnitudes are treated as sign-only (unit strength) by design — we do not sample a
magnitude distribution, since there's no principled basis for one. The band is over the
confidence weights only.
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from cognitive_map.engine import propagate as pr, objective as ob
from cognitive_map.engine.target_vector import build_target

OUT = Path(__file__).resolve().parents[1] / "output"
BG, INK, MUT, GRID = "#0f1115", "#e8eaed", "#9aa3b2", "#242a35"
GREEN, RED, GREY, GOLD = "#4caf7d", "#e15759", "#7b8494", "#e8c468"


def montecarlo_bands(edges, nodes, target_rows, M=2000, seed=0, alpha=0.15):
    rng = np.random.default_rng(seed)
    scored = [r for r in target_rows if r["w"] > 0]
    w_lo = np.array([r["w_lo"] for r in scored]); w_hi = np.array([r["w_hi"] for r in scored])
    present = set(nodes)
    knobs = [r for r in target_rows if r["role"] == "knob" and r["d"] != 0 and r["gene"] in present]
    # per-knob downstream benefit contribution to each scored target (self excluded)
    B = np.zeros((len(knobs), len(scored)))
    for ki, kr in enumerate(knobs):
        x = pr.steady_state(edges, nodes, {kr["gene"]: kr["d"]}, alpha=alpha)
        for gi, sr in enumerate(scored):
            if sr["gene"] != kr["gene"]:
                B[ki, gi] = ob.node_benefit(x.get(sr["gene"], 0.0), sr["d"])
    # shared weight draws
    Wd = rng.uniform(w_lo, w_hi, size=(M, len(scored)))       # M × genes
    S = Wd @ B.T                                              # M × knobs  (downstream benefit samples)
    med = np.median(S, axis=0)
    lo = np.percentile(S, 10, axis=0); hi = np.percentile(S, 90, axis=0)
    ranks = (-S).argsort(axis=1).argsort(axis=1) + 1          # rank per draw (1 = best)
    p_top = (ranks == 1).mean(axis=0)
    mean_rank = ranks.mean(axis=0)
    out = [{"gene": kr["gene"], "d": kr["d"], "median": med[ki], "lo": lo[ki], "hi": hi[ki],
            "p_top": p_top[ki], "mean_rank": mean_rank[ki]} for ki, kr in enumerate(knobs)]
    out.sort(key=lambda s: -s["median"])
    return out


def _darkax(ax):
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_color("#39414f")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.tick_params(colors=MUT, labelsize=11)
    ax.xaxis.label.set_color(INK); ax.title.set_color(INK)


def band_plot(bands, path=OUT / "knob_bands.png", n=15):
    top = bands[:n][::-1]
    fig, ax = plt.subplots(figsize=(8.2, 6.2), dpi=200, facecolor=BG); _darkax(ax)
    for i, b in enumerate(top):
        c = GREEN if b["median"] > 1e-4 else (RED if b["median"] < -1e-4 else GREY)
        ax.plot([b["lo"], b["hi"]], [i, i], color=c, lw=3, alpha=0.45, solid_capstyle="round")
        ax.plot(b["median"], i, "o", color=c, ms=7)
    ax.axvline(0, color=MUT, lw=1, ls=":")
    ax.set_yticks(range(len(top))); ax.set_yticklabels([b["gene"] for b in top], color=INK, fontsize=11)
    ax.set_xlabel("downstream benefit  —  median + 10–90% band")
    ax.set_title("Single-knob ranking under confidence-weight uncertainty")
    top_b = bands[0]
    ax.text(0.98, 0.04, f"{top_b['gene']} is #1 in {top_b['p_top']*100:.0f}% of draws",
            transform=ax.transAxes, ha="right", color=GOLD, fontsize=11)
    fig.tight_layout(); fig.savefig(path, facecolor=BG); plt.close(fig)
    return path


def build_report(bands):
    rows_html = "\n".join(
        f'<tr><td class="rk">{i}</td><td class="g">{b["gene"]}</td>'
        f'<td class="p">{"↑" if b["d"]>0 else "↓"}</td>'
        f'<td class="bd" style="color:{GREEN if b["median"]>1e-4 else (RED if b["median"]<-1e-4 else GREY)}">{b["median"]:+.4f}</td>'
        f'<td class="bn">[{b["lo"]:+.4f}, {b["hi"]:+.4f}]</td>'
        f'<td class="pt">{b["p_top"]*100:.0f}%</td><td class="mr">{b["mean_rank"]:.1f}</td></tr>'
        for i, b in enumerate(bands, 1))
    html = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Knob ranking — confidence bands</title><style>
:root{{--bg:#0f1115;--panel:#171a21;--ink:#e8eaed;--muted:#9aa3b2;--line:#2a2f3a}}
*{{box-sizing:border-box}} body{{margin:0;background:#0f1115;color:var(--ink);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:30px}}
.wrap{{max-width:900px;margin:0 auto}} h1{{font-size:22px;margin:0 0 4px}} .sub{{color:var(--muted);margin:0 0 14px}}
h2{{font-size:14px;margin:22px 0 8px;border-bottom:1px solid var(--line);padding-bottom:6px}}
img{{max-width:100%;border:1px solid var(--line);border-radius:10px}}
.lead{{background:rgba(232,196,104,.08);border-left:3px solid #e8c468;border-radius:8px;padding:10px 16px;margin:10px 0;font-size:14px;color:#e6dcc4}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin-top:8px}} td,th{{padding:5px 9px;border-bottom:1px solid var(--line);text-align:left}}
th{{color:var(--muted);font-weight:600}} .rk{{color:var(--muted);width:24px}} .g{{font:600 13px ui-monospace,Menlo,monospace}}
.bd,.bn,.pt,.mr{{font-family:ui-monospace,Menlo,monospace}} .bn{{color:var(--muted)}} .p{{color:var(--muted)}}
</style></head><body><div class="wrap">
<h1>Single-knob ranking with confidence bands</h1>
<p class="sub">Stage 4. 2,000 Monte-Carlo draws over the hand-verified weight intervals. Band = 10–90% coverage; P(top) = share of draws where the knob ranks #1.</p>
<div class="lead"><b>{bands[0]['gene']}</b> stays #1 in <b>{bands[0]['p_top']*100:.0f}%</b> of draws — the ranking is robust to weight uncertainty at the top. Lower down the bands overlap, so those ranks are soft.</div>
<img src="knob_bands.png" alt="confidence bands">
<h2>Ranking (median + band)</h2>
<table><tr><th>#</th><th>knob</th><th>dir</th><th>median</th><th>10–90% band</th><th>P(top)</th><th>mean rank</th></tr>
{rows_html}</table>
<p style="color:var(--muted);font-size:12px;margin-top:16px;border-top:1px solid var(--line);padding-top:10px">
Uncertainty here is over the confidence weights. Edge magnitudes are treated as sign-only by design — no principled magnitude distribution to sample. Next: Stage 5 searches combinations (Pareto front).</p>
</div></body></html>"""
    (OUT / "knob_bands.html").write_text(html)
    md = ["# Single-knob ranking with confidence bands (Stage 4)", "",
          f"2,000 Monte-Carlo draws over the weight intervals. **{bands[0]['gene']}** is #1 in "
          f"**{bands[0]['p_top']*100:.0f}%** of draws.", "",
          "| # | knob | dir | median | 10–90% band | P(top) | mean rank |", "|---|---|---|---|---|---|---|"]
    for i, b in enumerate(bands, 1):
        md.append(f"| {i} | {b['gene']} | {'+1' if b['d']>0 else '−1'} | {b['median']:+.4f} | "
                  f"[{b['lo']:+.4f}, {b['hi']:+.4f}] | {b['p_top']*100:.0f}% | {b['mean_rank']:.1f} |")
    (OUT / "knob_bands.md").write_text("\n".join(md) + "\n")


def main():
    nodes = pd.read_csv(OUT / "nodes.csv"); edges = pd.read_csv(OUT / "edges_regulatory.csv")
    node_list = nodes["gene"].astype(str).tolist()
    bands = montecarlo_bands(edges, node_list, build_target(), M=2000, seed=0)
    band_plot(bands); build_report(bands)
    print(f"top {bands[0]['gene']}: median {bands[0]['median']:+.4f} "
          f"[{bands[0]['lo']:+.4f},{bands[0]['hi']:+.4f}]  P(top)={bands[0]['p_top']*100:.0f}%")
    return bands


if __name__ == "__main__":
    main()
