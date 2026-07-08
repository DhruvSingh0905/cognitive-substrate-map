"""Hand-verifiable propagation check (Phase 3 gate).

Runs a few unit perturbations on the REAL substrate and checks x* against signs read
straight out of edges_regulatory.csv — so every prediction is derivable by hand from the
data, not from the model. Emits md + HTML for hand-verification BEFORE the objective
(Stage 3) is allowed to consume x*.

Each probe: perturb one gene +1, and for a set of direct-edge targets state the sign we
EXPECT (from the CSV edge) vs the sign the engine OBSERVED. Direct-edge signs must match;
multi-hop nodes are reported as net-of-feedback (informative, not asserted).
"""
from pathlib import Path
import numpy as np
import pandas as pd

from cognitive_map.engine import operator as op
from cognitive_map.engine import propagate as pr

OUT = Path(__file__).resolve().parents[1] / "output"
ALPHA = 0.15

# probe = (perturbed gene, [(target, hops, mechanism)]). Signs are looked up live from the CSV.
PROBES = [
    ("CREB1", [("BDNF", 1, "CREB1→BDNF transcription"),
               ("EGR1", 1, "CREB1→EGR1 (Zif268)"),
               ("TH", 1, "CREB1→TH catecholamine synthesis"),
               ("JUN", 1, "CREB1⊣JUN (repressive edge — sign FLIP)"),
               ("NTRK2", 2, "CREB1→BDNF→NTRK2 (TrkB), net")]),
    ("AKT1", [("CHUK", 1, "AKT1→CHUK/IKKα"),
              ("NFKB1", 2, "AKT1→CHUK⊣NFKB1, net sign-flip")]),
    ("GSK3B", [("CREB1", 1, "GSK3B⊣CREB1 (inhibitory — sign FLIP)")]),
]


def _direct_sign(edges, s, t):
    row = edges[(edges.source == s) & (edges.target == t)]["sign"].values
    return int(row[0]) if len(row) else None


def analyze():
    nodes = pd.read_csv(OUT / "nodes.csv")["gene"].astype(str).tolist()
    edges = pd.read_csv(OUT / "edges_regulatory.csv")
    W, _ = op.signed_weight_matrix(edges, nodes)
    What = op.normalize(W)
    rho = op.spectral_radius(What)
    used = int((W != 0).sum())

    probes = []
    for gene, targets in PROBES:
        x = pr.steady_state(edges, nodes, {gene: 1.0}, alpha=ALPHA)
        xv = np.array([x[n] for n in nodes])
        checks = []
        for t, hops, mech in targets:
            ds = _direct_sign(edges, gene, t) if hops == 1 else None
            obs = x.get(t, float("nan"))
            obs_sign = int(np.sign(obs)) if abs(obs) > 1e-9 else 0
            match = None if hops > 1 else (obs_sign == ds)
            checks.append({"target": t, "hops": hops, "mech": mech,
                           "edge_sign": ds, "observed": obs, "obs_sign": obs_sign,
                           "match": match})
        movers = sorted(((n, x[n]) for n in nodes if n != gene),
                        key=lambda kv: -abs(kv[1]))[:10]
        probes.append({"gene": gene, "source_val": x[gene], "checks": checks,
                       "movers": movers,
                       "oversmoothed": pr.is_oversmoothed(xv),
                       "resp_std": float(xv.std())})
    return {"n_nodes": len(nodes), "n_edges_used": used, "rho": rho,
            "alpha": ALPHA, "probes": probes}


# ---------------- rendering (md + HTML) ----------------
def build_md(r, path=OUT / "propagation_verify.md"):
    L = ["# Propagation engine — hand-verification (Phase 3 gate)", "",
         f"Substrate: **{r['n_nodes']} nodes**, **{r['n_edges_used']} signed edges** used · "
         f"α = {r['alpha']} · **ρ(Ŵ) = {r['rho']:.3f}** (≤1 ⇒ resolvent converges).", "",
         "Every direct-edge prediction below is read from `edges_regulatory.csv`, not the model. "
         "Direct edges must match sign; multi-hop rows are net-of-feedback.", ""]
    for p in r["probes"]:
        L += [f"## Perturb `{p['gene']}` +1.0  (source x* = {p['source_val']:+.4f})",
              f"over-smoothed: **{p['oversmoothed']}** · response σ = {p['resp_std']:.4f}", "",
              "| target | hops | edge sign | observed x* | obs sign | match | mechanism |",
              "|---|---|---|---|---|---|---|"]
        for c in p["checks"]:
            es = {1: "+1", -1: "−1", None: "—"}[c["edge_sign"]]
            m = "n/a" if c["match"] is None else ("✅" if c["match"] else "❌")
            L.append(f"| {c['target']} | {c['hops']} | {es} | {c['observed']:+.4f} | "
                     f"{c['obs_sign']:+d} | {m} | {c['mech']} |")
        L += ["", "Top movers: " + ", ".join(f"{g} ({v:+.4f})" for g, v in p["movers"]), ""]
    path.write_text("\n".join(L) + "\n")
    return path


def build_html(r, path=OUT / "propagation_verify.html"):
    def rows(p):
        out = []
        for c in p["checks"]:
            es = {1: "+1", -1: "−1", None: "—"}[c["edge_sign"]]
            cls = "" if c["match"] is None else ("ok" if c["match"] else "bad")
            m = "net" if c["match"] is None else ("✓ match" if c["match"] else "✗ MISMATCH")
            col = "#4caf7d" if c["observed"] >= 0 else "#e15759"
            out.append(
                f'<tr class="{cls}"><td class="g">{c["target"]}</td><td>{c["hops"]}</td>'
                f'<td>{es}</td><td style="color:{col};font-family:ui-monospace">{c["observed"]:+.4f}</td>'
                f'<td>{m}</td><td class="mech">{c["mech"]}</td></tr>')
        return "\n".join(out)

    probes = []
    for p in r["probes"]:
        movers = " · ".join(
            f'<span style="color:{"#4caf7d" if v>=0 else "#e15759"}">{g} {v:+.4f}</span>'
            for g, v in p["movers"])
        probes.append(f"""<div class="probe"><h2>perturb <code>{p['gene']}</code> +1.0
      <span class="src">source x* = {p['source_val']:+.4f} · over-smoothed: {p['oversmoothed']} · σ={p['resp_std']:.4f}</span></h2>
      <table><tr><th>target</th><th>hops</th><th>edge</th><th>observed x*</th><th>check</th><th>mechanism</th></tr>
      {rows(p)}</table><div class="movers"><b>top movers:</b> {movers}</div></div>""")

    html = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Propagation engine — hand-verification</title><style>
:root{{--bg:#0f1115;--panel:#171a21;--ink:#e8eaed;--muted:#9aa3b2;--line:#2a2f3a}}
*{{box-sizing:border-box}} body{{margin:0;background:linear-gradient(180deg,#0f1115,#0c0e12);color:var(--ink);
font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:30px}}
.wrap{{max-width:1000px;margin:0 auto}} h1{{font-size:23px;margin:0 0 4px}}
.sub{{color:var(--muted);margin:0 0 8px}} .kpi{{background:var(--panel);border:1px solid var(--line);
border-radius:12px;padding:12px 18px;margin:14px 0 22px;font-size:14px}} .kpi b{{color:#8fd6a8}}
.probe{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:8px 18px 16px;margin:16px 0}}
h2{{font-size:15px;margin:14px 0 8px}} h2 .src{{color:var(--muted);font-weight:400;font-size:12px;margin-left:8px}}
code{{background:#1d212b;padding:1px 6px;border-radius:4px}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin:6px 0}}
td,th{{padding:5px 9px;border-bottom:1px solid var(--line);text-align:left}} th{{color:var(--muted);font-weight:600}}
.g{{font:600 13px ui-monospace,Menlo,monospace}} .mech{{color:#cfd6e2;font-size:12px}}
tr.ok td{{background:rgba(76,175,125,.07)}} tr.bad td{{background:rgba(225,87,89,.12)}}
.movers{{color:var(--muted);font-size:12px;margin-top:8px}} .movers span{{font-family:ui-monospace,Menlo,monospace}}
.note{{color:var(--muted);font-size:12px;margin-top:18px;border-top:1px solid var(--line);padding-top:10px}}
</style></head><body><div class="wrap">
<h1>Propagation engine — hand-verification</h1>
<p class="sub">Phase-3 gate. Every direct-edge prediction is read from <code>edges_regulatory.csv</code>, not the model.</p>
<div class="kpi"><b>{r['n_nodes']}</b> nodes · <b>{r['n_edges_used']}</b> signed edges · α = {r['alpha']} ·
<b>ρ(Ŵ) = {r['rho']:.3f}</b> (≤ 1 ⇒ the (I−(1−α)Ŵ)⁻¹ resolvent converges).</div>
{''.join(probes)}
<p class="note">Green x* = node moved up, red = down. Direct-edge (1-hop) rows must match the CSV sign;
multi-hop rows are net-of-feedback through the 200-node core, reported not asserted. Magnitudes are raw x*
(deviation-from-baseline) at unit perturbation — read <b>signs and relative sizes</b>, not absolute %, per the
linearization caveat. Nothing enters the objective until these signs check out.</p>
</div></body></html>"""
    path.write_text(html)
    return path


if __name__ == "__main__":
    r = analyze()
    print(build_md(r))
    print(build_html(r))
    # console summary
    print(f"\nnodes={r['n_nodes']} edges_used={r['n_edges_used']} rho={r['rho']:.3f} alpha={r['alpha']}")
    for p in r["probes"]:
        print(f"\nperturb {p['gene']} (+1) -> source {p['source_val']:+.4f} oversmoothed={p['oversmoothed']}")
        for c in p["checks"]:
            m = "net" if c["match"] is None else ("MATCH" if c["match"] else "MISMATCH")
            print(f"  {c['target']:<7} hops={c['hops']} edge={c['edge_sign']} obs={c['observed']:+.4f} [{m}]")
