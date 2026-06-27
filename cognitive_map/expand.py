"""One-hop promiscuity-filtered expansion (spec §4 Phase 1 step 2)."""
from cognitive_map.db import Graph


def expand(graph: Graph, seeds: list[str], cutoff: int = 100) -> dict[str, int]:
    """1-hop PPI neighbors of seeds -> {neighbor: # distinct seeds it links to}.

    Drops promiscuous drug-hubs (drug-degree > cutoff). The seed-link count lets
    the caller keep only neighbors wired to >=2 seeds (genuinely in the core, not
    a random hub partner).
    """
    seeds = list(seeds)
    rows = graph.query(
        "MATCH (g:gene_protein)-[:protein_protein]-(n:gene_protein) "
        "WHERE g.node_name IN $seeds "
        "RETURN n.node_name AS gene, count(DISTINCT g) AS seed_links",
        seeds=seeds)
    seedset = set(seeds)
    cand = {r["gene"]: r["seed_links"] for r in rows if r["gene"] not in seedset}
    if not cand:
        return {}

    deg = {r["gene"]: r["n"] for r in graph.query(
        "MATCH (g:gene_protein)-[:drug_protein]-(:drug) "
        "WHERE g.node_name IN $genes "
        "RETURN g.node_name AS gene, count(*) AS n",
        genes=list(cand))}

    return {g: c for g, c in cand.items() if deg.get(g, 0) <= cutoff}
