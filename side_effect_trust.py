"""
Side-effect trust scoring for a PrimeKG drug.

PrimeKG stores every drug->side_effect edge with equal weight and no provenance.
This script reconstructs a trust signal from three angles:

  1. PROMISCUITY  (graph-native, Hetionet DWPC-style degree damping):
       weight = n_drugs_with_SE ** (-w),  w=0.4  (Himmelstein et al. 2017)
       A side effect shared by ~1000 drugs (nausea) carries almost no
       drug-specific information; one shared by ~30 does.

  2. SIDER LABEL FREQUENCY  (recovered provenance PrimeKG discarded):
       SIDER's meddra_freq table only contains side effects with a frequency
       reported on the official drug label = clinically established. A PrimeKG
       edge MISSING from this table likely came from OFFSIDES/FAERS statistical
       mining = the confounded source. So label-presence is itself a trust flag.

  3. MECHANISTIC CORROBORATION  (graph-native):
       count of proteins the drug targets that are ALSO linked to the side-effect
       phenotype (drug_protein x phenotype_protein). A corroborating mechanism
       path raises trust.

Usage:  python side_effect_trust.py "Telmisartan"
"""

import sys, gzip
from pathlib import Path
import pandas as pd
from neo4j import GraphDatabase

DRUG = sys.argv[1] if len(sys.argv) > 1 else "Telmisartan"
W = 0.4  # Hetionet DWPC damping exponent

HERE = Path(__file__).parent
SIDER = HERE / "data" / "sider"
URI, AUTH = "bolt://localhost:7687", ("neo4j", "primekg123")

# ── 1+3. graph: promiscuity + mechanistic corroboration ──────────────────────
drv = GraphDatabase.driver(URI, auth=AUTH)
with drv.session() as s:
    promis = s.run(
        """
        MATCH (d:drug {node_name:$drug})-[:drug_effect]-(e:effect_phenotype)
        RETURN e.node_name AS side_effect,
               COUNT { (e)-[:drug_effect]-(:drug) } AS n_drugs
        """, drug=DRUG).data()
    mech = s.run(
        """
        MATCH (d:drug {node_name:$drug})-[:drug_effect]-(e:effect_phenotype)
        OPTIONAL MATCH (d)-[:drug_protein]-(p:gene_protein)-[:phenotype_protein]-(e)
        RETURN e.node_name AS side_effect, count(DISTINCT p) AS shared_proteins
        """, drug=DRUG).data()
drv.close()

if not promis:
    sys.exit(f"No side effects found for drug '{DRUG}' in PrimeKG.")

df = pd.DataFrame(promis).merge(pd.DataFrame(mech), on="side_effect", how="left")

# ── 2. SIDER: recover label-reported frequencies for this drug ───────────────
names = pd.read_csv(SIDER / "drug_names.tsv", sep="\t",
                    names=["cid", "name"], dtype=str)
hit = names[names["name"].str.lower() == DRUG.lower()]
if hit.empty:  # fall back to substring
    hit = names[names["name"].str.lower().str.contains(DRUG.lower())]

# qualitative tiers, ranked by severity (for entries with no precise number)
TIER = {"postmarketing":0, "rare":1, "infrequent":2, "frequent":3,
        "common":4, "very common":5}
TIER_INV = {v: k for k, v in TIER.items()}

sider_freq, sider_tier, on_label_keys = {}, {}, set()
sider_status = "drug not found in SIDER"
if not hit.empty:
    cids = set(hit["cid"])
    cols = ["cid_flat","cid_stereo","umls_label","placebo",
            "freq_txt","freq_lo","freq_hi","mtype","umls_meddra","se_name"]
    rows = []
    with gzip.open(SIDER / "meddra_freq.tsv.gz", "rt") as fh:
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 10 and p[0] in cids:
                rows.append(p)
    if rows:
        fdf = pd.DataFrame(rows, columns=cols)
        fdf["freq_lo"] = pd.to_numeric(fdf["freq_lo"], errors="coerce")
        fdf["freq_hi"] = pd.to_numeric(fdf["freq_hi"], errors="coerce")
        fdf["key"] = fdf["se_name"].str.lower()
        on_label_keys = set(fdf["key"])
        # PRECISE point estimate only: lower==upper bound and > 0
        precise = fdf[(fdf["freq_lo"] == fdf["freq_hi"]) & (fdf["freq_hi"] > 0)]
        sider_freq = (100 * precise.groupby("key")["freq_hi"].max()).round(2).to_dict()
        # otherwise keep the qualitative tier (highest severity reported)
        fdf["tier"] = fdf["freq_txt"].str.strip().str.lower().map(TIER)
        tbest = fdf.dropna(subset=["tier"]).groupby("key")["tier"].max()
        sider_tier = {k: TIER_INV[int(v)] for k, v in tbest.items()}
        sider_status = f"{len(on_label_keys)} on-label side effects"
    else:
        sider_status = "drug in SIDER but no label-frequency rows"

df["label_freq_pct"] = df["side_effect"].str.lower().map(sider_freq)   # precise only
df["label_tier"] = df["side_effect"].str.lower().map(sider_tier)       # rare..very common
df["on_label"] = df["side_effect"].str.lower().isin(on_label_keys)

# ── scoring ──────────────────────────────────────────────────────────────────
df["dwpc_weight"] = df["n_drugs"] ** (-W)
df["promiscuity_trust"] = df["dwpc_weight"] / df["dwpc_weight"].max()   # 0..1
# composite: promiscuity prior, boosted by on-label provenance + mechanism
df["trust"] = (
    df["promiscuity_trust"]
    * (1.0 + 0.5 * df["on_label"].astype(int))
    * (1.0 + 0.25 * df["shared_proteins"].clip(upper=4))
)
df["trust"] = (df["trust"] / df["trust"].max()).round(3)
df = df.sort_values("trust", ascending=False).reset_index(drop=True)

# ── report ───────────────────────────────────────────────────────────────────
pd.set_option("display.width", 140)
pd.set_option("display.max_colwidth", 42)

def show(d):
    return d[["side_effect","n_drugs","promiscuity_trust","on_label",
              "label_tier","label_freq_pct","shared_proteins","trust"]] \
        .rename(columns={"n_drugs":"#drugs","promiscuity_trust":"promisc",
                         "label_freq_pct":"freq%","label_tier":"tier",
                         "shared_proteins":"mech"}).round(3)

n = len(df)
on_label_n = int(df["on_label"].sum())
print(f"\n=== Side-effect trust for {DRUG} ===")
print(f"PrimeKG side effects: {n}   |   SIDER: {sider_status}   "
      f"|   on-label matched: {on_label_n}/{n} ({100*on_label_n//max(n,1)}%)")

print(f"\n── MOST trusted (specific / on-label / mechanism-backed) ──")
print(show(df.head(12)).to_string(index=False))
print(f"\n── LEAST trusted (promiscuous, off-label-only) ──")
print(show(df.tail(12)).to_string(index=False))

spot = df[df["side_effect"].str.lower().isin(["malnutrition","dry skin","nausea","headache"])]
if not spot.empty:
    print(f"\n── spotlight ──")
    print(show(spot).to_string(index=False))

print(f"\nReading it: promisc≈1 → drug-specific; #drugs high → generic/confounder-prone.")
print(f"on_label=True → clinically established (SIDER label); False → OFFSIDES/FAERS-mined only.")
