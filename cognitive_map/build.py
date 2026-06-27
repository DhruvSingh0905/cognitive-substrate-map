"""Phase 1 orchestrator: seed -> expand -> brain-scope -> attributes -> export."""
from pathlib import Path
import pandas as pd
from cognitive_map.db import Graph
from cognitive_map.seeds import intervention_seeds, classify, DISEASE_READOUT
from cognitive_map.brain_enrichment import brain_enrichment
from cognitive_map.node_attributes import node_attributes
from cognitive_map.expand import expand

OUT = Path(__file__).parent / "output"


def build_substrate(graph: Graph) -> pd.DataFrame:
    seeds = intervention_seeds() | set(DISEASE_READOUT)
    expanded = expand(graph, list(seeds))
    nodes = sorted(seeds | expanded)

    enr = brain_enrichment(graph, nodes)
    attrs = node_attributes(graph, nodes)

    rows = []
    for g in nodes:
        a = attrs[g]
        rows.append({
            "gene": g,
            "klass": classify(g),
            "brain_enrichment": round(enr.get(g, 0.0), 3),
            "n_diseases": a["n_diseases"],
            "promiscuity": a["promiscuity"],
            "n_pathways": len(a["pathways"]),
            "modulating_drugs": ";".join(a["modulating_drugs"]),
            # Phase-2 human-rigor columns — created EMPTY, never fabricated (spec §3)
            "direction": pd.NA,
            "magnitude": pd.NA,
            "tradeoff": pd.NA,
            "evidence_grade": pd.NA,
        })
    return pd.DataFrame(rows).sort_values("brain_enrichment", ascending=False)


def edges_among(graph: Graph, nodes: list[str]) -> pd.DataFrame:
    rows = graph.query(
        "MATCH (a:gene_protein)-[:protein_protein]-(b:gene_protein) "
        "WHERE a.node_name IN $nodes AND b.node_name IN $nodes AND a.node_name < b.node_name "
        "RETURN a.node_name AS source, b.node_name AS target",
        nodes=list(nodes))
    df = pd.DataFrame(rows, columns=["source", "target"])
    df["sign"] = pd.NA
    df["magnitude"] = pd.NA
    df["magnitude_status"] = "unknown"
    return df


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = Graph()
    try:
        nodes_df = build_substrate(g)
        edges_df = edges_among(g, nodes_df["gene"].tolist())
    finally:
        g.close()
    nodes_df.to_csv(OUT / "nodes.csv", index=False)
    edges_df.to_csv(OUT / "edges.csv", index=False)
    print(f"wrote {len(nodes_df)} nodes, {len(edges_df)} edges to {OUT}")


if __name__ == "__main__":
    main()
