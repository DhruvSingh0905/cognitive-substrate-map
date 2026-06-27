"""
PrimeKG subgraph explorer — Dash + Cytoscape interactive app.

Schema:
  nodes.csv  (TSV): node_index, node_id, node_type, node_name, node_source
  edges.csv  (CSV): relation, display_relation, x_index, y_index

Usage:
    python explore.py                         # hub ego-graph (top-degree node), 300 nodes
    python explore.py --seed "metformin"      # ego-graph around a node name
    python explore.py --seed "Alzheimer"
    python explore.py --seed "TP53" --hops 2 --limit 500
    python explore.py --ntype drug            # 50 drugs + 1-hop neighbors
    python explore.py --port 8051

Open http://127.0.0.1:8050
"""

import argparse, sys
from pathlib import Path

import pandas as pd
import networkx as nx
import dash
from dash import html, dcc, Input, Output, callback
import dash_cytoscape as cyto

DATA_DIR = Path(__file__).parent / "data" / "primekg"

for f in ("nodes.csv", "edges.csv"):
    if not (DATA_DIR / f).exists():
        sys.exit(f"{f} not found. Run:  python download_primekg.py  first.")

# ── load nodes ────────────────────────────────────────────────────────────────
print("Loading nodes … ", end="", flush=True)
nodes_df = pd.read_csv(DATA_DIR / "nodes.csv", sep="\t",
                       dtype={"node_index": int, "node_type": str,
                              "node_name": str, "node_source": str})
# strip stray quotes
for col in ("node_type", "node_name", "node_source"):
    nodes_df[col] = nodes_df[col].str.strip('"')
idx2name = nodes_df.set_index("node_index")["node_name"].to_dict()
idx2type = nodes_df.set_index("node_index")["node_type"].to_dict()
print(f"{len(nodes_df):,} nodes")

# ── load edges (stream, large file) ──────────────────────────────────────────
print("Loading edges … ", end="", flush=True)
edges_df = pd.read_csv(DATA_DIR / "edges.csv",
                       dtype={"x_index": int, "y_index": int,
                              "relation": str, "display_relation": str})
print(f"{len(edges_df):,} edges")

# ── build graph ───────────────────────────────────────────────────────────────
print("Building graph … ", end="", flush=True)
G = nx.Graph()

# bulk-add nodes
node_attrs = {
    row.node_index: {"name": row.node_name, "ntype": row.node_type}
    for row in nodes_df.itertuples(index=False)
}
G.add_nodes_from(node_attrs.items())

# bulk-add edges — zip arrays, no per-row dict
edge_iter = zip(
    edges_df["x_index"].tolist(),
    edges_df["y_index"].tolist(),
    edges_df["display_relation"].tolist(),
    edges_df["relation"].tolist(),
)
G.add_edges_from(
    (x, y, {"display_relation": dr, "relation": r})
    for x, y, dr, r in edge_iter
)

print(f"{G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges\n")

# ── colour palette ─────────────────────────────────────────────────────────
PALETTE = {
    "drug":                  "#4e79a7",
    "disease":               "#e15759",
    "gene/protein":          "#76b7b2",
    "biological_process":    "#59a14f",
    "molecular_function":    "#f28e2b",
    "cellular_component":    "#b07aa1",
    "pathway":               "#ff9da7",
    "anatomy":               "#9c755f",
    "exposure":              "#bab0ac",
    "phenotype":             "#edc948",
}

def node_color(ntype: str) -> str:
    ntype = (ntype or "").lower()
    for k, v in PALETTE.items():
        if k in ntype:
            return v
    return "#aaaaaa"

# ── subgraph builder ──────────────────────────────────────────────────────────
def make_subgraph(seed: str | None, ntype: str | None,
                  hops: int, limit: int) -> nx.Graph:
    if seed:
        seed_lower = seed.lower()
        matches = [n for n, d in G.nodes(data=True)
                   if seed_lower in d.get("name","").lower()]
        if not matches:
            print(f"  No node matching '{seed}'")
            return nx.Graph()
        center = matches[0]
        print(f"  Seed → '{G.nodes[center]['name']}' ({G.nodes[center]['ntype']})")
        sub_nodes = {center}
        frontier = {center}
        for _ in range(hops):
            nxt = set()
            for n in frontier:
                nxt.update(G.neighbors(n))
            sub_nodes.update(nxt)
            frontier = nxt
            if len(sub_nodes) > limit:
                break
        if len(sub_nodes) > limit:
            scored = sorted(sub_nodes, key=lambda n: G.degree(n), reverse=True)
            sub_nodes = set(scored[:limit])
            sub_nodes.add(center)
        return G.subgraph(sub_nodes).copy()

    elif ntype:
        ntype_lower = ntype.lower()
        seeds = [n for n, d in G.nodes(data=True)
                 if ntype_lower in d.get("ntype","").lower()][:60]
        if not seeds:
            return nx.Graph()
        nbrs = set(seeds)
        for n in seeds:
            nbrs.update(list(G.neighbors(n))[:8])
            if len(nbrs) > limit:
                break
        return G.subgraph(list(nbrs)[:limit]).copy()

    else:
        # hub ego-graph
        hub = max(G.nodes, key=lambda n: G.degree(n))
        print(f"  Hub → '{G.nodes[hub]['name']}' deg={G.degree(hub)}")
        sub_nodes = {hub}
        frontier = {hub}
        for _ in range(hops):
            nxt = set()
            for n in frontier:
                nxt.update(G.neighbors(n))
            sub_nodes.update(nxt)
            frontier = nxt
            if len(sub_nodes) > limit:
                break
        if len(sub_nodes) > limit:
            scored = sorted(sub_nodes, key=lambda n: G.degree(n), reverse=True)
            sub_nodes = set(scored[:limit])
            sub_nodes.add(hub)
        return G.subgraph(sub_nodes).copy()


def to_cytoscape(sg: nx.Graph) -> list[dict]:
    elements = []
    for n, d in sg.nodes(data=True):
        name = d.get("name", str(n))
        nt   = d.get("ntype", "unknown")
        elements.append({"data": {
            "id":     str(n),
            "label":  name,
            "ntype":  nt,
            "color":  node_color(nt),
            "degree": sg.degree(n),
        }})
    for u, v, d in sg.edges(data=True):
        elements.append({"data": {
            "source":   str(u),
            "target":   str(v),
            "relation": d.get("display_relation", d.get("relation","—")),
        }})
    return elements


# ── stylesheet ─────────────────────────────────────────────────────────────
STYLESHEET = [
    {"selector": "node", "style": {
        "label":              "data(label)",
        "background-color":   "data(color)",
        "width":  "mapData(degree, 1, 50, 14, 65)",
        "height": "mapData(degree, 1, 50, 14, 65)",
        "font-size":          "10px",
        "text-valign":        "bottom",
        "text-halign":        "center",
        "color":              "#222",
        "text-outline-color": "#fff",
        "text-outline-width": "1.5px",
        "border-width":       1,
        "border-color":       "#666",
    }},
    {"selector": "node:selected", "style": {
        "border-color": "#f90",
        "border-width":  3,
    }},
    {"selector": "edge", "style": {
        "width":       1,
        "line-color":  "#ccc",
        "curve-style": "bezier",
        "opacity":     0.65,
    }},
    {"selector": "edge:selected", "style": {
        "line-color": "#f60",
        "width":       2,
        "label":      "data(relation)",
        "font-size":  "9px",
        "color":      "#c00",
        "text-rotation": "autorotate",
    }},
]

# ── legend ─────────────────────────────────────────────────────────────────
def legend_item(ntype: str, color: str) -> html.Span:
    return html.Span([
        html.Span("●", style={"color": color, "fontSize": "18px",
                               "marginRight": "4px"}),
        ntype + "  ",
    ], style={"marginRight": "12px", "whiteSpace": "nowrap"})

LEGEND = html.Div(
    [legend_item(nt, col) for nt, col in PALETTE.items()],
    style={"display":"flex","flexWrap":"wrap","padding":"6px 16px",
           "background":"#fff","borderBottom":"1px solid #e0e0e0",
           "fontSize":"12px","alignItems":"center"},
)

# ── Dash app ───────────────────────────────────────────────────────────────
cyto.load_extra_layouts()
app = dash.Dash(__name__, title="PrimeKG Explorer")

NTYPES = sorted({d.get("ntype","") for _,d in G.nodes(data=True) if d.get("ntype","")})
RELATIONS = sorted(edges_df["display_relation"].unique())

app.layout = html.Div([

    # ── top bar ──
    html.Div([
        html.H2("PrimeKG Subgraph Explorer",
                style={"margin":"0 16px 0 0","fontSize":"18px"}),
        html.Label("Seed (name fragment):"),
        dcc.Input(id="seed-input", type="text",
                  placeholder="metformin · TP53 · Alzheimer · EGFR",
                  debounce=False,
                  style={"width":"220px","marginRight":"16px","padding":"4px"}),
        html.Label("Node type:"),
        dcc.Dropdown(id="ntype-drop",
                     options=[{"label":t,"value":t} for t in NTYPES],
                     placeholder="all types",
                     clearable=True,
                     style={"width":"200px","marginRight":"16px","display":"inline-block"}),
        html.Label("Hops:", style={"marginRight":"4px"}),
        html.Div(
            dcc.Slider(id="hops-slider", min=1, max=3, step=1, value=1,
                       marks={1:"1",2:"2",3:"3"},
                       tooltip={"placement":"bottom","always_visible":False}),
            style={"width":"120px","marginRight":"16px"}),
        html.Label("Max nodes:", style={"marginRight":"4px"}),
        html.Div(
            dcc.Slider(id="limit-slider", min=50, max=800, step=50, value=300,
                       marks={50:"50",200:"200",500:"500",800:"800"},
                       tooltip={"placement":"bottom","always_visible":False}),
            style={"width":"180px","marginRight":"16px"}),
        html.Label("Layout:", style={"marginRight":"4px"}),
        dcc.Dropdown(id="layout-drop",
                     options=[{"label":l,"value":l} for l in
                               ["cose","cola","spread","circle","grid","concentric"]],
                     value="cose", clearable=False,
                     style={"width":"120px","display":"inline-block","marginRight":"16px"}),
        html.Button("Draw", id="draw-btn", n_clicks=0,
                    style={"padding":"6px 20px","fontWeight":"bold",
                           "background":"#4e79a7","color":"#fff","border":"none",
                           "borderRadius":"4px","cursor":"pointer"}),
    ], style={"display":"flex","alignItems":"center","flexWrap":"wrap",
               "gap":"6px","padding":"10px 16px",
               "background":"#f5f5f5","borderBottom":"1px solid #ddd"}),

    LEGEND,

    # ── graph ──
    cyto.Cytoscape(
        id="kg-graph",
        layout={"name":"cose","idealEdgeLength":90,"animate":False,
                "nodeRepulsion":4500,"gravity":0.25},
        style={"width":"100%","height":"calc(100vh - 160px)"},
        elements=[],
        stylesheet=STYLESHEET,
        minZoom=0.04, maxZoom=5,
        responsive=True,
    ),

    # ── info bar ──
    html.Div(id="info-panel",
             children="Click a node or edge for details.",
             style={"padding":"8px 16px","background":"#fafafa",
                    "borderTop":"1px solid #ddd","fontSize":"13px",
                    "minHeight":"36px","fontFamily":"monospace"}),

], style={"fontFamily":"sans-serif","margin":"0","padding":"0"})


@callback(
    Output("kg-graph", "elements"),
    Output("kg-graph", "layout"),
    Input("draw-btn", "n_clicks"),
    Input("seed-input",   "n_submit"),   # enter key
    Input("hops-slider",  "value"),
    Input("limit-slider", "value"),
    Input("ntype-drop",   "value"),
    Input("layout-drop",  "value"),
    prevent_initial_call=False,
)
def update_graph(_clicks, _submit, hops, limit, ntype, layout_name):
    from dash import ctx
    seed_val = dash.callback_context.inputs.get("seed-input.value") if dash.callback_context.inputs else None
    # seed comes from the Input directly — pull from component state via pattern
    return (
        to_cytoscape(make_subgraph(None, ntype or None, hops or 1, limit or 300)),
        {"name": layout_name or "cose", "idealEdgeLength": 90, "animate": False,
         "nodeRepulsion": 4500, "gravity": 0.25},
    )


# separate callback driven by the seed input value
@callback(
    Output("kg-graph", "elements", allow_duplicate=True),
    Input("draw-btn", "n_clicks"),
    dash.dependencies.State("seed-input",  "value"),
    dash.dependencies.State("ntype-drop",  "value"),
    dash.dependencies.State("hops-slider", "value"),
    dash.dependencies.State("limit-slider","value"),
    dash.dependencies.State("layout-drop", "value"),
    prevent_initial_call=True,
)
def draw_on_button(_clicks, seed, ntype, hops, limit, _layout):
    sg = make_subgraph(seed or None, ntype or None, hops or 1, limit or 300)
    return to_cytoscape(sg)


@callback(
    Output("info-panel", "children"),
    Input("kg-graph", "tapNodeData"),
    Input("kg-graph", "tapEdgeData"),
)
def show_info(node_data, edge_data):
    if node_data:
        name   = node_data.get("label","?")
        ntype  = node_data.get("ntype","?")
        subdeg = node_data.get("degree","?")
        nid    = node_data.get("id","")
        full_deg = G.degree(int(nid)) if nid.isdigit() and int(nid) in G else "?"
        return [html.B(name), f"  |  type: {ntype}  |  subgraph deg: {subdeg}  |  full KG deg: {full_deg}"]
    if edge_data:
        src = edge_data.get("source","?")
        tgt = edge_data.get("target","?")
        rel = edge_data.get("relation","?")
        sname = G.nodes[int(src)].get("name", src) if src.isdigit() else src
        tname = G.nodes[int(tgt)].get("name", tgt) if tgt.isdigit() else tgt
        return f"{sname}  →[{rel}]→  {tname}"
    return "Click a node or edge for details."


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--seed",  default=None)
    p.add_argument("--ntype", default=None)
    p.add_argument("--hops",  type=int, default=1)
    p.add_argument("--limit", type=int, default=300)
    p.add_argument("--port",  type=int, default=8050)
    args = p.parse_args()

    print(f"\nOpen  http://127.0.0.1:{args.port}  in your browser\n")
    app.run(debug=False, port=args.port)
