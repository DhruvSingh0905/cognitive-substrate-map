"""Dual report: markdown + interactive pyvis HTML of the built substrate."""
from pathlib import Path
import pandas as pd
from pyvis.network import Network

OUT = Path(__file__).parent / "output"
COLORS = {"intervention": "#4e79a7", "trap": "#e15759",
          "readout": "#f28e2b", "expanded": "#bab0ac"}


def build_html(nodes_csv=OUT / "nodes.csv", edges_csv=OUT / "edges.csv",
               out_html=OUT / "substrate.html") -> Path:
    nodes = pd.read_csv(nodes_csv)
    edges = pd.read_csv(edges_csv)
    net = Network(height="800px", width="100%", bgcolor="#0f1115",
                  font_color="#e8eaed", notebook=False)
    for _, r in nodes.iterrows():
        be = float(r["brain_enrichment"])
        net.add_node(str(r["gene"]), label=str(r["gene"]),
                     color=COLORS.get(r["klass"], "#999999"),
                     size=10 + 40 * be,
                     title=(f"{r['gene']} | {r['klass']} | brain {be:.2f} | "
                            f"{int(r['n_diseases'])} diseases | promisc {int(r['promiscuity'])}"))
    present = set(nodes["gene"].astype(str))
    for _, e in edges.iterrows():
        s, t = str(e["source"]), str(e["target"])
        if s in present and t in present:
            net.add_edge(s, t, color="#33384a")
    net.force_atlas_2based()
    out_html.parent.mkdir(parents=True, exist_ok=True)
    net.save_graph(str(out_html))
    return out_html


def build_core_html(nodes_csv=OUT / "nodes.csv", edges_csv=OUT / "edges.csv",
                    out_html=OUT / "core.html",
                    classes=("intervention", "input", "readout", "trap")) -> Path:
    """Render ONLY the curated core (no 'expanded' flood) — loads in any browser."""
    nodes = pd.read_csv(nodes_csv)
    core = nodes[nodes["klass"].isin(classes)]
    coreset = set(core["gene"].astype(str))
    edges = pd.read_csv(edges_csv)
    net = Network(height="850px", width="100%", bgcolor="#0f1115",
                  font_color="#e8eaed", notebook=False)
    net.barnes_hut(gravity=-8000, spring_length=120)
    for _, r in core.iterrows():
        be = float(r["brain_enrichment"])
        net.add_node(str(r["gene"]), label=str(r["gene"]),
                     color=COLORS.get(r["klass"], "#999999"), size=12 + 35 * be,
                     title=(f"{r['gene']} | {r['klass']} | brain {be:.2f} | "
                            f"{int(r['n_diseases'])} diseases | promisc {int(r['promiscuity'])}"))
    for _, e in edges.iterrows():
        s, t = str(e["source"]), str(e["target"])
        if s in coreset and t in coreset:
            net.add_edge(s, t, color="#33384a")
    out_html.parent.mkdir(parents=True, exist_ok=True)
    net.save_graph(str(out_html))
    return out_html


def build_regulatory_html(nodes_csv=OUT / "nodes.csv",
                          reg_csv=OUT / "edges_regulatory.csv",
                          out_html=OUT / "regulatory.html",
                          classes=("intervention", "input", "readout", "trap")) -> Path:
    """Directed, signed regulatory network (green=activation, red=inhibition)."""
    nodes = pd.read_csv(nodes_csv)
    core = nodes[nodes["klass"].isin(classes)]
    coreset = set(core["gene"].astype(str))
    reg = pd.read_csv(reg_csv)
    reg = reg[reg["source"].isin(coreset) & reg["target"].isin(coreset)]
    present = set(reg["source"]) | set(reg["target"])

    net = Network(height="860px", width="100%", bgcolor="#0f1115",
                  font_color="#e8eaed", directed=True, notebook=False)
    net.barnes_hut(gravity=-9000, spring_length=130)
    for _, r in core[core["gene"].isin(present)].iterrows():
        g = str(r["gene"])
        net.add_node(g, label=g, color=COLORS.get(r["klass"], "#999999"),
                     size=14, title=f"{g} | {r['klass']}")
    sign_color = {1: "#4caf7d", -1: "#e15759", 0: "#7b8494"}
    for _, e in reg.iterrows():
        net.add_edge(str(e["source"]), str(e["target"]),
                     color=sign_color.get(int(e["sign"]), "#7b8494"), arrows="to",
                     title=f"sign={int(e['sign'])} · {int(e['n_sources'])} sources")
    out_html.parent.mkdir(parents=True, exist_ok=True)
    net.save_graph(str(out_html))
    return out_html


CASCADE = ["BDNF", "NTRK2", "CREB1", "CREBBP", "PRKACA", "ADCY1", "CAMK2A",
           "JUN", "FOS", "ARC", "EGR1", "NFKB1", "RELA", "GRIN2B",
           "ADORA1", "ADORA2A", "ADRB2", "NR3C1"]
CASCADE_DRUGS = ["Caffeine", "Carbamazepine", "Lamotrigine", "Fluoxetine", "Ketamine"]
STATUS_W = {"literature·in-brain": 6, "literature·directional": 3,
            "IUPHAR·potency": 3, "sign-only": 1.5}


def build_cascade_html(nodes_csv=OUT / "nodes.csv", reg_csv=OUT / "edges_regulatory.csv",
                       out_html=OUT / "cascade_magnitudes.html") -> Path:
    """Interactive learning-cascade view with REAL magnitudes labelled on the edges."""
    from cognitive_map.magnitudes import drug_magnitudes
    nodes = pd.read_csv(nodes_csv)
    klass = dict(zip(nodes["gene"].astype(str), nodes["klass"]))
    cset = set(CASCADE)

    net = Network(height="860px", width="100%", bgcolor="#0f1115",
                  font_color="#e8eaed", directed=True, notebook=False)
    net.barnes_hut(gravity=-12000, spring_length=160)

    for g in CASCADE:
        net.add_node(g, label=g, color=COLORS.get(klass.get(g, "expanded"), "#999999"),
                     size=18, title=f"{g} | {klass.get(g,'?')}")
    for d in CASCADE_DRUGS:
        net.add_node(d, label=d, color="#e8c468", shape="diamond", size=16, title=f"{d} (drug)")

    # regulatory edges among cascade genes (sign from OmniPath)
    reg = pd.read_csv(reg_csv)
    reg = reg[reg["source"].isin(cset) & reg["target"].isin(cset)]
    sc = {1: "#4caf7d", -1: "#e15759", 0: "#7b8494"}
    for _, e in reg.iterrows():
        s = int(e["sign"])
        net.add_edge(str(e["source"]), str(e["target"]), arrows="to",
                     color=sc[s], width=STATUS_W["sign-only"],
                     label={1: "+", -1: "−", 0: "?"}[s],
                     title=f"OmniPath · sign={s} · magnitude: sign-only (no number) · {int(e['n_sources'])} sources")

    # drug -> gene magnitudes (literature gold + IUPHAR potency)
    for m in drug_magnitudes(CASCADE_DRUGS):
        if m["gene"] in cset:
            net.add_edge(m["drug"], m["gene"], arrows="to", color="#f0a23c",
                         width=STATUS_W.get(m["status"], 3), label=m["value"],
                         title=f"{m['drug']} → {m['gene']}  =  {m['value']}\n[{m['status']}]  {m['source']}")
    out_html.parent.mkdir(parents=True, exist_ok=True)
    net.save_graph(str(out_html))
    return out_html


def build_markdown(nodes_csv=OUT / "nodes.csv",
                   out_md=OUT / "substrate_report.md") -> Path:
    nodes = pd.read_csv(nodes_csv)
    lines = ["# Cognitive Substrate — Phase 1 Report", ""]
    lines.append(f"**Total nodes:** {len(nodes)}")
    for k, n in nodes["klass"].value_counts().items():
        lines.append(f"- {k}: {n}")
    lines += ["", "## Top 25 by brain-enrichment", "",
              "| gene | class | brain | diseases | promisc |",
              "|---|---|---|---|---|"]
    for _, r in nodes.head(25).iterrows():
        lines.append(f"| {r['gene']} | {r['klass']} | {r['brain_enrichment']} "
                     f"| {int(r['n_diseases'])} | {int(r['promiscuity'])} |")
    out_md.write_text("\n".join(lines) + "\n")
    return out_md
