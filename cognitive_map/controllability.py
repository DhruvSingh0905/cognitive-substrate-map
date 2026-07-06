"""Structural controllability / reachability of the substrate (Phase 2a).

Pure graph structure — no WE-built vectors. Answers "what can we even steer this to"
BEFORE we commit to a target state.

  1. components   — islands / orphans no intervention can reach
  2. reachability — druggable set -> which nodes are controllable at all
  3. driver nodes — Liu-Barabasi max-matching min driver set, and are drivers druggable
"""
import networkx as nx
import pandas as pd

OUT = __import__("pathlib").Path(__file__).parent / "output"


def build_graph():
    nodes = pd.read_csv(OUT / "nodes.csv")
    reg = pd.read_csv(OUT / "edges_regulatory.csv")
    G = nx.DiGraph()
    G.add_nodes_from(nodes["gene"].astype(str))
    G.add_edges_from(reg[["source", "target"]].astype(str).itertuples(index=False, name=None))
    # druggable = has a target-role drug, OR is an input-layer receptor
    md = nodes["modulating_drugs"].fillna("").astype(str)
    druggable = set(nodes.loc[(md.str.len() > 0) | (nodes["klass"] == "input"), "gene"].astype(str))
    return G, nodes, druggable


def max_matching_drivers(G):
    """Liu-Barabasi: min driver nodes = N - |max matching| on the bipartite out/in graph."""
    B = nx.Graph()
    B.add_nodes_from((("o", n) for n in G.nodes), bipartite=0)
    B.add_nodes_from((("i", n) for n in G.nodes), bipartite=1)
    B.add_edges_from((("o", u), ("i", v)) for u, v in G.edges())
    top = [("o", n) for n in G.nodes]
    matching = nx.bipartite.maximum_matching(B, top_nodes=top)
    matched_targets = {node[1] for node in matching if node[0] == "i"}
    drivers = [n for n in G.nodes if n not in matched_targets]   # unmatched in-copy => driver
    return drivers


def analyze():
    G, nodes, druggable = build_graph()
    alln = set(G.nodes)

    # reachability from druggable set
    reach = set(druggable)
    for d in druggable:
        reach |= nx.descendants(G, d)
    orphans = alln - reach

    # components
    wcc = sorted((len(c) for c in nx.weakly_connected_components(G)), reverse=True)
    scc = sorted((len(c) for c in nx.strongly_connected_components(G) if len(c) > 1), reverse=True)
    isolates = list(nx.isolates(G))

    # driver nodes
    drivers = max_matching_drivers(G)
    drivers_druggable = [d for d in drivers if d in druggable]

    return {
        "N": len(alln),
        "edges": G.number_of_edges(),
        "druggable": len(druggable),
        "reachable_from_druggable": len(reach),
        "orphans": sorted(orphans),
        "weak_components": wcc,
        "strong_components_gt1": scc,
        "isolates": isolates,
        "N_driver": len(drivers),
        "drivers_druggable": len(drivers_druggable),
        "drivers_sample": sorted(drivers)[:20],
    }


if __name__ == "__main__":
    r = analyze()
    print(f"nodes={r['N']}  edges={r['edges']}  druggable={r['druggable']}")
    print(f"reachable from druggable set: {r['reachable_from_druggable']}/{r['N']}  "
          f"| orphans (unreachable): {len(r['orphans'])}")
    if r["orphans"]:
        print("  orphans:", r["orphans"])
    print(f"weakly-connected components (sizes): {r['weak_components'][:8]}  isolates={len(r['isolates'])}")
    print(f"strongly-connected cores (>1): {r['strong_components_gt1'][:8]}")
    print(f"min driver nodes N_D (Liu-Barabasi) = {r['N_driver']}  "
          f"| of which druggable = {r['drivers_druggable']}")
    print(f"  full controllability needs {r['N_driver']} independent inputs; "
          f"we can drug {r['druggable']} nodes.")
