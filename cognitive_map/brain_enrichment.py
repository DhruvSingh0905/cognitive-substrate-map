"""Brain-specificity from PrimeKG tissue expression (spec §2)."""
import re
from collections import defaultdict
from cognitive_map.db import Graph

# Curated brain-term matcher. Developmental/zebrafish terms ("neural keel") still
# match via 'neural' — acceptable as a soft signal; refined in Phase 1b.
_BRAIN = re.compile(
    r"(?i)(brain|cerebr|cortex|cortical|hippocamp|cerebell|nervous|neuron|neural|"
    r"amygdala|striatum|thalam|hypothalam|substantia nigra|prefrontal|"
    r"forebrain|midbrain|hindbrain)"
)


def is_brain_anatomy(name: str) -> bool:
    return bool(_BRAIN.search(name or ""))


def brain_enrichment_detailed(graph: Graph, genes: list[str]) -> dict[str, dict]:
    """Per gene: {'enrichment': fraction brain tissues, 'support': total tissues}.

    `support` matters: a gene seen in 1 (brain) tissue scores 1.0 but is noise —
    callers should require support >= 5 before trusting the enrichment.
    """
    rows = graph.query(
        "MATCH (g:gene_protein)-[:anatomy_protein_present]-(a:anatomy) "
        "WHERE g.node_name IN $genes "
        "RETURN g.node_name AS gene, a.node_name AS tissue",
        genes=list(genes),
    )
    total: dict[str, int] = defaultdict(int)
    brain: dict[str, int] = defaultdict(int)
    for r in rows:
        total[r["gene"]] += 1
        if is_brain_anatomy(r["tissue"]):
            brain[r["gene"]] += 1
    return {g: {"enrichment": (brain[g] / total[g] if total[g] else 0.0),
                "support": total[g]} for g in genes}


def brain_enrichment(graph: Graph, genes: list[str]) -> dict[str, float]:
    return {g: d["enrichment"] for g, d in brain_enrichment_detailed(graph, genes).items()}
