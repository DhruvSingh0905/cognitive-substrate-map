"""Hand-verify report for the Stage-3 objective inputs (d + w).  md + HTML."""
from pathlib import Path
import collections
from cognitive_map.engine.target_vector import build_target

OUT = Path(__file__).resolve().parents[1] / "output"
DCOL = {1.0: "#4caf7d", -1.0: "#e15759", 0.0: "#7b8494"}
DLAB = {1.0: "+1  (up)", -1.0: "−1  (down)", 0.0: "0  (hold)"}
ROLE_ORDER = ["knob", "input", "readout"]
ROLE_LABEL = {"knob": "KNOBS — actionable targets", "input": "INPUTS — systemic drivers",
              "readout": "READOUTS — gauges (w = 0, not optimized)"}

DECISIONS = [
    ("Setpoints → d = 0 (hold at baseline).", "43 genes. Assumes the awake-encoding baseline sits at the "
     "inverted-U peak, so <b>any</b> push is penalized. We have no data on where baseline actually sits on the "
     "curve — d=0 is the honest default. If you think some are off-optimum, we set d≠0 for those."),
    ("Readouts → w = 0 (gauges, not optimized).", "13 genes — the 7 IEG markers (FOS/JUN family) and 6 disease "
     "genes (APP/PSEN/MAPT/MECP2/APOE). We measure them but don't score or push them. Alternative: score the disease "
     "readouts so lowering tau/amyloid counts as benefit."),
    ("Confidence → w = 1.0 / 0.6 / 0.3.", "Point weights for the first ranking; intervals (high [.9,1] · med [.5,.7] "
     "· low [.2,.4]) feed the Monte-Carlo band later. Magnitudes are a choice."),
    ("Benefit form + scale.", "b_i = |d_i| − |x*_i − d_i| with d ∈ {+1,−1,0}. For the small x* we get (~0.003), this "
     "reduces to <b>≈ signed x*</b> — reward moving a gene toward its d, penalize any setpoint deviation. Values are "
     "small but <b>rank</b> cleanly. Note the pushed gene's own x* (≈0.15) dominates its own benefit, so I'll report "
     "<b>total</b> and <b>downstream-only</b> scores separately."),
]


def _summary(rows):
    scored = [r for r in rows if r["scored"]]
    dcount = collections.Counter(r["d"] for r in scored)
    return {"n": len(rows), "scored": len(scored), "unscored": len(rows) - len(scored),
            "up": dcount[1.0], "down": dcount[-1.0], "hold": dcount[0.0]}


def build_html(path=OUT / "target_vector.html"):
    rows = build_target(); s = _summary(rows)
    by_role = collections.defaultdict(list)
    for r in rows:
        by_role[r["role"]].append(r)
    decisions = "".join(f"<li><b>{t}</b> {d}</li>" for t, d in DECISIONS)
    sections = []
    for role in ROLE_ORDER:
        rs = by_role[role]
        body = []
        for r in sorted(rs, key=lambda r: (r["system"], r["gene"])):
            c = DCOL[r["d"]]
            wtxt = "—" if r["w"] == 0 else f'{r["w"]:.1f} <span class="wi">[{r["w_lo"]:.1f},{r["w_hi"]:.1f}]</span>'
            body.append(
                f'<tr><td class="g">{r["gene"]}</td><td class="sys">{r["system"]}</td>'
                f'<td>{r["direction"]}</td><td class="sh">{r["shape"]}</td>'
                f'<td class="cf {r["confidence"]}">{r["confidence"]}</td>'
                f'<td><span class="chip" style="background:{c}">{DLAB[r["d"]]}</span></td>'
                f'<td class="w">{wtxt}</td></tr>')
        sections.append(
            f'<h2>{ROLE_LABEL[role]} <span class="ct">({len(rs)})</span></h2>'
            f'<table><tr><th>gene</th><th>system</th><th>dir</th><th>shape</th><th>conf</th>'
            f'<th>d</th><th>w [band]</th></tr>{"".join(body)}</table>')
    html = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Target vector d + weights w — hand-verify</title><style>
:root{{--bg:#0f1115;--panel:#171a21;--ink:#e8eaed;--muted:#9aa3b2;--line:#2a2f3a}}
*{{box-sizing:border-box}} body{{margin:0;background:#0f1115;color:var(--ink);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:30px}}
.wrap{{max-width:1000px;margin:0 auto}} h1{{font-size:22px;margin:0 0 4px}} .sub{{color:var(--muted);margin:0 0 16px}}
h2{{font-size:14px;margin:24px 0 8px;border-bottom:1px solid var(--line);padding-bottom:6px}} .ct{{color:var(--muted);font-weight:400}}
.cards{{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0}} .card{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 16px}}
.card .n{{font-size:22px;font-weight:700}} .card .l{{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.5px}}
.find{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:6px 20px;margin:12px 0}} .find li{{margin:8px 0;color:#cfd6e2}}
.find b{{color:#fff}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin-bottom:6px}} td,th{{padding:5px 9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}
th{{color:var(--muted);font-weight:600}} .g{{font:600 13px ui-monospace,Menlo,monospace}} .sys{{color:#8fa0d6;font-size:12px}} .sh{{color:var(--muted);font-size:12px}}
.chip{{color:#0c0e12;font:600 12px ui-monospace,Menlo,monospace;padding:2px 8px;border-radius:5px;white-space:nowrap}}
.cf{{font-size:12px}} .cf.high{{color:#4caf7d}} .cf.medium{{color:#f0a23c}} .cf.low{{color:#e15759}}
.w{{font:600 12px ui-monospace,Menlo,monospace}} .wi{{color:var(--muted);font-weight:400}}
</style></head><body><div class="wrap">
<h1>Target vector <code>d</code> + confidence weights <code>w</code></h1>
<p class="sub">WE-built numbers for the Stage-3 objective. <b>Hand-verify before the scorer uses them.</b>
Direction color: <span style="color:#4caf7d">+1 up</span> · <span style="color:#e15759">−1 down</span> · <span style="color:#7b8494">0 hold</span>.</p>
<div class="cards">
  <div class="card"><div class="n">{s['n']}</div><div class="l">genes</div></div>
  <div class="card"><div class="n">{s['scored']}</div><div class="l">scored</div></div>
  <div class="card"><div class="n">{s['unscored']}</div><div class="l">readouts (w=0)</div></div>
  <div class="card"><div class="n">{s['up']}</div><div class="l">d = +1</div></div>
  <div class="card"><div class="n">{s['down']}</div><div class="l">d = −1</div></div>
  <div class="card"><div class="n">{s['hold']}</div><div class="l">d = 0</div></div>
</div>
<h2>Decisions to verify</h2>
<div class="find"><ol>{decisions}</ol></div>
{''.join(sections)}
<p style="color:var(--muted);font-size:12px;margin-top:18px;border-top:1px solid var(--line);padding-top:10px">
Change any <code>d</code> or <code>w</code> by editing the map in <code>engine/target_vector.py</code>, or tell me the edits. Nothing enters the objective until you sign off.</p>
</div></body></html>"""
    path.write_text(html); return path


def build_md(path=OUT / "target_vector.md"):
    rows = build_target(); s = _summary(rows)
    L = ["# Target vector d + confidence weights w — hand-verify", "",
         f"**{s['n']} genes · {s['scored']} scored · {s['unscored']} readouts (w=0) · "
         f"d: {s['up']} up / {s['down']} down / {s['hold']} hold**", "",
         "## Decisions to verify"]
    for t, d in DECISIONS:
        L.append(f"- **{t}** {d.replace('<b>','**').replace('</b>','**')}")
    by_role = collections.defaultdict(list)
    for r in rows:
        by_role[r["role"]].append(r)
    for role in ROLE_ORDER:
        rs = by_role[role]
        L += ["", f"## {ROLE_LABEL[role]} ({len(rs)})", "",
              "| gene | system | dir | shape | conf | d | w | band |", "|---|---|---|---|---|---|---|---|"]
        for r in sorted(rs, key=lambda r: (r["system"], r["gene"])):
            band = "—" if r["w"] == 0 else f"[{r['w_lo']:.1f},{r['w_hi']:.1f}]"
            wv = "—" if r["w"] == 0 else f"{r['w']:.1f}"
            L.append(f"| {r['gene']} | {r['system']} | {r['direction']} | {r['shape']} | "
                     f"{r['confidence']} | {r['d']:+.0f} | {wv} | {band} |")
    path.write_text("\n".join(L) + "\n"); return path


if __name__ == "__main__":
    print(build_md()); print(build_html())
    s = _summary(build_target())
    print(f"\n{s['n']} genes | scored {s['scored']} | readouts(w=0) {s['unscored']} | "
          f"d: +1={s['up']}  -1={s['down']}  0={s['hold']}")
