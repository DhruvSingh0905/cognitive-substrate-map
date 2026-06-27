"""One-hop promiscuity-filtered expansion (spec §4 Phase 1 step 2)."""
from cognitive_map.db import Graph


def expand(graph: Graph, seeds: list[str], cutoff: int = 100) -> set[str]:
    seeds = list(seeds)
    rows = graph.query(
        "MATCH (g:gene_protein)-[:protein_protein]-(n:gene_protein) "
        "WHERE g.node_name IN $seeds "
        "RETURN DISTINCT n.node_name AS gene",
        seeds=seeds)
    neighbors = {r["gene"] for r in rows} - set(seeds)
    if not neighbors:
        return set()

    deg = {r["gene"]: r["n"] for r in graph.query(
        "MATCH (g:gene_protein)-[:drug_protein]-(:drug) "
        "WHERE g.node_name IN $genes "
        "RETURN g.node_name AS gene, count(*) AS n",
        genes=list(neighbors))}

    return {n for n in neighbors if deg.get(n, 0) <= cutoff}
