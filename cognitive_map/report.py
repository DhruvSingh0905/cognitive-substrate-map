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
