# A Network-Control Approach to a Learning-Optimal Brain State

**Dhruv Singh** · Work in progress · a personal project · July 2026

> ⚠️ **Status — core pipeline complete (work in progress).** A personal learning project, not peer-reviewed. The full chain now runs end to end — substrate, propagation, controllability, objective, uncertainty, optimizer — with a first result (§7) that survives a nonlinear cross-check (§8). Refinement continues; feedback welcome.

> **Overview.** This project treats a biomedical knowledge graph as a signed, directed control system and asks a simple question with a hard answer: which genes would you nudge, and by how much, to move the brain toward a state that's good for learning — without disturbing everything else? The scoring objective, uncertainty pass, and optimizer now run end to end: one high-leverage node — **BDNF** — stands out, with a small optimal set and sharp diminishing returns rather than a synergistic drug stack, and the finding holds under a nonlinear cross-check.

*Academic-styled HTML version: [deep-dive.html](deep-dive.html)*

## 1. Substrate

The base graph is PrimeKG [1] — 129,375 nodes and about 4 million edges across ten types (genes, drugs, diseases, pathways, and so on), from the Hetionet / Rephetio line of work [2].

Most of that graph has nothing to do with learning, so I keep only genes mostly expressed in brain tissue. The score for a gene $v$ is the fraction of the tissues it appears in that are brain, over PrimeKG's `anatomy_protein_present` edges $E_a$:

$$e(v)=\frac{\bigl|\{a:(v,a)\in E_a,\ a\in A_{\mathrm{brain}}\}\bigr|}{\bigl|\{a:(v,a)\in E_a\}\bigr|},\qquad \text{keep if } e(v)\ge 0.15 \ \wedge\ \deg_a(v)\ge 5 \tag{1}$$

*In words —* keep a gene only if a decent share of the tissues it's active in are brain, and only if it's active in enough places for that share to mean something.

After pruning: 280 nodes in four layers (70 intervention, 15 input, 6 readout, 2 off-limits, 187 one-hop neighbors), 3,912 directed edges (2,871 signed: 2,253 activating, 618 inhibiting), one 200-node feedback loop.

![Figure 1 — the 280-node substrate](assets/graph_brain_substrate.png)

## 2. The propagation operator

Put the edges in a matrix $W$: the entry $W_{ij}$ is $+1$, $-1$, or $0$ for the effect of gene $j$ on gene $i$. A hub gene with many out-edges would swamp everything, so divide each gene's column by its out-degree — the PageRank trick [3] ($d^{\mathrm{out}}_j=\sum_i|W_{ij}|$):

$$\hat{W}=W\,D_{\mathrm{out}}^{-1},\qquad \hat{W}_{ij}=\frac{W_{ij}}{\sum_k|W_{kj}|} \tag{2}$$

*In words —* spread each gene's outgoing effect evenly across the genes it points at, so one gene that talks to everyone can't dominate.

Each column now sums to 1 in absolute value, forcing the largest eigenvalue to be $\le 1$ (Perron–Frobenius) and keeping the next step stable (measured: $\rho(\hat W)=0.544$). Dividing by out-degree suits a *directed* graph; the symmetric GCN form $D^{-1/2}\tilde W D^{-1/2}$ [6] is for undirected graphs.

![Figure 2 — out-degree is heavy-tailed](assets/fig_outdegree.png)

## 3. Propagation by random-walk-with-restart

Push a signal $p$ into one gene and let it spread, pulling a fraction $\alpha$ back to the source each step [5,4]:

$$x^{(t+1)}=(1-\alpha)\,\hat{W}x^{(t)}+\alpha\,p \tag{3}$$

*In words —* at each step, spread the signal one hop, but yank a fixed slice $\alpha$ back to the gene you started from.

Solving for the value it settles to gives a closed form (a sum over every path length $k$):

$$x^{*}=\alpha\bigl(I-(1-\alpha)\hat{W}\bigr)^{-1}p=\alpha\sum_{k\ge0}(1-\alpha)^{k}\hat{W}^{k}p \tag{4}$$

*In words —* the settled response; each extra hop is discounted by $(1-\alpha)^k$, so far-away genes barely feel it.

Far hops are discounted, so the effect stays local. The 200-node feedback loop is why we solve for a settled value instead of one push.

![Figure 3 — measured decay vs hop distance](assets/fig_decay.png)

## 4. Controllability

Can a few inputs steer the whole thing? As a linear system with input map $B$, $\dot{x}=Wx+Bu$, it's fully steerable when the controllability matrix has full rank (Kalman [7]):

$$\operatorname{rank}\mathcal{C}=N,\qquad \mathcal{C}=[\,B,\ WB,\ W^{2}B,\ \dots,\ W^{N-1}B\,] \tag{5}$$

*In words —* you can reach any state exactly when your inputs, pushed through more and more hops, together cover all $N$ directions.

Testing that directly is impractical, so I use structural controllability (Lin [8]; Liu–Slotine–Barabási [9]): the fewest genes you must control is the number left unmatched after pairing up the network as well as possible,

$$N_{D}=\max\bigl(N-|M^{*}|,\ 1\bigr) \tag{6}$$

*In words —* match each gene to one it directly drives; whatever's left over is what you control by hand.

Matching via Hopcroft–Karp [10]. Result: all 280 reachable, but full control needs **81 driver genes, only 37 druggable** — so you can't push it to any state. You *can* steer the readouts you care about (target control [11]), which takes fewer inputs.

![Figure 4 — driver nodes on the substrate](assets/fig_drivers.png)

| quantity | value |
|---|---|
| druggable inputs \|𝒟\| | 172 |
| reachable \|R\|/N | 280 / 280 |
| min drivers N_D (full) | 81 |
| drivers druggable | 37 / 81 |
| feedback SCC | 200 |

## 5. Target state and objective

The target is a vector $d$ of desired changes. Key fact: most brain variables have a sweet spot, an inverted-U (Yerkes–Dodson [18]; Arnsten [19]) — dopamine, arousal, cortisol, E/I balance, mTOR. Benefit is how much closer to the target you get:

$$b_i=\lvert d_i\rvert-\lvert x^{*}_i-d_i\rvert \tag{7}$$

*In words —* positive if the nudge moved a gene toward its ideal level, negative if it pushed past it.

Total benefit weights each gene by confidence (readouts count 0); cost is effort plus off-target movement:

$$B(p)=\sum_i w_i\,b_i,\qquad C(p)=\lVert p\rVert_1+\gamma\sum_{j\,\notin\,T}\lvert x^{*}_j\rvert \tag{8}$$

*In words —* add up the good across genes, then subtract the cost: effort plus collateral elsewhere.

Current target vector: 94 genes, 43 set-point / 30 up / 12 down.

![Figure 5 — the target set](assets/graph_target_set.png)

## 6. Uncertainty quantification

Our confidence in each target isn't uniform — some directions are well-established, others shaky — so a single score would overstate precision. We run it many times, sampling each target's confidence weight within its interval (Monte-Carlo [12]), and report a range,

$$\widehat{\mathrm{CI}}_{90\%}=\bigl[\,Y_{(\lceil0.05M\rceil)},\ Y_{(\lfloor0.95M\rfloor)}\,\bigr] \tag{9}$$

*In words —* run it many times, sort the scores, report the middle 90% as an honest range.

Then use Sobol indices [13,14] to see which unknown drives the range:

$$S_i=\frac{\operatorname{Var}_{\theta_i}\!\bigl(\mathbb{E}[Y\mid\theta_i]\bigr)}{\operatorname{Var}(Y)},\qquad S_{T_i}=\frac{\mathbb{E}\bigl[\operatorname{Var}(Y\mid\theta_{\sim i})\bigr]}{\operatorname{Var}(Y)} \tag{10}$$

*In words —* of all the wobble in the score, how much comes from each unknown — so you know which fact to check first.

Edge *strengths* are deliberately left out: they're treated as sign-only (unit weight), because there's no principled distribution to sample — inventing one would add noise, not information.

## 7. Optimization

No single best answer — more benefit usually costs more — so the output is a trade-off curve (Pareto front), traced with the ε-constraint method [15]:

$$\max_p\ B(p)\quad\text{s.t.}\quad C(p)\le\varepsilon \tag{11}$$

*In words —* squeeze out the most benefit at each cost budget, then vary the budget to draw the whole curve.

A plain weighted sum would quietly skip part of the curve when it bends the wrong way (non-convex) [16,17]; ε-constraint doesn't.

**Result.** Scoring every actionable knob (downstream effect only), one gene stands out: pushing **BDNF** up gives ~5× the downstream benefit of the next-best knob, and under the §6 confidence-weight uncertainty it's the #1 knob in **100%** of 2,000 draws (narrow band).

![Figure 6 — single-knob ranking with confidence bands](assets/knob_bands.png)

Searching combinations (all singles/pairs/triples + a greedy path), the benefit–cost front has a **sharp knee at BDNF** — it captures most of the achievable downstream benefit at low cost, and adding knobs gives steep diminishing returns. The top plasticity knobs are *redundant* (overlapping downstream), so there's no synergistic stack; the optimal set is small.

![Figure 7 — benefit–cost Pareto front](assets/pareto_front.png)

## 8. Validation

Test-driven throughout — each stage is gated by unit tests. The main sign check: push one gene by $+1$ and confirm the response sign matches the edge sign in the database — not the model. All eight match ($\alpha=0.15$, $\rho=0.544$):

![Figure 8 — predicted signs vs curated edges](assets/fig_signcheck.png)

| perturb | → target | edge | $x^{*}$ | check |
|---|---|---|---|---|
| `CREB1 ↑` | BDNF | +1 | +0.0030 | ✓ |
| `CREB1 ↑` | JUN | −1 | −0.0027 | ✓ flip |
| `CREB1 ↑` | NTRK2 | +1→+1 | +0.0080 | ✓ net |
| `GSK3B ↑` | CREB1 | −1 | −0.0041 | ✓ inhib |
| `AKT1 ↑` | NFKB1 | +1→−1 | −0.0008 | ✓ net-flip |

One nice check: two-hop `NTRK2` moves more than one-hop `BDNF`, because CREB1's ~40 out-edges split its signal while BDNF's single out-edge passes it straight through — exactly what (2) predicts.

**Nonlinear cross-check.** The engine is linear, so the headline could be an artifact of that. Re-running the ranking under a saturating (tanh) propagation, pushing knobs deep into the nonlinear regime: **BDNF stays #1 at every strength** (its lead grows as the system saturates), and combinations stay roughly additive (no synergy). The finding survives.

![Figure 9 — nonlinear pressure test](assets/pressure_test.png)

## 9. Groundedness and assumptions

The layers rest on different evidence: brain-scoping is computed, edge signs are curated, edge strengths are mostly sign-only, and the target vector is hand-built. $\hat W$ is a linear (first-order) stand-in for nonlinear biology, so results hold for small nudges near the resting state, not big ones. Output: an ordered list of interventions and a trade-off map — not exact fold-changes, not medical advice.

## 10. Status & roadmap

**Built, tested, and run:** the full pipeline — substrate (§1), operator + RWR engine (§2–3), controllability (§4), the objective (§5), the uncertainty pass (§6), the ε-constraint optimizer (§7), and the nonlinear cross-check (§8). **Further out:** real edge strengths where measured data exists, a richer intervention model (dose, timing), and validation against real perturbation datasets. A living write-up.

---

## References

1. Chandak, P., Huang, K., Zitnik, M. Building a knowledge graph to enable precision medicine. *Scientific Data* **10**, 67 (2023).
2. Himmelstein, D.S. et al. Systematic integration of biomedical knowledge prioritizes drugs for repurposing. *eLife* **6**, e26726 (2017).
3. Page, L., Brin, S., Motwani, R., Winograd, T. The PageRank Citation Ranking. *Stanford InfoLab* (1999).
4. Gasteiger, J., Bojchevski, A., Günnemann, S. Predict then Propagate: GNNs meet Personalized PageRank (APPNP). *ICLR* (2019).
5. Tong, H., Faloutsos, C., Pan, J-Y. Fast Random Walk with Restart and Its Applications. *ICDM* (2006).
6. Kipf, T.N., Welling, M. Semi-Supervised Classification with Graph Convolutional Networks. *ICLR* (2017).
7. Kalman, R.E. Mathematical Description of Linear Dynamical Systems. *J. SIAM Control* **1**(2), 152–192 (1963).
8. Lin, C-T. Structural Controllability. *IEEE Trans. Automatic Control* **19**(3), 201–208 (1974).
9. Liu, Y-Y., Slotine, J-J., Barabási, A-L. Controllability of complex networks. *Nature* **473**, 167–173 (2011).
10. Hopcroft, J.E., Karp, R.M. An $n^{5/2}$ Algorithm for Maximum Matchings in Bipartite Graphs. *SIAM J. Comput.* **2**(4), 225–231 (1973).
11. Gao, J., Liu, Y-Y., D'Souza, R.M., Barabási, A-L. Target control of complex networks. *Nature Communications* **5**, 5415 (2014).
12. JCGM 101:2008. Propagation of distributions using a Monte Carlo method (GUM Supplement 1). *BIPM* (2008).
13. Sobol, I.M. Global sensitivity indices for nonlinear models and their Monte Carlo estimates. *Math. Comput. Simul.* **55**, 271–280 (2001).
14. Saltelli, A. et al. *Global Sensitivity Analysis: The Primer.* Wiley (2008).
15. Haimes, Y.Y., Lasdon, L.S., Wismer, D.A. The ε-constraint method. *IEEE Trans. Syst. Man Cybern.* **1**(3), 296–297 (1971).
16. Boyd, S., Vandenberghe, L. *Convex Optimization* (§4.7). Cambridge Univ. Press (2004).
17. Marler, R.T., Arora, J.S. Survey of multi-objective optimization methods for engineering. *Struct. Multidiscip. Optim.* **26**, 369–395 (2004).
18. Yerkes, R.M., Dodson, J.D. The relation of strength of stimulus to rapidity of habit-formation. *J. Comp. Neurol. Psychol.* **18**, 459–482 (1908).
19. Arnsten, A.F.T. Stress signalling pathways that impair prefrontal cortex structure and function. *Nat. Rev. Neurosci.* **10**, 410–422 (2009).

---

[Project overview](index.html) · [source code](https://github.com/DhruvSingh0905/cognitive-substrate-map) · personal learning project — not medical advice.
