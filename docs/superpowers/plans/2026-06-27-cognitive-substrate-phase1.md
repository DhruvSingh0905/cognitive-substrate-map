# Cognitive Substrate Map — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the brain-scoped cognitive substrate subgraph — a node set with graph-derived attributes, brain-enrichment scores, classification (intervention/trap/readout), and raw unsigned edges — exported as a node table + edge list for the later research and simulation phases.

**Architecture:** A small Python package `cognitive_map/` that reads the running PrimeKG Neo4j instance, seeds canonical cognitive genes, expands one promiscuity-filtered hop, scores brain-enrichment from tissue expression, attaches graph-derived columns, and exports CSVs. Pure functions over a thin DB wrapper; each module one responsibility.

**Tech Stack:** Python 3.11 (`.venv`), `neo4j` driver, `pandas`. Source graph: PrimeKG in Neo4j (`bolt://localhost:7687`, `neo4j`/`primekg123`).

## Global Constraints

- Neo4j container MUST be running for any DB-touching test: `./neo4j.sh start`.
- Connection: `bolt://localhost:7687`, auth `("neo4j", "primekg123")` — copy verbatim.
- Brain-scoping is a **soft downweight**, never a hard exclude (spec §2). `brain_enrichment ∈ [0,1]` is an attribute on every node.
- Promiscuity hub cutoff: drop expansion neighbors with drug-degree **> 100** (the ALB/ABCB1/CYP-grade garbage hubs).
- No fabricated values anywhere; this phase writes only graph-derived facts. Direction/magnitude/tradeoff columns are created **empty** for Phase 2.
- Run all Python via `.venv/bin/python` and tests via `.venv/bin/pytest`.

---

### Task 1: DB wrapper

**Files:**
- Create: `cognitive_map/__init__.py` (empty)
- Create: `cognitive_map/db.py`
- Create: `cognitive_map/tests/__init__.py` (empty)
- Create: `cognitive_map/tests/test_db.py`
- Modify: `.gitignore` (add `cognitive_map/output/`)

**Interfaces:**
- Produces: `class Graph` with `query(cypher: str, **params) -> list[dict]` and `close() -> None`.

- [ ] **Step 1: Write the failing test**

```python
# cognitive_map/tests/test_db.py
from cognitive_map.db import Graph

def test_query_returns_node_count():
    g = Graph()
    try:
        rows = g.query("MATCH (n) RETURN count(n) AS n")
        assert rows[0]["n"] > 100_000      # PrimeKG has ~129k nodes
    finally:
        g.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest cognitive_map/tests/test_db.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cognitive_map.db'`

- [ ] **Step 3: Write minimal implementation**

```python
# cognitive_map/db.py
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "primekg123")

class Graph:
    def __init__(self, uri: str = URI, auth: tuple = AUTH):
        self._driver = GraphDatabase.driver(uri, auth=auth)

    def query(self, cypher: str, **params) -> list[dict]:
        with self._driver.session() as session:
            return [record.data() for record in session.run(cypher, **params)]

    def close(self) -> None:
        self._driver.close()
```

Also create empty `cognitive_map/__init__.py` and `cognitive_map/tests/__init__.py`, and append `cognitive_map/output/` to `.gitignore`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest cognitive_map/tests/test_db.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cognitive_map/__init__.py cognitive_map/db.py cognitive_map/tests/ .gitignore
git commit -m "feat(cogmap): Neo4j DB wrapper"
```

---

### Task 2: Seed definitions + cascade triage

**Files:**
- Create: `cognitive_map/seeds.py`
- Create: `cognitive_map/tests/test_seeds.py`

**Interfaces:**
- Produces: `intervention_seeds() -> set[str]`; `classify(gene: str) -> str` returning one of `"intervention" | "trap" | "readout" | "expanded"`; module constants `DEVELOPMENTAL_TRAP: list[str]`, `DISEASE_READOUT: list[str]`.

- [ ] **Step 1: Write the failing test**

```python
# cognitive_map/tests/test_seeds.py
from cognitive_map.seeds import intervention_seeds, classify

def test_canonical_genes_are_seeds():
    s = intervention_seeds()
    for gene in ["GRIN2B", "BDNF", "DRD2", "CREB1", "ARC", "PRKAA1"]:
        assert gene in s

def test_classification_precedence():
    assert classify("NOTCH1") == "trap"        # developmental
    assert classify("MECP2") == "readout"       # disease cascade
    assert classify("GRIN2B") == "intervention"
    assert classify("SOMETHING_ELSE") == "expanded"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest cognitive_map/tests/test_seeds.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# cognitive_map/seeds.py
"""Curated brain-cognition seed genes + cascade triage (spec §2, §4)."""

NEUROTRANSMITTER = {
    "cholinergic":   ["CHRNA7", "CHRNA4", "CHRNB2", "ACHE", "CHAT", "SLC18A3"],
    "glutamatergic": ["GRIN1", "GRIN2A", "GRIN2B", "GRIA1", "GRIA2", "GRM5", "GRM2"],
    "dopaminergic":  ["DRD1", "DRD2", "DRD3", "DRD4", "DRD5", "COMT", "TH", "SLC6A3", "DDC"],
    "serotonergic":  ["HTR1A", "HTR2A", "SLC6A4", "TPH2"],
    "gabaergic":     ["GABRA1", "GABRB2", "GAD1", "GAD2", "SLC6A1"],
}
PLASTICITY_CASCADES = {
    "camp_pka_creb":  ["ADCY1", "PRKACA", "CREB1", "CREBBP"],
    "immediate_early":["FOS", "JUN", "EGR1", "ARC", "NR4A1", "BDNF"],
    "rho_ras_gtpase": ["RHOA", "RAC1", "CDC42", "HRAS", "RASGRF1", "KALRN"],
    "core_plasticity":["NTRK2", "MTOR", "CAMK2A", "CAMK2B"],
}
NEUROINFLAMMATION = ["TREM2", "IL1B", "TNF", "NFKB1", "NLRP3", "CX3CR1"]
CLEARANCE         = ["AQP4", "SQSTM1", "BECN1"]
METABOLIC         = ["PRKAA1", "PRKAA2", "PRKAB1", "PRKAG1"]

# Out of intervention scope — load-bearing/oncogenic if perturbed in the adult brain.
DEVELOPMENTAL_TRAP = ["NOTCH1", "NOTCH2", "CTNNB1", "WNT3A", "SHH", "GLI1", "HES1", "DLL1"]
# Disease-cascade reference / readouts, not knobs.
DISEASE_READOUT    = ["APP", "PSEN1", "PSEN2", "MAPT", "MECP2", "APOE"]

def intervention_seeds() -> set[str]:
    genes: set[str] = set()
    for group in (NEUROTRANSMITTER, PLASTICITY_CASCADES):
        for names in group.values():
            genes.update(names)
    genes.update(NEUROINFLAMMATION, CLEARANCE, METABOLIC)
    return genes

def classify(gene: str) -> str:
    if gene in DEVELOPMENTAL_TRAP:
        return "trap"
    if gene in DISEASE_READOUT:
        return "readout"
    if gene in intervention_seeds():
        return "intervention"
    return "expanded"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest cognitive_map/tests/test_seeds.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cognitive_map/seeds.py cognitive_map/tests/test_seeds.py
git commit -m "feat(cogmap): seed genes + cascade triage"
```

---

### Task 3: Brain-enrichment scoring

**Files:**
- Create: `cognitive_map/brain_enrichment.py`
- Create: `cognitive_map/tests/test_brain_enrichment.py`

**Interfaces:**
- Consumes: `Graph` from Task 1.
- Produces: `is_brain_anatomy(name: str) -> bool`; `brain_enrichment(graph: Graph, genes: list[str]) -> dict[str, float]` (gene → fraction of expression tissues that are brain, 0.0 if no expression data).

- [ ] **Step 1: Write the failing test**

```python
# cognitive_map/tests/test_brain_enrichment.py
from cognitive_map.db import Graph
from cognitive_map.brain_enrichment import is_brain_anatomy, brain_enrichment

def test_anatomy_matcher():
    assert is_brain_anatomy("cerebral cortex")
    assert is_brain_anatomy("hippocampus")
    assert not is_brain_anatomy("liver")
    assert not is_brain_anatomy("kidney")

def test_enrichment_separates_brain_from_systemic():
    g = Graph()
    try:
        e = brain_enrichment(g, ["GRIN2B", "BDNF", "AGTR1", "INS"])
    finally:
        g.close()
    # validated 2026-06-27: GRIN2B ~0.52, BDNF ~0.34, AGTR1 ~0.05, INS 0
    assert e["GRIN2B"] > 0.40
    assert e["AGTR1"] < 0.15
    assert e["GRIN2B"] > e["BDNF"] > e["AGTR1"]
    assert e["INS"] == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest cognitive_map/tests/test_brain_enrichment.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# cognitive_map/brain_enrichment.py
"""Brain-specificity from PrimeKG tissue expression (spec §2)."""
import re
from collections import defaultdict
from cognitive_map.db import Graph

# Curated adult-brain term matcher (drops obvious non-brain; developmental/zebrafish
# terms like "neural keel" still match via 'neural' — acceptable as a soft signal).
_BRAIN = re.compile(
    r"(?i)(brain|cerebr|cortex|cortical|hippocamp|cerebell|nervous|neuron|neural|"
    r"amygdala|striatum|thalam|hypothalam|substantia nigra|prefrontal|"
    r"forebrain|midbrain|hindbrain)"
)

def is_brain_anatomy(name: str) -> bool:
    return bool(_BRAIN.search(name or ""))

def brain_enrichment(graph: Graph, genes: list[str]) -> dict[str, float]:
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
    return {g: (brain[g] / total[g] if total[g] else 0.0) for g in genes}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest cognitive_map/tests/test_brain_enrichment.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cognitive_map/brain_enrichment.py cognitive_map/tests/test_brain_enrichment.py
git commit -m "feat(cogmap): brain-enrichment scoring"
```

---

### Task 4: Graph-derived node attributes

**Files:**
- Create: `cognitive_map/node_attributes.py`
- Create: `cognitive_map/tests/test_node_attributes.py`

**Interfaces:**
- Consumes: `Graph` from Task 1.
- Produces: `node_attributes(graph: Graph, genes: list[str]) -> dict[str, dict]` where each value has keys `pathways: list[str]`, `n_diseases: int`, `promiscuity: int` (drug-degree), `modulating_drugs: list[str]` (target-role drugs).

- [ ] **Step 1: Write the failing test**

```python
# cognitive_map/tests/test_node_attributes.py
from cognitive_map.db import Graph
from cognitive_map.node_attributes import node_attributes

def test_attributes_for_bdnf():
    g = Graph()
    try:
        attrs = node_attributes(g, ["BDNF"])
    finally:
        g.close()
    a = attrs["BDNF"]
    assert a["n_diseases"] > 0
    assert isinstance(a["pathways"], list)
    assert a["promiscuity"] >= 0
    assert isinstance(a["modulating_drugs"], list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest cognitive_map/tests/test_node_attributes.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# cognitive_map/node_attributes.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest cognitive_map/tests/test_node_attributes.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cognitive_map/node_attributes.py cognitive_map/tests/test_node_attributes.py
git commit -m "feat(cogmap): graph-derived node attributes"
```

---

### Task 5: Promiscuity-filtered expansion

**Files:**
- Create: `cognitive_map/expand.py`
- Create: `cognitive_map/tests/test_expand.py`

**Interfaces:**
- Consumes: `Graph` from Task 1.
- Produces: `expand(graph: Graph, seeds: list[str], cutoff: int = 100) -> set[str]` — 1-hop PPI neighbors of seeds, excluding seeds themselves and any neighbor with drug-degree > `cutoff`.

- [ ] **Step 1: Write the failing test**

```python
# cognitive_map/tests/test_expand.py
from cognitive_map.db import Graph
from cognitive_map.expand import expand

def test_expansion_filters_hubs_and_excludes_seeds():
    g = Graph()
    try:
        neighbors = expand(g, ["BDNF"], cutoff=100)
    finally:
        g.close()
    assert "BDNF" not in neighbors          # seeds excluded
    assert "ALB" not in neighbors           # promiscuous hub dropped
    assert "ABCB1" not in neighbors
    assert len(neighbors) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest cognitive_map/tests/test_expand.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# cognitive_map/expand.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest cognitive_map/tests/test_expand.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cognitive_map/expand.py cognitive_map/tests/test_expand.py
git commit -m "feat(cogmap): promiscuity-filtered 1-hop expansion"
```

---

### Task 6: Build orchestrator + export

**Files:**
- Create: `cognitive_map/build.py`
- Create: `cognitive_map/tests/test_build.py`

**Interfaces:**
- Consumes: `Graph`, `intervention_seeds`, `classify`, `brain_enrichment`, `node_attributes`, `expand` from Tasks 1–5.
- Produces: `build_substrate(graph: Graph) -> pandas.DataFrame` (one row per gene with columns `gene, klass, brain_enrichment, n_diseases, promiscuity, n_pathways, modulating_drugs, direction, magnitude, tradeoff, evidence_grade`); `main()` writing `cognitive_map/output/nodes.csv` and `cognitive_map/output/edges.csv`.

- [ ] **Step 1: Write the failing test**

```python
# cognitive_map/tests/test_build.py
from cognitive_map.db import Graph
from cognitive_map.build import build_substrate

def test_build_produces_scoped_table():
    g = Graph()
    try:
        df = build_substrate(g)
    finally:
        g.close()
    # seeds present
    assert (df["gene"] == "GRIN2B").any()
    # required columns exist, incl. the empty Phase-2 rigor columns
    for col in ["gene", "klass", "brain_enrichment", "n_diseases",
                "promiscuity", "direction", "tradeoff", "evidence_grade"]:
        assert col in df.columns
    # brain-scoping worked: GRIN2B more brain-enriched than the median
    grin = df.loc[df["gene"] == "GRIN2B", "brain_enrichment"].iloc[0]
    assert grin > df["brain_enrichment"].median()
    # Phase-2 columns created empty
    assert df["direction"].isna().all()
    assert df["tradeoff"].isna().all()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest cognitive_map/tests/test_build.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# cognitive_map/build.py
"""Phase 1 orchestrator: seed -> expand -> brain-scope -> attributes -> export."""
from pathlib import Path
import pandas as pd
from cognitive_map.db import Graph
from cognitive_map.seeds import intervention_seeds, classify, DISEASE_READOUT
from cognitive_map.brain_enrichment import brain_enrichment
from cognitive_map.node_attributes import node_attributes
from cognitive_map.expand import expand

OUT = Path(__file__).parent / "output"

def build_substrate(graph: Graph) -> pd.DataFrame:
    seeds = intervention_seeds() | set(DISEASE_READOUT)
    expanded = expand(graph, list(seeds))
    nodes = sorted(seeds | expanded)

    enr = brain_enrichment(graph, nodes)
    attrs = node_attributes(graph, nodes)

    rows = []
    for g in nodes:
        a = attrs[g]
        rows.append({
            "gene": g,
            "klass": classify(g),
            "brain_enrichment": round(enr.get(g, 0.0), 3),
            "n_diseases": a["n_diseases"],
            "promiscuity": a["promiscuity"],
            "n_pathways": len(a["pathways"]),
            "modulating_drugs": ";".join(a["modulating_drugs"]),
            # Phase-2 human-rigor columns — created EMPTY, never fabricated (spec §3)
            "direction": pd.NA,
            "magnitude": pd.NA,
            "tradeoff": pd.NA,
            "evidence_grade": pd.NA,
        })
    return pd.DataFrame(rows).sort_values("brain_enrichment", ascending=False)

def edges_among(graph: Graph, nodes: list[str]) -> pd.DataFrame:
    rows = graph.query(
        "MATCH (a:gene_protein)-[:protein_protein]-(b:gene_protein) "
        "WHERE a.node_name IN $nodes AND b.node_name IN $nodes AND a.node_name < b.node_name "
        "RETURN a.node_name AS source, b.node_name AS target",
        nodes=list(nodes))
    df = pd.DataFrame(rows, columns=["source", "target"])
    # unsigned/unweighted placeholders for Phase 2
    df["sign"] = pd.NA
    df["magnitude"] = pd.NA
    df["magnitude_status"] = "unknown"
    return df

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = Graph()
    try:
        nodes_df = build_substrate(g)
        edges_df = edges_among(g, nodes_df["gene"].tolist())
    finally:
        g.close()
    nodes_df.to_csv(OUT / "nodes.csv", index=False)
    edges_df.to_csv(OUT / "edges.csv", index=False)
    print(f"wrote {len(nodes_df)} nodes, {len(edges_df)} edges to {OUT}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest cognitive_map/tests/test_build.py -v`
Expected: PASS

- [ ] **Step 5: Run the pipeline end-to-end and eyeball output**

Run: `.venv/bin/python -m cognitive_map.build`
Expected: prints `wrote N nodes, M edges …`; inspect `cognitive_map/output/nodes.csv` — top rows are high brain-enrichment (GRIN2B/BDNF-grade), `direction`/`tradeoff` empty, `klass` shows trap/readout/intervention.

- [ ] **Step 6: Commit**

```bash
git add cognitive_map/build.py cognitive_map/tests/test_build.py
git commit -m "feat(cogmap): Phase 1 build orchestrator + export"
```

---

### Task 7: Dual report — markdown + interactive HTML (standing rule)

Per the user's standing preference: any report-to-verify gets both a markdown file AND a visually appealing interactive HTML. The substrate is a pathway network, so the HTML is an interactive pyvis graph (drag/zoom/hover), not a static table.

**Files:**
- Create: `cognitive_map/report.py`
- Create: `cognitive_map/tests/test_report.py`

**Interfaces:**
- Consumes: `cognitive_map/output/nodes.csv`, `edges.csv` from Task 6.
- Produces: `build_html(...) -> Path` writing `output/substrate.html`; `build_markdown(...) -> Path` writing `output/substrate_report.md`.

- [ ] **Step 1: Write the failing test**

```python
# cognitive_map/tests/test_report.py
from cognitive_map.build import main as build_main
from cognitive_map.report import build_html, build_markdown

def test_reports_render_and_contain_genes():
    build_main()                       # ensure nodes.csv / edges.csv exist
    html = build_html()
    md = build_markdown()
    assert html.exists() and md.exists()
    assert "GRIN2B" in html.read_text()
    assert "brain-enrichment" in md.read_text().lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest cognitive_map/tests/test_report.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cognitive_map.report'`

- [ ] **Step 3: Write minimal implementation**

```python
# cognitive_map/report.py
"""Dual report: markdown + interactive pyvis HTML of the built substrate."""
from pathlib import Path
import pandas as pd
from pyvis.network import Network

OUT = Path(__file__).parent / "output"
COLORS = {"intervention": "#4e79a7", "trap": "#e15759",
          "readout": "#f28e2b", "expanded": "#bab0ac"}

def build_html(nodes_csv=OUT / "nodes.csv", edges_csv=OUT / "edges.csv",
               out_html=OUT / "substrate.html") -> Path:
    nodes = pd.read_csv(nodes_csv)
    edges = pd.read_csv(edges_csv)
    net = Network(height="800px", width="100%", bgcolor="#ffffff",
                  font_color="#222", notebook=False)
    for _, r in nodes.iterrows():
        be = float(r["brain_enrichment"])
        net.add_node(str(r["gene"]), label=str(r["gene"]),
                     color=COLORS.get(r["klass"], "#999999"),
                     size=10 + 40 * be,
                     title=(f"{r['gene']} | {r['klass']} | brain {be:.2f} | "
                            f"{int(r['n_diseases'])} diseases | promisc {int(r['promiscuity'])}"))
    present = set(nodes["gene"].astype(str))
    for _, e in edges.iterrows():
        s, t = str(e["source"]), str(e["target"])
        if s in present and t in present:
            net.add_edge(s, t, color="#cccccc")
    net.force_atlas_2based()
    out_html.parent.mkdir(parents=True, exist_ok=True)
    net.save_graph(str(out_html))
    return out_html

def build_markdown(nodes_csv=OUT / "nodes.csv",
                   out_md=OUT / "substrate_report.md") -> Path:
    nodes = pd.read_csv(nodes_csv)
    lines = ["# Cognitive Substrate — Phase 1 Report", ""]
    lines.append(f"**Total nodes:** {len(nodes)}")
    for k, n in nodes["klass"].value_counts().items():
        lines.append(f"- {k}: {n}")
    lines += ["", "## Top 20 by brain-enrichment", "",
              "| gene | class | brain | diseases | promisc |",
              "|---|---|---|---|---|"]
    for _, r in nodes.head(20).iterrows():
        lines.append(f"| {r['gene']} | {r['klass']} | {r['brain_enrichment']} "
                     f"| {int(r['n_diseases'])} | {int(r['promiscuity'])} |")
    out_md.write_text("\n".join(lines) + "\n")
    return out_md
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest cognitive_map/tests/test_report.py -v`
Expected: PASS

- [ ] **Step 5: Open the HTML and eyeball it**

Run: `open cognitive_map/output/substrate.html`
Expected: an interactive network — intervention nodes blue, trap (developmental) red, readout orange; node size ∝ brain-enrichment; hover shows the attributes.

- [ ] **Step 6: Commit**

```bash
git add cognitive_map/report.py cognitive_map/tests/test_report.py
git commit -m "feat(cogmap): dual md + interactive HTML report"
```

---

## Self-Review

**Spec coverage:**
- §2 brain-scoping → Task 3 (`brain_enrichment`) + Task 6 (sort/attribute). Soft-downweight (attribute, no hard cut) ✓.
- §3.A graph columns → Task 4. §3.B empty rigor columns → Task 6 (created `pd.NA`) ✓.
- §3 edge schema (sign/magnitude/magnitude_status) → Task 6 `edges_among` placeholders ✓.
- §4 Phase 1 steps: seed (Task 2), expand+promiscuity-filter (Task 5), brain-scope (Task 3), attributes (Task 4), raw edges + bound + export (Task 6) ✓.
- Cascade triage (developmental=trap, disease=readout) → Task 2 `classify` ✓.
- Honesty rule #1 (no fabricated magnitudes) → Task 6 writes only graph facts; rigor columns empty ✓.

**Gaps / deferred to Phase 2 (intentional, not plan gaps):** `disease_systems` breakdown, `upstream_systemic` flag, brain-anatomy term curation refinement, and the `desired_direction`/`magnitude`/`tradeoff`/`evidence_grade` *values*. All are Phase 2 by spec §4. Columns are created here so Phase 2 has the schema.

**Placeholder scan:** No "TBD"/"add error handling"/"similar to Task N". All code complete.

**Type consistency:** `Graph.query` signature consistent across Tasks 3–6. `classify` return values match the test. `brain_enrichment`/`node_attributes`/`expand` signatures match their consumers in Task 6.
