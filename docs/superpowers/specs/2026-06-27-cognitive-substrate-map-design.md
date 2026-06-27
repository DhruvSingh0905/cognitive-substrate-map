# Cognitive Substrate Map — Design Spec

**Date:** 2026-06-27
**Status:** Draft for review
**Type:** Theoretical / learning project. Built on the local PrimeKG-in-Neo4j setup (`~/Desktop/compbio-stuff`).

---

## 1. Purpose

A systematic, mechanism-grounded **map of cognitive-optimization intervention points**, encoded as a signed/weighted/directed regulatory network, that we can (a) score honestly for tradeoffs and evidence and (b) run a toy perturbation simulation + optimization over.

Primary goal is **learning / intuition-building**. The artifact (the scored map + the scoring/simulation methodology) is the product.

### Framing discipline (load-bearing)

The naive framing — "find genes/enzymes we don't need and suppress them" — is **wrong** and the project must not inherit it. Pathways are pleiotropic; the thing you downregulate for benefit A is doing essential job B elsewhere (angiotensin II is *load-bearing* for BP/fluid/renal function, not vestigial). There is almost no free lunch.

**Corrected framing:** find regulatory nodes where *shifting the setpoint* produces net benefit **despite tradeoffs**, and characterize the tradeoffs. The tradeoff column is the rigor. **A node with no listed tradeoff means we haven't looked hard enough — not that it is free.**

### Deliverable boundary

The deliverable is **the map + the methodology**. Every node carries benefit-direction, tradeoff, and evidence-grade; **no node carries a dose or a personal recommendation.** This is a mechanism/intuition artifact, explicitly **not** a protocol or "stack to take."

---

## 2. Scope — brain-canonical hubs only

This is **not** a complete map of the brain. It is a graph of the **most canonical regulatory hubs that act *within* the brain.** Nodes that are present in brain but operate body-wide (angiotensin machinery, broad metabolic/housekeeping genes) are **downweighted or excluded**, because perturbing them = systemic effects, which defeats the purpose.

### Brain-specificity score (validated)

Computed from PrimeKG's tissue-expression layer (Bgee `anatomy_protein_present` edges):

```
brain_enrichment(gene) = (# brain-region tissues it's expressed in) / (# total tissues it's expressed in)
```

Validation (run 2026-06-27): GRIN2B 52%, BDNF 34%, DRD2 26%, CHRNA7 21% (brain-canonical, retained) vs. AGTR1 **5.2%**, ACE 12%, ALB 11%, INS 0% (systemic, downweighted). The metric reproduces the angiotensin intuition as a number.

- 628 brain-related anatomy nodes exist; 24,829 genes carry expression edges.
- **Refinement needed:** the brain-anatomy term list currently includes cross-species/developmental terms (zebrafish "neural keel/rod"). Phase 1 curates it to relevant adult-human brain regions.
- `brain_enrichment` is both a **node attribute** and a **filter** (threshold/downweight below a cutoff, e.g., retain ≥ ~15–20%, tunable).

---

## 3. Data model — signed, weighted, directed regulatory network

### Nodes (row unit = gene/protein)

Pathways are a *grouping attribute*, not the row unit, because drugs act on proteins and direction (↑/↓) is defined per protein. The "gene pathways" view is a roll-up.

**Graph-fillable columns (mechanical, from PrimeKG):**
| column | source |
|---|---|
| `pathways`, `bio_processes` | pathway_protein, bioprocess_protein |
| `brain_enrichment` | anatomy_protein_present (§2) |
| `n_diseases`, `disease_systems` | disease_protein — **provisional systemic-tradeoff proxy** |
| `promiscuity` | drug-degree, pathway-degree (pleiotropy/hub proxy) |
| `modulating_drugs` | drug_protein, by role (target/enzyme/transporter) |

**Human-rigor columns (literature, NOT graph-fillable — the spine):**
| column | why the graph can't supply it |
|---|---|
| `desired_direction` (↑/↓ for cognition) | graph is **unsigned** |
| `benefit_strength`, `evidence_grade` | no effect sizes / evidence weighting in PrimeKG |
| `tradeoff` (what essential job perturbing it breaks, how badly) | **no "and this also breaks B" edge exists** |

### Edges (carry the physics for simulation)

- **regulatory edge** `A → B`: `sign` (+/−), `magnitude` (% or bucket), `magnitude_status`, `confidence`, `mechanism`, `citation`
- **drug → node edge**: `direction` (↑/↓), `magnitude` (%Δ if known), `magnitude_status`, `dose/context`, `citation`

### Honesty rule #1 — magnitude status

Every weight is tagged `magnitude_status ∈ {quantified, sign-only, unknown}`:
- `quantified` — a real, cited % change.
- `sign-only` — direction established, magnitude unpublished (honest; most edges start here).
- `unknown` — neither.

**Fabricating a % is leaving science.** The simulation propagates `sign-only`/`unknown` as uncertainty (e.g., run at magnitude bounds), never as false precision.

---

## 4. The three phases

### Phase 1 — Build the subgraph (mechanical; PrimeKG)

1. **Seed** the brain node set:
   - Curated canonical cognitive genes by system: cholinergic (CHRNA7, ACHE, CHAT…), glutamatergic (GRIN2A/B, GRIA*, GRM*…), dopaminergic (DRD1–5, COMT, TH, SLC6A3…), serotonergic, GABAergic; plasticity (BDNF, NTRK2, CREB1, MTOR, ARC, CAMK2A…); neuroinflammation (TREM2, IL1B, TNF, NFKB1…); clearance/proteostasis (AQP4, autophagy genes, APP, MAPT); metabolic (AMPK complex…).
   - + PrimeKG `disease_protein` from cognitive diseases (Alzheimer's, cognitive decline, …) and `bioprocess_protein` from cognitive GO terms (learning, memory, cognition, synaptic plasticity, LTP).
2. **Expand** 1 hop via PPI / shared-pathway, **promiscuity-filtered** (drop ALB/ABCB1/CYP-grade hubs).
3. **Brain-scope:** compute `brain_enrichment`, downweight/threshold systemic nodes.
4. **Attach** graph-derived columns (§3) and raw candidate edges (unsigned: PPI, pathway co-membership, drug→target) for Phase 2 to sign/weight.
5. **Bound** to the core substrate (~a few hundred brain-canonical nodes), expandable.

**Output:** brain-scoped substrate graph with graph-derived attributes + empty human-rigor columns.

### Phase 2 — Research pass (literature; the slow rigor)

Fill `sign`, `magnitude` (% where real, else `sign-only`), `confidence`, and the real `tradeoff` per node/edge, with citations. This is where the project's value lives. LLM-assisted curation is allowed but every claim is cited and adversarially checked; uncited magnitude = `sign-only` at most.

### Phase 3 — Simulate + optimize (toy)

- **Simulation model:** linear / log-linear **signed influence propagation** — set an intervention vector, propagate signed magnitudes along edges, read out effect on cognitive-benefit nodes and on systemic-cost nodes.
- **Optimization:** choose the intervention/direction vector maximizing `Σ benefit − λ·Σ systemic_cost`, weighted by `evidence_grade`.

### Honesty rule #2 — the simulation is a toy

Linear propagation ignores nonlinearity, saturation, feedback, and homeostatic compensation (push AT1R down → renin compensates). The sim is for **intuition about direction and rough net magnitude, not prediction.** It is labeled as such everywhere it appears.

---

## 5. Open questions / refinements (to resolve in planning)

- Curate the adult-human brain-anatomy term list (drop developmental/cross-species).
- Set the `brain_enrichment` retention threshold.
- Phase-2 literature sourcing workflow + citation/verification standard.
- Storage: extend the Neo4j graph with these properties, or a separate matrix/table artifact? (Leaning: Neo4j properties + an exported matrix for the optimizer.)

---

## 6. Non-goals (YAGNI)

- Not a whole-brain or whole-body map.
- Not a dynamical systems-biology simulator (no ODEs, kinetics, or validated dynamics).
- Not a protocol, dosing guide, or recommendation engine.
- Not chasing the newest unpublished compounds — the graph rewards well-characterized nodes, which is fine.
