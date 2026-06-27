"""
Rephetio rebuild — STEP 2: define the metapaths (drug -> ... -> disease templates).

These are Rephetio's top-ranked metapaths, mapped to PrimeKG relations. Each is a
fixed sequence of edge types. Right now we just COUNT paths (PC = path count) to
confirm they fire — Step 3 will degree-weight them into DWPC.
"""
from neo4j import GraphDatabase

URI, AUTH = "bolt://localhost:7687", ("neo4j", "primekg123")
DISEASE = "type 2 diabetes mellitus"
SAMPLE  = "Pioglitazone"          # a known positive — should score on the mechanistic paths

TARGET = "{display_relation:'target'}"

# name -> (human description, cypher path pattern from $drug to disease)
METAPATHS = {
    "C-targets-G-assoc-D": (
        "drug targets a T2D-associated gene  (Rephetio CbGaD, #2)",
        f"(d)-[:drug_protein {TARGET}]-(g:gene_protein)-[:disease_protein]-(dis)"),
    "C-shares-target-with-Tx": (
        "drug shares a target with a known T2D drug  (Rephetio CbGbCtD, #1)",
        f"(d)-[:drug_protein {TARGET}]-(g:gene_protein)-[:drug_protein {TARGET}]-(d2:drug)-[:indication]-(dis)"),
    "C-target-PPI-G-assoc-D": (
        "drug's target interacts (PPI) with a T2D-associated gene  (CbGiGaD)",
        f"(d)-[:drug_protein {TARGET}]-(g:gene_protein)-[:protein_protein]-(g2:gene_protein)-[:disease_protein]-(dis)"),
}

drv = GraphDatabase.driver(URI, auth=AUTH)
print(f"Path counts (PC) for {SAMPLE} -> {DISEASE}:\n")
with drv.session() as s:
    for name, (desc, pattern) in METAPATHS.items():
        q = (f"MATCH p={pattern} "
             f"WHERE d.node_name=$drug AND dis.node_name=$dis "
             f"RETURN count(p) AS pc")
        pc = s.run(q, drug=SAMPLE, dis=DISEASE).single()["pc"]
        print(f"  {name:24} PC = {pc:<4}  ({desc})")
drv.close()

print("\nPC just counts paths — but a path through a 800-drug hub gene counts the")
print("same as one through a specific gene. Step 3 (DWPC) fixes that.")
