"""
Convert PrimeKG nodes.csv + edges.csv into the header format that
`neo4j-admin database import` expects.

Outputs → data/primekg/neo4j_import/
    nodes_neo4j.csv   header: node_index:ID,node_id,:LABEL,node_name,node_source
    edges_neo4j.csv   header: :START_ID,:END_ID,:TYPE,display_relation

Notes:
  - Neo4j LABELs cannot contain '/', so 'gene/protein' -> 'gene_protein'
    and 'effect/phenotype' -> 'effect_phenotype'.
  - PrimeKG ships every undirected edge twice (x->y and y->x). We dedup on the
    unordered (lo, hi, relation) triple to get the canonical 4.05M edges, which
    matches the NetworkX undirected edge count.
  - :TYPE (relationship type) is sanitized: spaces/'/'/'-' -> '_'.
"""

import re
from pathlib import Path
import pandas as pd

DATA = Path(__file__).parent / "data" / "primekg"
OUT  = DATA / "neo4j_import"
OUT.mkdir(parents=True, exist_ok=True)


def sanitize_label(s: str) -> str:
    return re.sub(r"[/\s-]+", "_", str(s).strip())


# ── nodes ──────────────────────────────────────────────────────────────────
print("Reading nodes …", flush=True)
nodes = pd.read_csv(DATA / "nodes.csv", sep="\t",
                    dtype={"node_index": int})
for c in ("node_id", "node_type", "node_name", "node_source"):
    if nodes[c].dtype == object:
        nodes[c] = nodes[c].astype(str).str.strip('"')

nodes["label"] = nodes["node_type"].map(sanitize_label)

nodes_out = nodes[["node_index", "node_id", "label", "node_name", "node_source"]].copy()
nodes_out.columns = ["node_index:ID", "node_id", ":LABEL", "node_name", "node_source"]
nodes_out.to_csv(OUT / "nodes_neo4j.csv", index=False)
print(f"  wrote {len(nodes_out):,} nodes")
print("  labels:", dict(nodes["label"].value_counts()))


# ── edges ──────────────────────────────────────────────────────────────────
print("Reading edges …", flush=True)
edges = pd.read_csv(DATA / "edges.csv",
                    dtype={"x_index": int, "y_index": int,
                           "relation": str, "display_relation": str})

before = len(edges)
lo = edges[["x_index", "y_index"]].min(axis=1)
hi = edges[["x_index", "y_index"]].max(axis=1)
edges = edges.assign(_lo=lo, _hi=hi)
edges = edges.drop_duplicates(subset=["_lo", "_hi", "relation"])
print(f"  deduped {before:,} -> {len(edges):,} undirected edges")

edges["rel_type"] = edges["relation"].map(sanitize_label)

edges_out = edges[["_lo", "_hi", "rel_type", "display_relation"]].copy()
edges_out.columns = [":START_ID", ":END_ID", ":TYPE", "display_relation"]
edges_out.to_csv(OUT / "edges_neo4j.csv", index=False)
print(f"  wrote {len(edges_out):,} edges")
print("  rel types:", sorted(edges['rel_type'].unique()))

print("\nDone →", OUT)
