# Optimizing the Brain for Learning — a Network-Control Approach

Turning a biomedical knowledge graph into a **signed, directed control system**, and asking a control-theory question of it: which genes do you nudge — and by how much — to move the brain toward a learning-optimal state, at minimal systemic cost?

*A personal deep-dive into knowledge graphs, network propagation, structural controllability, and multi-objective optimization. Everything below is a model — see the honesty section. Not medical advice.*

**129k KG nodes · 280 brain core · 2,871 signed edges · ρ(Ŵ) = 0.544 · 8/8 sign checks ✓**

## 01 · The premise

Biology isn't a spreadsheet. Genes regulate other genes through transcription factors and signalling cascades, so cognition emerges from a **network**, not from any single gene. Modeling that network as a graph turns "how do I improve learning?" into a two-part engineering question:

1. **Map** the regulatory network of cognition as a directed, signed graph.
2. Find the **optimal set of node perturbations** — gene up/down-regulations — that cascade the rest of the network into a "learning-optimal" state while minimizing off-target movement.

It's a control problem.

## 02 · The substrate: a knowledge graph, scoped to the brain

The base is [PrimeKG](https://github.com/mims-harvard/PrimeKG) — 129,375 nodes and ~4M edges across ten types (genes/proteins, drugs, diseases, pathways, anatomy, phenotypes, …). The lineage is [Hetionet / Rephetio](https://het.io), a hetnet built to *repurpose drugs* by scoring the metapaths connecting a compound to a disease.

![biological knowledge graph](assets/graph_bio_graph.png)

I re-purposed the idea for the brain: scope the whole-body graph down to the subnetwork that controls learning — glutamate, BDNF, GABA, the cholinergic and dopaminergic systems — using tissue-expression enrichment, then bound it. The result is **280 nodes / 3,912 directed edges (2,871 signed: 2,253 activating, 618 inhibitory)** in four layers (intervention, input, readout, bounded expansion), with a single 200-node strongly-connected feedback core.

![the cognitive substrate](assets/graph_brain_substrate.png)

## 03 · From graph to operator

Each edge carries a direction and a sign — $+1$ activation (gas pedal), $-1$ inhibition (brake) — stacked into a matrix oriented so influence flows *source → target*: $W_{ij}=\operatorname{sign}(j\to i)$.

**The hub problem, and the PageRank fix.** A regulator touching 40 targets would dominate everything. Column-normalize by out-strength — the PageRank transition operator:

$$\hat{W}_{ij} = \frac{W_{ij}}{\sum_k \lvert W_{kj}\rvert}$$

A hub's influence is now *split* across its targets. And the absolute-value matrix is column-stochastic, so $\rho(\hat{W}) \le 1$ — guaranteeing the propagation below converges. (The symmetric GCN form $\hat{W}=D^{-1/2}\tilde{W}D^{-1/2}$ is the undirected analogue; it damps the receiver instead of splitting the sender. For a directed regulatory graph the PageRank form is correct.)

![mTOR hub](assets/graph_mtor_hub.png)

## 04 · Propagation: random-walk-with-restart

Inject a signal $p$ (push one gene) and diffuse it, with a restart probability $\alpha$ that re-anchors it at the source each step — a random walk with restart, identical to Personalized PageRank / APPNP:

$$x^{(t+1)} = (1-\alpha)\,\hat{W}\,x^{(t)} + \alpha\,p$$

At the fixed point, the closed form is a resolvent — equivalently a damped power series over hop-count $k$:

$$x^{*} = \alpha\bigl(I-(1-\alpha)\hat{W}\bigr)^{-1}p = \alpha\sum_{k\ge 0}(1-\alpha)^{k}\hat{W}^{k}p$$

![random walk with restart](assets/diagram_rwr.png)

The $(1-\alpha)^{k}$ term is an **over-smoothing guard**: deep hops are exponentially suppressed, so $x^{*}$ never collapses to a uniform blob. And because the substrate has a 200-node feedback loop, there's no one-shot answer — you solve the *steady state under feedback*, which is exactly what the resolvent computes.

## 05 · Can you even steer it? Controllability

Is the system controllable — can a few inputs drive it to an arbitrary state? Kalman controllability asks whether the controllability matrix spans the state space:

$$\mathcal{C} = [\,B,\ WB,\ W^{2}B,\ \dots,\ W^{N-1}B\,]$$

For a large network, direct rank tests are impractical, so I used **structural controllability** (Liu–Barabási): the minimum driver count equals the nodes left unmatched by a maximum matching $M^{*}$ on the graph's bipartite representation:

$$N_D = \max\!\left(N - |M^{*}|,\ 1\right)$$

Denser wiring → larger matching → fewer independent drivers ($\langle k\rangle \propto 1/N_D$). On the substrate: **all 280 nodes are reachable**, full arbitrary-state control needs 81 drivers (~35 druggable), but **target-control of the cognitive core is plausible** — all the optimizer needs. The 200-node feedback core is the structural signature of homeostasis.

## 06 · The target: what "optimal" means

I hand-curated a 94-gene target vector $d$ from a literature sweep. The dominant finding: **most cognitive variables are not "maximize" — they're set-points with an inverted-U** (Yerkes–Dodson / Arnsten): dopamine, arousal, cortisol, E/I balance, mTOR. 43 of 94 targets are inverted-U, so a naïve "turn up the good genes" objective gets nearly half the directions wrong. A second finding: some genes are *readouts* (activity gauges), not levers.

![target gene set](assets/graph_target_set.png)

## 07 · Scoring an intervention

Benefit is **distance-reduction toward the target** — rewarding partial progress, penalizing overshoot (the far arm of the inverted-U):

$$b_i = \lvert d_i\rvert - \lvert x^{*}_i - d_i\rvert$$

Aggregate benefit weights each node by confidence; cost prices intervention effort ($L_1$ → few knobs) plus systemic collateral:

$$B(p)=\sum_i w_i\,b_i, \qquad C(p)=\lVert p\rVert_1 + \gamma\sum_{j\,\notin\,\text{targets}} \lvert x^{*}_j\rvert$$

## 08 · Uncertainty and optimization

Many edge magnitudes are sign-only, so a single number would be dishonest. I propagate input uncertainty by **Monte-Carlo** (GUM-S1): sample the uncertain inputs, re-run, report a coverage *band* per intervention. A **Sobol** sensitivity analysis attributes the band — telling you which unknown to verify to shrink it.

The optimization is multi-objective (max $B$, min $C$), so the honest output is a **Pareto front**. Because the system is small, I trace it exactly with the **ε-constraint** method ($\max B$ s.t. $C\le\varepsilon$, sweeping $\varepsilon$) rather than a weighted sum — which, on a non-convex problem, silently misses parts of the front.

## 09 · Does it work? Validation

Test-driven (11 tests, incl. real-substrate integration). The load-bearing check: perturb a gene and confirm response signs match the raw edge signs from the database — *not* the model. At $\alpha=0.15$, $\rho(\hat{W})=0.544$:

| perturb | → target | edge | observed $x^{*}$ | check |
|---|---|---|---|---|
| `CREB1 ↑` | BDNF | +1 | +0.0030 | ✓ |
| `CREB1 ↑` | JUN | −1 | −0.0027 | ✓ flip |
| `CREB1 ↑` | NTRK2 | +1→+1 | +0.0080 | ✓ net |
| `GSK3B ↑` | CREB1 | −1 | −0.0041 | ✓ inhibition |
| `AKT1 ↑` | NFKB1 | +1→−1 | −0.0008 | ✓ net-flip |

**Hub-damping, visible.** Two-hop `NTRK2` moved *more* than one-hop `BDNF`: `CREB1` has ~40 out-edges so its per-target influence is divided ~40×, while `BDNF` has one out-edge and transmits cleanly. Falls out of the operator for free.

The KG substrate carries real biological provenance — e.g. why an angiotensin-receptor blocker sits near metabolic disease:

![telmisartan to diabetes via PPARG](assets/graph_telmisartan_diabetes.png)

Telmisartan → **PPARG** → type-2 diabetes: the drug's off-target PPARγ agonism is the single shared node linking it to the disease in PrimeKG.

## 10 · The honesty ladder

Every layer sits on a different rung: **brain-scoping** is computed; **edge direction + sign** is curated; **edge magnitude** is mostly sign-only; the **objective + optimizer** are math-checked but consume a hand-built target vector. And the propagation is a *linear response to a nonlinear system* — valid for modest perturbations near baseline. So the deliverable is a **ranking of interventions and a map of trade-offs**, not fold-change predictions, and not a protocol. A math game — a serious one, but a game.

---

**Stack:** PrimeKG · Neo4j · NetworkX · Personalized PageRank / APPNP · Liu–Barabási controllability · ε-constraint / Pareto · Monte-Carlo (GUM-S1) · Sobol SA

Code + shorter overview: [the project page](index.html) · [GitHub](https://github.com/DhruvSingh0905/cognitive-substrate-map). A personal learning project — **not medical advice, dosing, or a protocol.**
