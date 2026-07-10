# A Network-Control Approach to a Learning-Optimal Brain State

**Dhruv Singh** · Independent project · July 2026

> **Abstract.** We cast a biomedical knowledge graph as a signed, directed control system and ask a control-theoretic question of it: which genes should be perturbed, and by how much, to steer the brain toward a learning-optimal state at minimal systemic cost? Starting from PrimeKG [1] (129,375 nodes), we scope to a 280-node brain core (2,871 signed edges, a 200-node feedback component), propagate perturbations by random-walk-with-restart / Personalized PageRank [4], analyze structural controllability [9], define a set-point-aware objective, quantify uncertainty by Monte-Carlo propagation [12] with Sobol attribution [13], and trace the benefit–cost Pareto front by the ε-constraint method [15]. Validated by sign-consistency against curated regulatory edges (8/8). The deliverable is a *ranking* of interventions and a trade-off map — not fold-change predictions, and not a protocol.

**Keywords:** knowledge graphs · network propagation · structural controllability · multi-objective optimization · computational neuroscience

*(Academic-styled HTML version: [deep-dive.html](deep-dive.html))*

## 1. Substrate

Base graph: PrimeKG [1] ($|V|=129{,}375$, $|E|\approx4.05\times10^{6}$, 10 node types, 30 edge types); lineage is the Hetionet / Rephetio hetnet for drug repurposing via metapath scoring [2].

**Brain-scoping.** Retain gene $v$ by tissue-expression enrichment over PrimeKG `anatomy_protein_present` edges $E_a$:

$$e(v)=\frac{\bigl|\{a:(v,a)\in E_a,\ a\in A_{\mathrm{brain}}\}\bigr|}{\bigl|\{a:(v,a)\in E_a\}\bigr|},\qquad \text{keep if } e(v)\ge 0.15 \ \wedge\ \deg_a(v)\ge 5 \tag{1}$$

*In words —* keep a gene only if a meaningful fraction of the tissues it is expressed in are brain tissues, and only if it is expressed in enough places for that fraction to be trustworthy.

Post-prune: $N=280$ (intervention 70, input 15, readout 6, trap 2, expansion 187), $3912$ directed edges, $2871$ signed ($+{:}\,2253,\ -{:}\,618$), one SCC of $200$.

![Figure 1 — knowledge graph slice](assets/graph_bio_graph.png)

![Figure 2 — the 280-node substrate](assets/graph_brain_substrate.png)

## 2. The propagation operator

Signed adjacency $W\in\{-1,0,+1\}^{N\times N}$, oriented so $(Wx)_i$ is influx to $i$: $W_{ij}=\operatorname{sign}(j\to i)$. Out-strength $d^{\mathrm{out}}_j=\sum_i|W_{ij}|$; column-normalize into the Personalized-PageRank transition [3]:

$$\hat{W}=W\,D_{\mathrm{out}}^{-1},\qquad \hat{W}_{ij}=\frac{W_{ij}}{\sum_k|W_{kj}|} \tag{2}$$

*In words —* split each gene's outgoing influence evenly across the targets it regulates, so a hub gene that talks to everyone cannot dominate.

$|\hat{W}|$ is column-stochastic, so by Perron–Frobenius $\rho(\hat{W})\le1$ (measured: $0.544$), guaranteeing §3 converges. Column normalization suits a *directed* graph (promiscuity is an out-degree property); the symmetric GCN form $D^{-1/2}\tilde{W}D^{-1/2}$ [6] is the undirected analogue.

![Figure 3 — MTOR hub](assets/graph_mtor_hub.png)

## 3. Propagation by random-walk-with-restart

Source $p\in\mathbb{R}^N$, restart probability $\alpha$ [5,4]:

$$x^{(t+1)}=(1-\alpha)\,\hat{W}x^{(t)}+\alpha\,p \tag{3}$$

*In words —* at every step, spread the signal one hop, but yank a fixed fraction $\alpha$ back to the gene you started from.

Fixed point solves $(I-(1-\alpha)\hat{W})x^{*}=\alpha p$; since $\rho((1-\alpha)\hat{W})\le1-\alpha<1$ it equals its Neumann series:

$$x^{*}=\alpha\bigl(I-(1-\alpha)\hat{W}\bigr)^{-1}p=\alpha\sum_{k\ge0}(1-\alpha)^{k}\hat{W}^{k}p \tag{4}$$

*In words —* the settled-down response; equivalently, sum the signal over every path length $k$, each discounted by $(1-\alpha)^k$, so distant hops fade exponentially.

Mean radius $\bar k=(1-\alpha)/\alpha\approx5.7$ at $\alpha=0.15$. As $\alpha\to0$, $x^{*}\to$ leading eigenvector of $\hat W$ (over-smoothing), which the decay prevents. The 200-node SCC is why a steady-state resolvent is required.

![Figure 4 — random walk with restart](assets/diagram_rwr.png)

## 4. Controllability

LTI form with input map $B\in\mathbb{R}^{N\times m}$: $\dot{x}=Wx+Bu$. Controllable iff (Kalman [7]):

$$\operatorname{rank}\mathcal{C}=N,\qquad \mathcal{C}=[\,B,\ WB,\ W^{2}B,\ \dots,\ W^{N-1}B\,] \tag{5}$$

*In words —* you can reach any state exactly when your inputs, pushed through successive hops, together span all $N$ dimensions.

Structural controllability (Lin [8]; Liu–Slotine–Barabási [9]): minimum drivers = nodes left unmatched by a maximum matching $M^{*}$:

$$N_{D}=\max\bigl(N-|M^{*}|,\ 1\bigr) \tag{6}$$

*In words —* the fewest genes you must control is the number left over after pairing up the network as efficiently as possible.

Matching via Hopcroft–Karp [10] in $O(|E|\sqrt N)$; $\langle k\rangle\propto1/N_D$. Result: all 280 reachable, full control needs $N_D=81$ (35 druggable) — arbitrary-state control fails, but **target control** [11] of the readout subset needs $\le N_D$ inputs and is feasible.

| quantity | value |
|---|---|
| druggable inputs \|𝒟\| | 172 |
| reachable \|R\|/N | 280 / 280 |
| min drivers N_D (full) | 81 |
| drivers druggable | 35 / 81 |
| feedback SCC | 200 |

## 5. Target state and objective

Target deviation $d\in\mathbb{R}^N$. Most cognitive variables are set-points with an inverted-U (Yerkes–Dodson [18]; Arnsten [19]). Benefit = distance-reduction to the target:

$$b_i=\lvert d_i\rvert-\lvert x^{*}_i-d_i\rvert \tag{7}$$

*In words —* how much closer to the ideal level this gene got: positive for moving toward the target, negative for overshooting.

Aggregate ($w_i$ = confidence, readouts $w_i=0$) and cost ($L_1$ effort + off-target collateral):

$$B(p)=\sum_i w_i\,b_i,\qquad C(p)=\lVert p\rVert_1+\gamma\sum_{j\,\notin\,T}\lvert x^{*}_j\rvert \tag{8}$$

*In words —* total good across genes, against total cost: how hard you pushed plus how much you disturbed things outside the target set.

Curated vector: 94 genes, 43 set-point / 30 up / 12 down.

![Figure 5 — target set](assets/graph_target_set.png)

## 6. Uncertainty quantification

Uncertain inputs $\theta$ (confidence-weight intervals + sign-only magnitudes). Monte-Carlo (GUM-S1 [12]): draw $\theta^{(m)}$, evaluate $Y^{(m)}=B(p;\theta^{(m)})$, report an order-statistic coverage interval:

$$\widehat{\mathrm{CI}}_{90\%}=\bigl[\,Y_{(\lceil0.05M\rceil)},\ Y_{(\lfloor0.95M\rfloor)}\,\bigr] \tag{9}$$

*In words —* run the model many times under the uncertainty, sort the scores, report the middle 90% as an honest range.

Attribute via Sobol indices [13,14]:

$$S_i=\frac{\operatorname{Var}_{\theta_i}\!\bigl(\mathbb{E}[Y\mid\theta_i]\bigr)}{\operatorname{Var}(Y)},\qquad S_{T_i}=\frac{\mathbb{E}\bigl[\operatorname{Var}(Y\mid\theta_{\sim i})\bigr]}{\operatorname{Var}(Y)} \tag{10}$$

*In words —* of all the wobble in the final score, how much is each uncertain input responsible for — telling you which fact to verify first.

## 7. Optimization

Multi-objective (max $B$, min $C$) → Pareto front, traced exactly by ε-constraint [15]:

$$\max_p\ B(p)\quad\text{s.t.}\quad C(p)\le\varepsilon \tag{11}$$

*In words —* get the most benefit while keeping cost under a cap $\varepsilon$, then slide the cap to draw the whole trade-off curve.

Weighted-sum $\max_p B-\lambda C$ is a supporting hyperplane of normal $(1,\lambda)$: recovers only the convex hull, so on a non-convex front it *provably misses* concave regions for every $\lambda$ [16,17]. ε-constraint does not.

## 8. Validation

Test-driven (11 tests): invariants include $\rho(\hat W)\le1$, resolvent (4) = truncated series to $10^{-8}$, sign propagation. Sign check — perturb $+1$, compare $\operatorname{sign}(x^{*})$ to raw edge signs ($\alpha=0.15$, $\rho=0.544$):

| perturb | → target | edge | $x^{*}$ | check |
|---|---|---|---|---|
| `CREB1 ↑` | BDNF | +1 | +0.0030 | ✓ |
| `CREB1 ↑` | JUN | −1 | −0.0027 | ✓ flip |
| `CREB1 ↑` | NTRK2 | +1→+1 | +0.0080 | ✓ net |
| `GSK3B ↑` | CREB1 | −1 | −0.0041 | ✓ inhib |
| `AKT1 ↑` | NFKB1 | +1→−1 | −0.0008 | ✓ net-flip |

Two-hop `NTRK2` ($+0.0080$) exceeds one-hop `BDNF` ($+0.0030$) because $d^{\mathrm{out}}(\text{CREB1})\approx40$ divides its transmission while $d^{\mathrm{out}}(\text{BDNF})=1$ — a direct consequence of (2).

![Figure 6 — telmisartan → PPARG → diabetes](assets/graph_telmisartan_diabetes.png)

## 9. Groundedness and assumptions

Rungs: brain-scoping (computed) > edge sign/direction (curated) > edge magnitude (mostly sign-only) > objective (hand-built $d$). $\hat W$ is the first-order Jacobian at baseline, so $x^{*}$ is valid only for small $\lVert x-x_0\rVert$; large perturbations leave the trust region. Deliverable: an *ordinal* ranking + trade-off map, not fold-change magnitudes, not medical advice.

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
