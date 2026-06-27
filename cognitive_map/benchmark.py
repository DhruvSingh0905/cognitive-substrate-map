"""Benchmark our substrate against external resources (Phase 1b).

A. sign completeness  — what the grey edges actually are (conflicting vs unsigned)
B. source confidence  — how many regulatory edges are SIGNOR/curated-backed
C. missing regulators — genes that regulate >=3 of our core but we didn't include (OmniPath)
D. missing cognition genes — learning/memory GO genes we didn't seed (PrimeKG)
"""
import io
import requests
import pandas as pd
from cognitive_map.db import Graph
from cognitive_map.seeds import intervention_seeds

API = "https://omnipathdb.org/interactions"
OUT = __import__("pathlib").Path(__file__).parent / "output"


def _fetch(partners, source_target):
    params = {"partners": ",".join(sorted(set(partners))), "source_target": source_target,
              "genesymbols": "1", "datasets": "omnipath,collectri,dorothea",
              "dorothea_levels": "A,B,C", "fields": "sources"}
    r = requests.get(API, params=params, timeout=180)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text), sep="\t")


def _truthy(s):
    return s.astype(str).str.strip().str.lower().isin(("true", "1"))


def run():
    nodes = pd.read_csv(OUT / "nodes.csv")
    nodeset = set(nodes["gene"])
    inter = sorted(intervention_seeds() & nodeset)
    report = []

    internal = _fetch(nodes["gene"].tolist(), "AND")
    stim = _truthy(internal.get("consensus_stimulation", internal["is_stimulation"]))
    inhib = _truthy(internal.get("consensus_inhibition", internal["is_inhibition"]))
    sign = {"activation": int((stim & ~inhib).sum()), "inhibition": int((inhib & ~stim).sum()),
            "conflicting": int((stim & inhib).sum()), "unsigned": int((~stim & ~inhib).sum())}
    report.append(("A. sign completeness (grey = conflicting + unsigned)", sign))

    src = internal["sources"].fillna("")
    conf = {db: int(src.str.contains(db).sum())
            for db in ["SIGNOR", "CollecTRI", "DoRothEA", "TRRUST", "Reactome", "SPIKE"]}
    report.append(("B. source confidence (edges citing each resource)", conf))

    touch = _fetch(inter, "OR")
    miss = touch[(~touch["source_genesymbol"].isin(nodeset))
                 & (touch["target_genesymbol"].isin(set(inter)))]
    regulators = (miss.groupby("source_genesymbol")["target_genesymbol"].nunique()
                  .sort_values(ascending=False))
    regulators = regulators[regulators >= 3]
    report.append(("C. missing upstream regulators (>=3 core targets, not in substrate)",
                   regulators.head(25).to_dict()))

    g = Graph()
    cog = {r["gene"] for r in g.query(
        "MATCH (b:biological_process)-[:bioprocess_protein]-(gp:gene_protein) "
        "WHERE b.node_name =~ '(?i).*(learning|memory|cognition|long-term potentiation|synaptic plasticity).*' "
        "RETURN DISTINCT gp.node_name AS gene")}
    g.close()
    missing_cog = sorted(cog - nodeset)
    report.append(("D. cognition-GO genes NOT in substrate (PrimeKG)",
                   {"count": len(missing_cog), "examples": missing_cog[:30]}))

    return report


if __name__ == "__main__":
    for title, data in run():
        print(f"\n=== {title} ===")
        print(data)
