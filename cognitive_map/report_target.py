"""Render the target-state vector for hand-verification (md + interactive HTML)."""
from pathlib import Path
import pandas as pd
from cognitive_map.target_state import TARGET_STATE, RATIO_TERMS, UNWIRED

OUT = Path(__file__).parent / "output"
DIR_COLOR = {"up": "#4caf7d", "down": "#e15759", "setpoint": "#f0a23c",
             "uncertain": "#7b8494", "marker": "#5b6472"}
ROLE_ORDER = ["knob", "input", "readout"]
ROLE_LABEL = {"knob": "KNOBS — actionable targets", "input": "INPUTS — systemic drivers (high-pleiotropy)",
              "readout": "READOUTS — gauges, NOT knobs"}

FINDINGS = [
    "<b>Setpoints dominate.</b> Almost nothing is monotone 'up' — neuromodulators, E/I balance, cortisol, AMPK, mTOR are inverted-U. 'More' is the #1 way to be wrong.",
    "<b>Knob vs readout.</b> The AP-1 / immediate-early genes (FOS/FOSB/FOSL1-2/JUN/JUNB/JUND) are activity MARKERS, not levers — as is the disease panel (APP/PSEN/MAPT/MECP2/APOE). ARC/EGR1/NR4A1 are the effector-IEGs that do drive consolidation.",
    "<b>mTOR = setpoint, confirmed by TWO independent agents</b> (plasticity + inflammation): translation-for-LTP vs autophagy suppression. AMPK↔mTOR is the metabolic balance node; PRKAA2 is the sharpest inverted-U in the map.",
    "<b>Ratio terms.</b> Some targets are ratios, not per-node values (GluN2A/2B, GluA1/2, GABA supply/reuptake, D1/D2, GR/MR) — the sim must specify these jointly.",
    "<b>Ceilings.</b> Every glutamatergic 'up' is hard-capped by the excitotoxicity ceiling (sharpest at GRIN2B).",
    "<b>Family ≠ one axis.</b> NF-κB: glial RELA/NFKB1 down, but c-Rel (REL) is neuroprotective. Don't collapse.",
]


def _rows_html(df):
    out = []
    for sysname, sub in df.groupby("system", sort=False):
        out.append(f'<tr class="sysrow"><td colspan="5">{sysname}</td></tr>')
        for _, r in sub.iterrows():
            c = DIR_COLOR.get(r["direction"], "#7b8494")
            flag = ' <span class="unwired">unwired</span>' if r["gene"] in UNWIRED else ""
            out.append(
                f'<tr><td class="g">{r["gene"]}{flag}</td>'
                f'<td><span class="chip" style="background:{c}">{r["direction"]}</span></td>'
                f'<td class="sh">{r["shape"]}</td>'
                f'<td class="cf {r["confidence"]}">{r["confidence"]}</td>'
                f'<td class="nt">{r["note"]}</td></tr>')
    return "\n".join(out)


def build_html(out_html=OUT / "target_state.html") -> Path:
    df = pd.DataFrame(TARGET_STATE, columns=["gene", "system", "role", "direction", "shape", "confidence", "note"])
    findings = "".join(f"<li>{f}</li>" for f in FINDINGS)
    ratios = "".join(f"<li><code>{k}</code> — {v[2]} ({v[0]}{'/'+v[1] if v[1] else ''})</li>"
                     for k, v in RATIO_TERMS.items())
    sections = []
    for role in ROLE_ORDER:
        sub = df[df["role"] == role]
        sections.append(
            f'<h2>{ROLE_LABEL[role]} <span class="ct">({len(sub)})</span></h2>'
            f'<table><tr><th>gene</th><th>direction</th><th>shape</th><th>conf</th><th>mechanism / coupling</th></tr>'
            f'{_rows_html(sub)}</table>')
    html = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Target-State Vector — for verification</title><style>
:root{{--bg:#0f1115;--panel:#171a21;--ink:#e8eaed;--muted:#9aa3b2;--line:#2a2f3a}}
*{{box-sizing:border-box}} body{{margin:0;background:#0f1115;color:var(--ink);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:30px}}
.wrap{{max-width:1060px;margin:0 auto}} h1{{font-size:23px;margin:0 0 4px}} .sub{{color:var(--muted);margin:0 0 18px}}
h2{{font-size:15px;margin:26px 0 8px;border-bottom:1px solid var(--line);padding-bottom:6px}} .ct{{color:var(--muted);font-weight:400}}
.find{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 18px}} .find li{{margin:6px 0;color:#cfd6e2}}
.ratio{{background:rgba(240,162,60,.08);border-left:3px solid #f0a23c;border-radius:8px;padding:8px 16px;margin:10px 0;font-size:13px}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin-bottom:6px}} td,th{{padding:5px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}
th{{color:var(--muted);font-weight:600}} .sysrow td{{color:#8fa0d6;font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:.6px;border-bottom:1px solid var(--line);padding-top:12px}}
.g{{font:600 13px ui-monospace,Menlo,monospace;white-space:nowrap}} .chip{{color:#0c0e12;font:600 12px ui-monospace,Menlo,monospace;padding:2px 8px;border-radius:5px}}
.sh{{color:var(--muted);font-size:12px}} .cf{{font-size:12px}} .cf.high{{color:#4caf7d}} .cf.medium{{color:#f0a23c}} .cf.low{{color:#e15759}}
.nt{{color:#cfd6e2;font-size:12px}} .unwired{{background:rgba(225,87,89,.15);color:#e15759;font-size:10px;padding:1px 5px;border-radius:4px}}
code{{background:#1d212b;padding:1px 5px;border-radius:4px;font-size:12px}}
</style></head><body><div class="wrap">
<h1>Target-State Vector — the learning-optimal state</h1>
<p class="sub">Synthesized from 5 parallel research agents. <b>Hand-verify each row before it enters the sim.</b> Direction color: <span style="color:#4caf7d">up</span> · <span style="color:#e15759">down</span> · <span style="color:#f0a23c">setpoint</span> · <span style="color:#7b8494">uncertain/marker</span>.</p>
<h2>What the research established</h2>
<div class="find"><ol>{findings}</ol></div>
<div class="ratio"><b>Ratio terms (specify jointly, not per-node):</b><ul>{ratios}</ul></div>
{''.join(sections)}
<p style="color:var(--muted);font-size:12px;margin-top:20px;border-top:1px solid var(--line);padding-top:10px">
Citations live in the 5 agent evidence reports; PMIDs are literature-grounded but need a verify-pass. Directions are CNS setpoints for a modeled awake-encoding window — not medical advice. <b>Unwired</b> = in-target but pruned (no OmniPath edge).</p>
</div></body></html>"""
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html)
    return out_html


def build_md(out_md=OUT / "target_state.md") -> Path:
    df = pd.DataFrame(TARGET_STATE, columns=["gene", "system", "role", "direction", "shape", "confidence", "note"])
    lines = ["# Target-State Vector — for hand-verification", "",
             "Synthesized from 5 parallel research agents. Hand-verify each row before the sim uses it.", ""]
    lines.append("## What the research established")
    for f in FINDINGS:
        lines.append(f"- {f.replace('<b>','**').replace('</b>','**')}")
    lines.append("")
    for role in ROLE_ORDER:
        sub = df[df["role"] == role]
        lines += [f"## {ROLE_LABEL[role]} ({len(sub)})", "",
                  "| gene | direction | shape | conf | mechanism / coupling |", "|---|---|---|---|---|"]
        for _, r in sub.iterrows():
            uw = " ⚠unwired" if r["gene"] in UNWIRED else ""
            lines.append(f"| {r['gene']}{uw} | {r['direction']} | {r['shape']} | {r['confidence']} | {r['note']} |")
        lines.append("")
    out_md.write_text("\n".join(lines) + "\n")
    return out_md


if __name__ == "__main__":
    print(build_md())
    print(build_html())
