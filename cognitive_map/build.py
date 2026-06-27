"""Phase 1 orchestrator: seed -> bounded expand -> brain-scope -> attributes -> regulatory -> export."""
from pathlib import Path
import pandas as pd
from cognitive_map.db import Graph
from cognitive_map.seeds import intervention_seeds, input_seeds, classify, DISEASE_READOUT
from cognitive_map.brain_enrichment import brain_enrichment_detailed
from cognitive_map.node_attributes import node_attributes
from cognitive_map.expand import expand
from cognitive_map.regulatory import fetch_regulatory

OUT = Path(__file__).parent / "output"

BRAIN_MIN = 0.15      # expansion neighbors must be at least this brain-enriched
SUPPORT_MIN = 5       # ...and seen in >=5 tissues (else the enrichment is noise)
SEED_LINKS_MIN = 2    # ...and wired to >=2 seeds (in the core, not a random partner)
EXPANSION_CAP = 200   # ...and keep only the top-N most-relevant (seed-links x brain)


def build_substrate(graph: Graph) -> pd.DataFrame:
    seeds = intervention_seeds() | input_seeds() | set(DISEASE_READOUT)

    # bounded expansion: >=2 seed links, brain-enriched, well-supported
    cand = expand(graph, list(seeds))
    multi = [g for g, n in cand.items() if n >= SEED_LINKS_MIN]
    cdet = brain_enrichment_detailed(graph, multi)
    kept = [g for g in multi
            if cdet[g]["enrichment"] >= BRAIN_MIN and cdet[g]["support"] >= SUPPORT_MIN]
    # rank by relevance (seed-links, then brain-enrichment) and cap
    kept.sort(key=lambda g: (cand[g], cdet[g]["enrichment"]), reverse=True)
    kept = set(kept[:EXPANSION_CAP])

    nodes = sorted(seeds | kept)
    det = brain_enrichment_detailed(graph, nodes)
    attrs = node_attributes(graph, nodes)

    rows = []
    for g in nodes:
        a = attrs[g]
        rows.append({
            "gene": g,
            "klass": classify(g),
            "brain_enrichment": round(det[g]["enrichment"], 3),
            "tissue_support": det[g]["support"],
            "n_diseases": a["n_diseases"],
            "promiscuity": a["promiscuity"],
            "n_pathways": len(a["pathways"]),
            "modulating_drugs": ";".join(a["modulating_drugs"]),
            # Phase-2 human-rigor columns — created EMPTY, never fabricated (spec §3)
            "direction": pd.NA, "magnitude": pd.NA,
            "tradeoff": pd.NA, "evidence_grade": pd.NA,
        })
    return pd.DataFrame(rows).sort_values("brain_enrichment", ascending=False)


def edges_ppi(graph: Graph, nodes: list[str]) -> pd.DataFrame:
    rows = graph.query(
        "MATCH (a:gene_protein)-[:protein_protein]-(b:gene_protein) "
        "WHERE a.node_name IN $nodes AND b.node_name IN $nodes AND a.node_name < b.node_name "
        "RETURN a.node_name AS source, b.node_name AS target",
        nodes=list(nodes))
    return pd.DataFrame(rows, columns=["source", "target"])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = Graph()
    try:
        nodes_df = build_substrate(g)
        genes = nodes_df["gene"].tolist()
        ppi_df = edges_ppi(g, genes)
    finally:
        g.close()
    reg_df = fetch_regulatory(genes)        # OmniPath directed+signed (the real wiring)

    nodes_df.to_csv(OUT / "nodes.csv", index=False)
    ppi_df.to_csv(OUT / "edges.csv", index=False)                 # PPI (reference)
    reg_df.to_csv(OUT / "edges_regulatory.csv", index=False)      # regulatory (primary)
    print(f"wrote {len(nodes_df)} nodes | {len(ppi_df)} ppi | {len(reg_df)} regulatory edges")
    print(nodes_df["klass"].value_counts().to_string())


if __name__ == "__main__":
    main()
