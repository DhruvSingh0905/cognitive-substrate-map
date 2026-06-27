# PrimeKG in Neo4j — Subgraph Exploration Cheat-Sheet

Open **Neo4j Browser** → http://localhost:7474 · login `neo4j` / `primekg123`

Any query that returns **nodes / relationships / paths** renders as an interactive
graph you can drag, expand (double-click a node), and inspect. Queries that return
scalars/strings render as a table. To explore visually, return `p` (a path) or
`n, r, m`.

> **You're on the new Query tool** (Neo4j Workspace), not the classic Browser —
> so there's no "Connect result nodes" toggle (returned nodes auto-connect now).
> To set node captions, click a node-type pill in the result legend and pick the
> property to display. Expansion/render limits live behind the **gear icon
> (bottom-left)** — see §7.

---

## 0. The schema (start here)

```cypher
// visual meta-graph: which node types connect to which, via what
CALL db.schema.visualization();
```

```cypher
// the 10 node labels and their counts
MATCH (n) RETURN labels(n)[0] AS node_type, count(*) AS n ORDER BY n DESC;
```

```cypher
// the 30 relationship types and their counts
MATCH ()-[r]->() RETURN type(r) AS relation, count(*) AS n ORDER BY n DESC;
```

**Node labels:** `gene_protein`, `disease`, `drug`, `effect_phenotype`,
`anatomy`, `biological_process`, `molecular_function`, `cellular_component`,
`pathway`, `exposure`.

**Reading relationship semantics** — `type(r)` is the machine type; the readable
label lives on `r.display_relation`. E.g. `drug_protein` edges carry
`display_relation` ∈ {target, enzyme, carrier, transporter}.

---

## 1. Find a node

```cypher
// fuzzy / keyword search across ALL node names (uses the full-text index)
CALL db.index.fulltext.queryNodes('nodeName', 'diabetes') YIELD node, score
RETURN labels(node)[0] AS type, node.node_name AS name, score
ORDER BY score DESC LIMIT 15;
```

```cypher
// exact lookup (indexed on drug/disease/gene_protein)
MATCH (d:drug {node_name:'Metformin'}) RETURN d;
```

---

## 2. Ego-graphs — load a node's neighborhood

```cypher
// 1-hop: everything directly connected to Metformin  (returns a graph)
MATCH p=(d:drug {node_name:'Metformin'})-[r]-(n)
RETURN p LIMIT 200;
```

```cypher
// summarise that neighborhood by edge type + neighbor type (table)
MATCH (d:drug {node_name:'Metformin'})-[r]-(n)
RETURN type(r) AS relation, labels(n)[0] AS neighbor, count(*) AS n
ORDER BY n DESC;
```

```cypher
// 2-hop ego graph, capped so it stays readable
MATCH p=(d:drug {node_name:'Metformin'})-[*1..2]-(n)
RETURN p LIMIT 300;
```

---

## 3. Typed exploration (the useful biology)

```cypher
// drug -> protein targets (and how they act)
MATCH p=(d:drug {node_name:'Imatinib'})-[r:drug_protein]-(g:gene_protein)
RETURN g.node_name AS target, r.display_relation AS role
ORDER BY role;
```

```cypher
// a drug's clinical profile: indications / contraindications / off-label
MATCH p=(d:drug {node_name:'Metformin'})-[r:indication|contraindication|off_label_use]-(dis:disease)
RETURN p;
```

```cypher
// a drug's known side effects
MATCH p=(d:drug {node_name:'Atorvastatin'})-[:drug_effect]-(e:effect_phenotype)
RETURN p LIMIT 100;
```

```cypher
// disease -> associated genes/proteins -> the pathways they sit in
MATCH p=(dis:disease {node_name:'Alzheimer disease'})-[:disease_protein]-(g:gene_protein)-[:pathway_protein]-(pw:pathway)
RETURN p LIMIT 150;
```

```cypher
// disease -> phenotypes (HPO presentation)
MATCH p=(dis:disease {node_name:'cystic fibrosis'})-[:disease_phenotype_positive]-(ph:effect_phenotype)
RETURN p LIMIT 100;
```

---

## 4. Paths between two entities (why are they linked?)

```cypher
// shortest mechanistic path: a disease and a drug that treats it
MATCH (a:disease {node_name:'Alzheimer disease'}), (b:drug {node_name:'Donepezil'})
MATCH p = shortestPath( (a)-[*..6]-(b) )
RETURN p;
```

```cypher
// ALL short paths (<=4 hops) between a gene and a disease
MATCH (g:gene_protein {node_name:'APOE'}), (d:disease {node_name:'Alzheimer disease'})
MATCH p = allShortestPaths( (g)-[*..4]-(d) )
RETURN p LIMIT 25;
```

---

## 5. Bigger motifs (start seeing the graph "think")

```cypher
// drug-repurposing motif: other drugs that hit the SAME targets as Imatinib
MATCH (d1:drug {node_name:'Imatinib'})-[:drug_protein]-(g:gene_protein)-[:drug_protein]-(d2:drug)
WHERE d1 <> d2
RETURN d2.node_name AS candidate, collect(DISTINCT g.node_name) AS shared_targets,
       count(DISTINCT g) AS n_shared
ORDER BY n_shared DESC LIMIT 15;
```

```cypher
// protein-protein interaction neighborhood of a gene (PPI ego)
MATCH p=(g:gene_protein {node_name:'TP53'})-[:protein_protein]-(n:gene_protein)
RETURN p LIMIT 120;
```

```cypher
// genes shared between two diseases (comorbidity hint)
MATCH (a:disease {node_name:'Alzheimer disease'})-[:disease_protein]-(g:gene_protein)-[:disease_protein]-(b:disease {node_name:'type 2 diabetes mellitus'})
RETURN g.node_name AS shared_gene LIMIT 50;
```

---

## 5b. Filtering noise & connecting two nodes

PrimeKG hubs are dominated by a few edge types (a drug's `drug_drug`
"synergistic interaction" edges, a gene's `protein_protein` edges). Filter them
to see the rest.

```cypher
// EXCLUDE a noisy relation type
MATCH p=(d:drug {node_name:'Metformin'})-[r]-(n)
WHERE type(r) <> 'drug_drug'
RETURN p;
```

```cypher
// INCLUDE only the types you care about (whitelist in the pattern)
MATCH p=(d:drug {node_name:'Metformin'})-[:indication|contraindication|drug_effect]-(n)
RETURN p;
```

```cypher
// drug_drug carries only "synergistic interaction"; to filter on the readable
// label of any edge use r.display_relation:
MATCH p=(d:drug {node_name:'Imatinib'})-[r:drug_protein]-(g)
WHERE r.display_relation = 'target'      // drop carrier/enzyme/transporter
RETURN p;
```

**What connects two specific nodes** (beyond a direct edge) — their shared neighbors:

```cypher
// diseases BOTH drugs relate to (here: shared contraindications)
MATCH p=(a:drug {node_name:'Metformin'})-[:indication|contraindication|off_label_use]-(d:disease)-[:indication|contraindication|off_label_use]-(b:drug {node_name:'Tadalafil'})
RETURN p;
```

```cypher
// shortest mechanistic path between two nodes, EXCLUDING the noisy edge type
MATCH (a:drug {node_name:'Metformin'}), (b:drug {node_name:'Tadalafil'})
MATCH p = allShortestPaths( (a)-[*..4]-(b) )
WHERE none(rel IN relationships(p) WHERE type(rel) = 'drug_drug')
RETURN p LIMIT 20;
```

---

## 6. Handy controls

- **Expand a node:** double-click it in the graph pane → pulls its neighbors.
- **Limit always:** PrimeKG hubs are huge (some genes have 1000s of edges).
  Keep `LIMIT` on exploratory queries or Browser will choke.
- **Degree check before expanding:**
  ```cypher
  MATCH (n {node_name:'TP53'})-[r]-() RETURN count(r) AS degree;
  ```
- **Re-run last:** ↑ in the editor recalls history.

---

## 7. Make the viz navigable (the actual settings)

The #1 reason the graph feels unwieldy: **double-clicking a node expands ALL its
neighbors**, and PrimeKG hubs have thousands. Cap that.

**Gear icon (bottom of the far-left vertical strip) → Settings → Performance:**

| Setting | Default | Set to | Why |
|---------|---------|--------|-----|
| **Max new neighbors** | 1000 | **25** | double-click a hub adds ≤25 nodes, not 1000 — no hairball |
| **Visualization node limit** | 1000 | **500** | keeps a rendered scene readable |
| Record limit | 5000 | leave | rows fetched per frame |

These persist in your browser's `localStorage` (there's no server file — the panel
even says "settings are stored in your browser's local storage"). To set them
without clicking, paste this in the browser DevTools console **on the
localhost:7474 tab** and reload:

```js
const K='nx.v1.nx.settings', s=JSON.parse(localStorage.getItem(K)), q=JSON.parse(s.query);
q.maxNewNeighbours=25; q.maxVizNodes=500;
s.query=JSON.stringify(q); localStorage.setItem(K, JSON.stringify(s));
location.reload();
```

Still a force-directed layout though. For genuinely better navigation of a dense
KG, a dedicated tool (**SemSpect**, **G.V()**) beats tuning this — see README.

---

## 8. Weighted side effects (recovered provenance)

`annotate_graph.py` writes back only verifiable facts (run it / `--undo` to remove):

| property | on | meaning |
|---|---|---|
| `effect_phenotype.n_drugs` | node | # drugs sharing this side effect — **promiscuity** (low = specific) |
| `drug_effect.sider_label_freq` | edge | precise label frequency % (only where SIDER had a point estimate) |
| `drug_effect.sider_freq_tier` | edge | `rare`…`very common` — clinically established on the drug's label |

```cypher
// telmisartan's CLINICALLY ESTABLISHED side effects (on-label), most frequent first
MATCH (d:drug {node_name:'Telmisartan'})-[r:drug_effect]-(e:effect_phenotype)
WHERE r.sider_freq_tier IS NOT NULL
RETURN e.node_name AS side_effect, r.sider_freq_tier AS tier,
       r.sider_label_freq AS freq_pct, e.n_drugs AS promiscuity
ORDER BY r.sider_label_freq DESC;
```

```cypher
// rank ALL of a drug's side effects by specificity (Hetionet-style promiscuity)
MATCH (d:drug {node_name:'Telmisartan'})-[r:drug_effect]-(e:effect_phenotype)
RETURN e.node_name AS side_effect, e.n_drugs AS n_drugs,
       coalesce(r.sider_freq_tier,'— unverified —') AS label_status
ORDER BY e.n_drugs ASC;
```

> **CRITICAL — how to read `null`:** `sider_freq_tier IS NULL` means **unknown**, NOT
> "fake/confounded." A null edge is either genuinely off-label (FAERS/OFFSIDES-mined)
> **or** a name that didn't match SIDER (PrimeKG uses HPO terms, SIDER uses MedDRA —
> only ~19% of edges match by exact name). Never filter `IS NULL` and call those
> "the confounded ones." Treat `IS NOT NULL` as a positive trust signal; treat null
> as "no evidence recovered," nothing more.

---

## From the command line (no Browser)

```bash
./neo4j.sh shell                      # interactive cypher-shell
./neo4j.sh query "MATCH (n) RETURN count(n);"
./neo4j.sh status                     # counts + container health
./neo4j.sh stop                       # data persists; restart with: ./neo4j.sh start
```
