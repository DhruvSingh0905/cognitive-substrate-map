# Cognitive Substrate Map

A brain-scoped, directed, signed regulatory network of cognition — used to ask which gene up/down-regulations move the brain toward a learning-optimal state at minimal systemic cost.

## The math

### 1 · Substrate → signed operator

Each edge carries a direction and a sign ($+1$ activation / $-1$ inhibition), oriented so influence flows *source → target*:

$$W_{ij} = \operatorname{sign}(j \to i)$$

Column-normalize by each regulator's out-strength — the Personalized-PageRank transition. This hub-damps promiscuous regulators and bounds the spectrum, so the propagation below converges:

$$\hat{W}_{ij} = \frac{W_{ij}}{\sum_k \lvert W_{kj} \rvert}, \qquad \rho(\hat{W}) \le 1$$

### 2 · Propagation to steady state (APPNP)

Perturb a gene with source vector $p$ and solve the fixed point that re-injects the source (weight $\alpha$) and diffuses the rest — the steady state under the 200-node feedback loop:

$$x^{*} = \alpha\, p + (1-\alpha)\,\hat{W} x^{*} \quad\Longrightarrow\quad x^{*} = \alpha \bigl(I - (1-\alpha)\hat{W}\bigr)^{-1} p = \alpha \sum_{k \ge 0} (1-\alpha)^{k} \hat{W}^{k} p$$

The $(1-\alpha)^{k}$ decay damps deep hops (the over-smoothing guard); $x^{*}$ is each node's deviation from baseline.

### 3 · Scoring — closeness to the target state *(next)*

Benefit rewards *movement toward* each target $d_i$ (overshoot flips negative — the inverted-U); cost prices intervention effort + systemic collateral:

$$b_i = \lvert d_i \rvert - \lvert x^{*}_i - d_i \rvert, \qquad B(p) = \sum_i w_i\, b_i, \qquad C(p) = \lVert p \rVert_1 + \gamma \sum_{j \in \text{off-target}} \lvert x^{*}_j \rvert$$

### 4 · Uncertainty band *(next)*

Sample the uncertain inputs (confidence weights, sign-only magnitudes) $M$ times → a coverage band, not a point. Sobol indices $S_{T_i}$ say which input drives the band.

### 5 · Optimization *(next)*

Trace the benefit-vs-cost Pareto front by ε-constraint (exact, since the system is small):

$$\max_{p}\; B(p) \quad \text{s.t.} \quad C(p) \le \varepsilon, \qquad \varepsilon\ \text{swept}$$

## Results

### Substrate

280 nodes in four layers — 70 intervention (knobs), 15 input, 6 readout, 2 trap, 187 bounded expansion — wired by 3,912 directed edges, **2,871 signed** (2,253 activating, 618 inhibitory). Fully connected, with a 200-node strongly-connected feedback core.

### Controllability

All 280 nodes are reachable from the druggable set. Arbitrary-state control would need 81 independent drivers (~35 druggable), but **target-control of the cognitive core is plausible** — all the optimizer needs.

### Propagation — verified against the raw edge signs

Perturb one gene $+1$, solve $x^{*}$, check against signs read straight from the edge table (not the model). At $\alpha = 0.15$, $\rho(\hat{W}) = 0.544$:

| perturb | → target | edge sign | observed $x^{*}$ | check |
|---|---|---|---|---|
| `CREB1 ↑` | BDNF | +1 | +0.0030 | ✓ |
| `CREB1 ↑` | EGR1 | +1 | +0.0030 | ✓ |
| `CREB1 ↑` | TH | +1 | +0.0035 | ✓ |
| `CREB1 ↑` | JUN | −1 | −0.0027 | ✓ flip |
| `CREB1 ↑` | NTRK2 | +1→+1 | +0.0080 | ✓ net |
| `GSK3B ↑` | CREB1 | −1 | −0.0041 | ✓ inhibition |
| `AKT1 ↑` | CHUK | +1 | +0.0046 | ✓ |
| `AKT1 ↑` | NFKB1 | +1→−1 | −0.0008 | ✓ net-flip |

**Hub-damping, visible.** Two-hop `NTRK2` moved *more* than one-hop `BDNF`: `CREB1` has ~40 out-edges so its influence is divided ~40× per target, while `BDNF` has one out-edge and transmits cleanly. A promiscuous regulator can't dominate the network; a specific one passes its signal — for free from the operator.
