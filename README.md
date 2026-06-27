# compbio-stuff — PrimeKG playground

Interactive exploration of **PrimeKG** (Precision Medicine Knowledge Graph) in
**Neo4j**: 129,375 nodes · 4,050,064 relationships · 10 node types · 30 edge types.

Source: Harvard Dataverse [doi:10.7910/DVN/IXA7BM](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/IXA7BM)
· [Zitnik Lab project page](https://zitniklab.hms.harvard.edu/projects/PrimeKG/)

---

## TL;DR — explore subgraphs now

```bash
cd ~/Desktop/compbio-stuff
./neo4j.sh start            # start the DB (already imported)
./neo4j.sh browser          # opens http://localhost:7474
```

Login `neo4j` / `primekg123`. Then work through
**[CYPHER_CHEATSHEET.md](CYPHER_CHEATSHEET.md)** — a guided progression from
"the schema" → ego-graphs → typed biology → paths → repurposing motifs.

First query to paste:

```cypher
MATCH p=(d:drug {node_name:'Metformin'})-[r]-(n) RETURN p LIMIT 200;
```

---

## What's here

| file | purpose |
|------|---------|
| `neo4j.sh`             | control script: `start \| stop \| status \| shell \| query \| browser \| reimport` |
| `CYPHER_CHEATSHEET.md` | copy-paste Cypher to load subgraphs and build intuition |
| `download_primekg.py`  | fetch raw PrimeKG CSVs from Harvard Dataverse |
| `prep_neo4j.py`        | convert raw CSVs → `neo4j-admin import` format (dedup, label sanitization) |
| `side_effect_trust.py` | score a drug's side effects: promiscuity + recovered SIDER label freq + mechanism |
| `annotate_graph.py`    | write verifiable provenance back onto the graph (`--undo` to remove) |
| `data/primekg/`        | raw downloads (`nodes.csv`, `edges.csv`, feature files) |
| `data/sider/`          | SIDER 4.1 drug-name + label-frequency tables (for provenance recovery) |
| `neo4j/`               | Neo4j container state: `data/` (the DB), `import/`, `logs/`, `plugins/` |
| `explore.py`           | *optional* lightweight pure-Python Dash explorer (no DB) — superseded by Neo4j |

---

## Rebuilding from scratch

If `neo4j/data` is wiped or you re-download the source:

```bash
source .venv/bin/activate
python download_primekg.py     # 1. fetch raw CSVs (~370 MB edges + features)
./neo4j.sh reimport            # 2. prep + bulk-import + start  (≈ 1 min)
```

`reimport` runs `prep_neo4j.py` then `neo4j-admin database import full` (the bulk
importer — loads all 4M edges in ~5 s), recreating the container.

---

## Container lifecycle

- **Data persists** in `neo4j/data/` (bind-mounted). `./neo4j.sh stop` then
  `./neo4j.sh start` keeps everything.
- The container is named `primekg`, image `neo4j:5.26`, ports **7474** (Browser /
  HTTP) and **7687** (Bolt). APOC plugin is enabled.
- Heap/pagecache set to 2 GB each — plenty for this graph.

## Schema reference

**Node labels** (`labels(n)[0]`): `gene_protein` (27.7K), `biological_process`
(28.6K), `disease` (17.1K), `effect_phenotype` (15.3K), `anatomy` (14.0K),
`molecular_function` (11.2K), `drug` (8.0K), `cellular_component` (4.2K),
`pathway` (2.5K), `exposure` (818).

**Relationship types** (`type(r)`), readable label on `r.display_relation`:
`drug_protein` (target/enzyme/carrier/transporter), `drug_drug`, `drug_effect`,
`indication`, `contraindication`, `off_label_use`, `disease_protein`,
`disease_phenotype_positive/negative`, `disease_disease`, `protein_protein`,
`pathway_protein`, `bioprocess_protein`, `molfunc_protein`, `cellcomp_protein`,
`anatomy_protein_present/absent`, `phenotype_protein`, `phenotype_phenotype`,
`exposure_*`, plus the ontology `*_*` hierarchy edges.

> Note: PrimeKG ships every undirected edge twice. `prep_neo4j.py` dedups to the
> canonical 4.05M undirected edges, so in Neo4j use direction-agnostic matches
> `(a)-[r]-(b)` (no arrow).
