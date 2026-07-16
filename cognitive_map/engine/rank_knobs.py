"""First result: single-knob importance ranking (Phase 3b).  md + HTML.

Push each actionable knob (role=knob, d≠0) in its target direction, propagate, score the
whole-state effect. Ranked by DOWNSTREAM benefit (network leverage — excludes the knob's own move).
Out-degree column explains why sinks score ~0: no out-edges → nothing cascades.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from cognitive_map.engine import operator as op, objective as ob
from cognitive_map.engine.target_vector import build_target

OUT = Path(__file__).resolve().parents[1] / "output"
CM = Path(__file__).resolve().parents[1] / "output"


def compute():
    nodes = pd.read_csv(CM / "nodes.csv"); edges = pd.read_csv(CM / "edges_regulatory.csv")
    node_list = nodes["gene"].astype(str).tolist()
    rows = build_target()
    W, idx = op.signed_weight_matrix(edges, node_list)
    dout = np.abs(W).sum(axis=0)
    rank = ob.rank_single_knobs(edges, node_list, rows, alpha=0.15, gamma=1.0)
    for s in rank:
        s["out_deg"] = int(dout[idx[s["gene"]]])
    return rank


CAVEATS = [
    "<b>Downstream benefit is the leverage signal.</b> It excludes the knob's own move, so it answers "
    "\"what does pushing this gene do to <i>everything else</i>?\" B_total adds the knob's own ~0.15.",
    "<b>Constrained to un-defended drivers.</b> Candidates are limited to druggable knobs that can cascade "
    "(out-degree&gt;0) and aren't defended hubs (in-degree ≤ 10). Defended convergence nodes like BDNF and CREB1 are "
    "excluded — they're targets we move <i>indirectly</i>, not levers we push directly (homeostasis fights that).",
    "<b>Negatives are real anti-signals.</b> CHRNA7 and the glial NF-κB genes move scored targets the <i>wrong</i> way "
    "downstream — pushing them hurts the state.",
    "<b>This is pre-uncertainty and single-knob.</b> No confidence band yet (Stage 4) and no combinations (Stage 5); "
    "magnitudes are small (linear, near-baseline) so read the <i>ranking</i>, not the absolute numbers.",
]


def build_html(rank, path=OUT / "knob_ranking.html"):
    def rows_html():
        out = []
        for i, s in enumerate(rank, 1):
            bd = s["B_downstream"]
            col = "#4caf7d" if bd > 1e-4 else ("#e15759" if bd < -1e-4 else "#7b8494")
            sink = ' <span class="sink">sink</span>' if s["out_deg"] == 0 else ""
            out.append(
                f'<tr><td class="rk">{i}</td><td class="g">{s["gene"]}</td>'
                f'<td class="p">{"↑ +1" if s["d"]>0 else "↓ −1"}</td>'
                f'<td class="od">{s["out_deg"]}{sink}</td>'
                f'<td class="bd" style="color:{col}">{bd:+.4f}</td>'
                f'<td class="bt">{s["B_total"]:+.4f}</td><td class="ct">{s["cost"]:.3f}</td></tr>')
        return "\n".join(out)
    cav = "".join(f"<li>{c}</li>" for c in CAVEATS)
    top = rank[0]
    html = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Single-knob ranking — first result</title><style>
:root{{--bg:#0f1115;--panel:#171a21;--ink:#e8eaed;--muted:#9aa3b2;--line:#2a2f3a}}
*{{box-sizing:border-box}} body{{margin:0;background:#0f1115;color:var(--ink);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:30px}}
.wrap{{max-width:940px;margin:0 auto}} h1{{font-size:22px;margin:0 0 4px}} .sub{{color:var(--muted);margin:0 0 16px}}
h2{{font-size:14px;margin:22px 0 8px;border-bottom:1px solid var(--line);padding-bottom:6px}}
.lead{{background:rgba(76,175,125,.08);border-left:3px solid #4caf7d;border-radius:8px;padding:10px 16px;margin:12px 0;font-size:14px;color:#cfe3d6}}
.find{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:6px 20px;margin:12px 0}} .find li{{margin:8px 0;color:#cfd6e2}} .find b{{color:#fff}}
table{{border-collapse:collapse;width:100%;font-size:13px}} td,th{{padding:5px 9px;border-bottom:1px solid var(--line);text-align:left}}
th{{color:var(--muted);font-weight:600}} .rk{{color:var(--muted);width:26px}} .g{{font:600 13px ui-monospace,Menlo,monospace}}
.p{{font-family:ui-monospace,Menlo,monospace;font-size:12px}} .od{{color:var(--muted);font-family:ui-monospace,Menlo,monospace}}
.bd,.bt,.ct{{font-family:ui-monospace,Menlo,monospace;text-align:right}} .bt,.ct{{color:var(--muted)}}
.sink{{background:rgba(123,132,148,.2);color:#9aa3b2;font-size:10px;padding:1px 5px;border-radius:4px}}
</style></head><body><div class="wrap">
<h1>Single-knob importance ranking</h1>
<p class="sub">Each <b>un-defended upstream driver</b> (constrained set) pushed in its target direction; ranked by downstream benefit. {len(rank)} candidates.</p>
<div class="lead"><b>{top['gene']}</b> is the top un-defended upstream driver, with <b>{top['B_downstream']:+.4f}</b> downstream benefit. Benefit is modest — the un-defended drivers have less reach than the defended hubs (BDNF, CREB1) we deliberately don't push directly.</div>
<h2>How to read this</h2>
<div class="find"><ul>{cav}</ul></div>
<h2>Ranking</h2>
<table><tr><th>#</th><th>knob</th><th>push</th><th>out-deg</th><th>B&#8209;downstream</th><th>B&#8209;total</th><th>cost</th></tr>
{rows_html()}</table>
<p style="color:var(--muted);font-size:12px;margin-top:18px;border-top:1px solid var(--line);padding-top:10px">
α=0.15 · γ=1.0 · benefit = Σ wᵢ(|dᵢ|−|x*ᵢ−dᵢ|) over scored targets. Next: Stage 4 wraps each row in a Monte-Carlo confidence band; Stage 5 searches combinations.</p>
</div></body></html>"""
    path.write_text(html); return path


def build_md(rank, path=OUT / "knob_ranking.md"):
    L = ["# Single-knob importance ranking — first result", "",
         f"Each actionable knob pushed in its target direction; ranked by **downstream benefit**. {len(rank)} candidates.", "",
         "## How to read this"]
    for c in CAVEATS:
        L.append("- " + c.replace("<b>", "**").replace("</b>", "**").replace("<i>", "*").replace("</i>", "*"))
    L += ["", "## Ranking", "", "| # | knob | push | out-deg | B_downstream | B_total | cost |",
          "|---|---|---|---|---|---|---|"]
    for i, s in enumerate(rank, 1):
        sink = " (sink)" if s["out_deg"] == 0 else ""
        L.append(f"| {i} | {s['gene']} | {'+1' if s['d']>0 else '−1'} | {s['out_deg']}{sink} | "
                 f"{s['B_downstream']:+.4f} | {s['B_total']:+.4f} | {s['cost']:.3f} |")
    path.write_text("\n".join(L) + "\n"); return path


if __name__ == "__main__":
    rank = compute()
    print(build_md(rank)); print(build_html(rank))
    print(f"\ntop: {rank[0]['gene']} B_down={rank[0]['B_downstream']:+.4f} | "
          f"{sum(1 for s in rank if abs(s['B_downstream'])<1e-4)} knobs at ~0 (sinks) | "
          f"{sum(1 for s in rank if s['B_downstream']<-1e-4)} negative")
