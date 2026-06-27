"""
Rephetio rebuild — STEP 1: define the prediction task.

We're predicting drug -[indication]-> <disease>.
  positives  = drugs ALREADY indicated for the disease (the model learns their shape)
  candidates = every drug that *could* be scored (we'll rank the non-positives)

A drug can only be scored if it can reach the disease through the graph, so the
"scorable universe" = drugs with at least one protein target (every useful
metapath starts with drug -[drug_protein]-> gene).
"""
from neo4j import GraphDatabase

URI, AUTH = "bolt://localhost:7687", ("neo4j", "primekg123")
DISEASE = "type 2 diabetes mellitus"

drv = GraphDatabase.driver(URI, auth=AUTH)
with drv.session() as s:
    # positives: drugs with a known indication edge to the disease
    positives = {r["d"] for r in s.run(
        "MATCH (d:drug)-[:indication]-(:disease {node_name:$dis}) RETURN d.node_name AS d",
        dis=DISEASE)}

    # scorable universe: drugs that have ≥1 protein target (so a metapath can start)
    universe = {r["d"] for r in s.run(
        "MATCH (d:drug)-[r:drug_protein]-(:gene_protein) WHERE r.display_relation='target' "
        "RETURN DISTINCT d.node_name AS d")}
drv.close()

# a few positives may have no target edge themselves — keep them as labels anyway
scorable = universe | positives
candidates = scorable - positives          # the unknowns we ultimately rank

print(f"Disease:                     {DISEASE}")
print(f"Known treatments (positives): {len(positives)}")
print("  examples:", sorted(positives)[:12])
print(f"Scorable universe:            {len(scorable)} drugs")
print(f"Unlabeled candidates to rank: {len(candidates)}")
