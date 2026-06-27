"""Graph-fillable node columns (spec §3.A)."""
from cognitive_map.db import Graph


def node_attributes(graph: Graph, genes: list[str]) -> dict[str, dict]:
    genes = list(genes)
    out = {g: {"pathways": [], "n_diseases": 0, "promiscuity": 0,
               "modulating_drugs": []} for g in genes}

    for r in graph.query(
        "MATCH (g:gene_protein)-[:pathway_protein]-(p:pathway) "
        "WHERE g.node_name IN $genes "
        "RETURN g.node_name AS gene, collect(DISTINCT p.node_name) AS pathways",
        genes=genes):
        out[r["gene"]]["pathways"] = r["pathways"]

    for r in graph.query(
        "MATCH (g:gene_protein)-[:disease_protein]-(d:disease) "
        "WHERE g.node_name IN $genes "
        "RETURN g.node_name AS gene, count(DISTINCT d) AS n",
        genes=genes):
        out[r["gene"]]["n_diseases"] = r["n"]

    for r in graph.query(
        "MATCH (g:gene_protein)-[:drug_protein]-(dr:drug) "
        "WHERE g.node_name IN $genes "
        "RETURN g.node_name AS gene, count(DISTINCT dr) AS n",
        genes=genes):
        out[r["gene"]]["promiscuity"] = r["n"]

    for r in graph.query(
        "MATCH (g:gene_protein)-[rel:drug_protein {display_relation:'target'}]-(dr:drug) "
        "WHERE g.node_name IN $genes "
        "RETURN g.node_name AS gene, collect(DISTINCT dr.node_name) AS drugs",
        genes=genes):
        out[r["gene"]]["modulating_drugs"] = r["drugs"]

    return out
