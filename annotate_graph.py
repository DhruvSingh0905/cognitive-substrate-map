"""
Annotate PrimeKG drug_effect edges with RECOVERED, VERIFIABLE provenance only.

Design principle: "rather nothing than wrong."
  - We only write facts we can verify, named for what they are.
  - We NEVER assert absence. A missing SIDER match -> property left null (unknown),
    never on_label=false (which would be wrong for HPO-vs-MedDRA naming misses).
  - We do NOT write any blended "trust" scalar (it would conflate a degree
    heuristic with clinical evidence and read as a probability the edge is real).

Writes:
  (node)  effect_phenotype.n_drugs        : # drugs sharing this side effect (pure graph fact)
  (edge)  drug_effect.sider_label_freq    : max precise label frequency %  (only on exact
                                            drug-name + SE-name match in SIDER; else null)
  (edge)  drug_effect.sider_freq_tier     : 'rare'..'very common' qualitative tier (else null)

Match precision: requires BOTH the drug name AND the side-effect name to match SIDER
exactly (case-insensitive). High precision / conservative recall by design.

Run:      python annotate_graph.py
Rollback: python annotate_graph.py --undo
"""

import sys, gzip
from pathlib import Path
import pandas as pd
from neo4j import GraphDatabase

HERE = Path(__file__).parent
SIDER = HERE / "data" / "sider"
URI, AUTH = "bolt://localhost:7687", ("neo4j", "primekg123")
UNDO = "--undo" in sys.argv

TIER = {"postmarketing":0,"rare":1,"infrequent":2,"frequent":3,"common":4,"very common":5}
TIER_INV = {v:k for k,v in TIER.items()}

drv = GraphDatabase.driver(URI, auth=AUTH)

# ── rollback ─────────────────────────────────────────────────────────────────
if UNDO:
    with drv.session() as s:
        s.run("MATCH (e:effect_phenotype) REMOVE e.n_drugs")
        s.run("MATCH ()-[r:drug_effect]->() REMOVE r.sider_label_freq, r.sider_freq_tier")
    print("Rolled back all annotations (n_drugs, sider_label_freq, sider_freq_tier).")
    drv.close(); sys.exit(0)

# ── 0. index for fast edge matching by effect name ───────────────────────────
with drv.session() as s:
    s.run("CREATE INDEX effect_name IF NOT EXISTS FOR (e:effect_phenotype) ON (e.node_name)")
    s.run("CALL db.awaitIndexes(120)")

# ── 1. node fact: promiscuity degree (always correct) ────────────────────────
print("Writing effect_phenotype.n_drugs (promiscuity) …", flush=True)
with drv.session() as s:
    s.run("""
        MATCH (e:effect_phenotype)
        SET e.n_drugs = COUNT { (e)-[:drug_effect]-(:drug) }
    """)

# ── 2. build SIDER (drug, side_effect) -> {precise freq, tier} ────────────────
print("Parsing SIDER label frequencies …", flush=True)
names = pd.read_csv(SIDER / "drug_names.tsv", sep="\t",
                    names=["cid","name"], dtype=str)
cid2name = dict(zip(names["cid"], names["name"].str.lower()))

rows = []
with gzip.open(SIDER / "meddra_freq.tsv.gz", "rt") as fh:
    for line in fh:
        p = line.rstrip("\n").split("\t")
        if len(p) < 10:
            continue
        drug = cid2name.get(p[0])
        if not drug:
            continue
        lo = pd.to_numeric(p[5], errors="coerce")
        hi = pd.to_numeric(p[6], errors="coerce")
        precise = hi if (pd.notna(lo) and pd.notna(hi) and lo == hi and hi > 0) else None
        tier = TIER.get(p[4].strip().lower())
        rows.append((drug, p[9].lower(), precise, tier))

sdf = pd.DataFrame(rows, columns=["drug","se","precise","tier"])
agg = sdf.groupby(["drug","se"]).agg(
    freq=("precise","max"),            # highest precise point estimate, if any
    tier=("tier","max"),               # highest-severity qualitative tier, if any
).reset_index()
agg["freq_pct"] = (100*agg["freq"]).round(2)
agg["tier_name"] = agg["tier"].map(lambda v: TIER_INV[int(v)] if pd.notna(v) else None)
print(f"  SIDER: {len(agg):,} (drug, side-effect) pairs with label data")

# ── 3. pull all drug_effect edges (drug + effect names) from the graph ───────
print("Pulling drug_effect edges from PrimeKG …", flush=True)
with drv.session() as s:
    edges = s.run("""
        MATCH (d:drug)-[:drug_effect]-(e:effect_phenotype)
        RETURN d.node_name AS drug, e.node_name AS se
    """).data()
edf = pd.DataFrame(edges)
edf["dk"] = edf["drug"].str.lower(); edf["sk"] = edf["se"].str.lower()
total_edges = len(edf)

# ── 4. EXACT double-name join (drug AND side-effect) — high precision ─────────
m = edf.merge(agg, left_on=["dk","sk"], right_on=["drug","se"],
              how="inner", suffixes=("","_s"))
m = m[m["freq_pct"].notna() | m["tier_name"].notna()]
print(f"  matched {len(m):,} / {total_edges:,} drug_effect edges "
      f"({100*len(m)//max(total_edges,1)}%) with high-precision name match")

# ── 5. write recovered facts (null elsewhere — never asserts absence) ────────
def _na(v):
    """NaN/None -> real Python None (so the driver sends null, not IEEE NaN)."""
    if v is None:
        return None
    try:
        if isinstance(v, float) and pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return v

payload = []
for r in m.itertuples(index=False):
    freq = _na(r.freq_pct)
    freq = None if freq is None else float(freq)
    tier = _na(r.tier_name)
    tier = None if tier is None else str(tier)
    if freq is None and tier is None:
        continue                       # nothing verifiable -> leave edge untouched
    payload.append({"drug": r.drug, "se": r.se, "freq": freq, "tier": tier})

print("Writing sider_label_freq / sider_freq_tier onto matched edges …", flush=True)
with drv.session() as s:
    for i in range(0, len(payload), 5000):
        s.run("""
            UNWIND $rows AS row
            MATCH (d:drug {node_name:row.drug})-[r:drug_effect]-(e:effect_phenotype {node_name:row.se})
            SET r.sider_label_freq = row.freq,
                r.sider_freq_tier  = row.tier
        """, rows=payload[i:i+5000])

# ── 6. verify the write landed correctly (read back FROM the graph) ──────────
print("\n=== verification (read back from graph) ===")
with drv.session() as s:
    chk = s.run("""
        MATCH (d:drug {node_name:'Telmisartan'})-[r:drug_effect]-(e:effect_phenotype)
        WHERE e.node_name IN ['Headache','Nausea','Malnutrition','Dry skin']
        RETURN e.node_name AS side_effect, e.n_drugs AS n_drugs,
               r.sider_label_freq AS label_freq, r.sider_freq_tier AS tier
        ORDER BY side_effect
    """).data()
    cov = s.run("""
        MATCH ()-[r:drug_effect]->()
        RETURN count(r) AS total,
               count(r.sider_label_freq) AS with_precise_freq,
               count(r.sider_freq_tier)  AS with_tier
    """).single().data()
for row in chk:
    print(f"  {row['side_effect']:<14} n_drugs={row['n_drugs']:<5} "
          f"label_freq={row['label_freq']}  tier={row['tier']}")
print(f"\ncoverage: {cov['with_tier']:,} edges got a SIDER tier, "
      f"{cov['with_precise_freq']:,} got a precise freq, of {cov['total']:,} drug_effect edges")
print("(unmatched edges left null = 'unknown', never asserted false)")
print("\nrollback anytime:  python annotate_graph.py --undo")
drv.close()
