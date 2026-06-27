"""
Rephetio rebuild — DWPC features + logistic regression, ranking T2D repurposing candidates.

DWPC (degree-weighted path count) via the matrix shortcut:
  for each metaedge, weight adjacency A so edge (u,v) -> A_uv / (deg_u^w * deg_v^w),
  i.e.  W = D_row^-w · A · D_col^-w   (w = 0.4, Rephetio's damping).
  DWPC along a metapath = product of the W matrices; the disease column = score per drug.
"""
import numpy as np
from scipy import sparse
from neo4j import GraphDatabase
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.metrics import roc_auc_score

W = 0.4
DISEASE = "type 2 diabetes mellitus"
URI, AUTH = "bolt://localhost:7687", ("neo4j", "primekg123")

drv = GraphDatabase.driver(URI, auth=AUTH)
def pull(c):
    with drv.session() as s:
        return [r.data() for r in s.run(c)]

print("pulling edges …", flush=True)
tgt = pull("MATCH (d:drug)-[r:drug_protein {display_relation:'target'}]-(g:gene_protein) RETURN d.node_name AS d, g.node_name AS g")
dpr = pull("MATCH (g:gene_protein)-[:disease_protein]-(x:disease) RETURN g.node_name AS g, x.node_name AS x")
ind = pull("MATCH (d:drug)-[:indication]-(x:disease) RETURN d.node_name AS d, x.node_name AS x")
ppi = pull("MATCH (a:gene_protein)-[:protein_protein]-(b:gene_protein) RETURN a.node_name AS a, b.node_name AS b")
drv.close()

# node index spaces
drugs = sorted({e['d'] for e in tgt} | {e['d'] for e in ind})
genes = sorted({e['g'] for e in tgt} | {e['g'] for e in dpr} | {e['a'] for e in ppi} | {e['b'] for e in ppi})
dises = sorted({e['x'] for e in dpr} | {e['x'] for e in ind})
di = {x: i for i, x in enumerate(drugs)}
gi = {x: i for i, x in enumerate(genes)}
si = {x: i for i, x in enumerate(dises)}

def mat(edges, kr, kc, ri, ci):
    rc = [(ri[e[kr]], ci[e[kc]]) for e in edges if e[kr] in ri and e[kc] in ci]
    r, c = zip(*rc)
    A = sparse.csr_matrix((np.ones(len(r)), (r, c)), shape=(len(ri), len(ci)))
    A.data[:] = 1.0
    return A

A_dg = mat(tgt, 'd', 'g', di, gi)                       # drug × gene  (target)
A_gD = mat(dpr, 'g', 'x', gi, si)                       # gene × disease (assoc)
A_dD = mat(ind, 'd', 'x', di, si)                       # drug × disease (indication)
ppis = ppi + [{'a': e['b'], 'b': e['a']} for e in ppi]  # symmetrize
A_gg = mat(ppis, 'a', 'b', gi, gi)                      # gene × gene  (PPI)

def dweight(A):
    r = np.asarray(A.sum(1)).ravel(); c = np.asarray(A.sum(0)).ravel()
    rw = np.where(r > 0, r ** -W, 0.0); cw = np.where(c > 0, c ** -W, 0.0)
    return sparse.diags(rw) @ A @ sparse.diags(cw)

W_dg, W_gD, W_dD, W_gg = map(dweight, (A_dg, A_gD, A_dD, A_gg))
t = si[DISEASE]

# DWPC vectors over drugs -> T2D, one per metapath
dwpc1 = np.asarray((W_dg @ W_gD[:, t]).todense()).ravel()                 # C-target-G-assoc-D
dwpc2 = np.asarray((W_dg @ (W_dg.T @ W_dD[:, t])).todense()).ravel()      # C-target-G-target-C-indic-D
dwpc3 = np.asarray((W_dg @ (W_gg @ W_gD[:, t])).todense()).ravel()        # C-target-G-PPI-G-assoc-D
MP = ["targets-T2D-gene", "shares-target-with-Tx", "target-PPI-to-T2D-gene"]

X = np.log1p(np.vstack([dwpc1, dwpc2, dwpc3]).T)
X = (X - X.mean(0)) / (X.std(0) + 1e-9)

pos = {e['d'] for e in ind if e['x'] == DISEASE}
y = np.array([1 if d in pos else 0 for d in drugs])

clf = LogisticRegression(class_weight='balanced', max_iter=2000)
cv = StratifiedKFold(5, shuffle=True, random_state=0)
proba = cross_val_predict(clf, X, y, cv=cv, method='predict_proba')[:, 1]
clf.fit(X, y)

print(f"\n=== model on {DISEASE} ===")
print(f"positives: {y.sum()}   drugs scored: {len(drugs)}")
print(f"cross-validated AUROC: {roc_auc_score(y, proba):.3f}  (how well metapaths recover known Tx)")
print("learned metapath weights (which signal mattered):")
for name, w in sorted(zip(MP, clf.coef_[0]), key=lambda z: -z[1]):
    print(f"   {w:+.2f}  {name}")

order = np.argsort(-proba)
print("\n=== TOP 20 repurposing candidates (known indications removed) ===")
rank = 0
for i in order:
    if drugs[i] in pos:
        continue
    rank += 1
    print(f"  {rank:2}. {drugs[i]:34} score={proba[i]:.3f}")
    if rank >= 20:
        break

for probe in ["Metformin", "Telmisartan", "Pioglitazone"]:
    if probe in di:
        r = 1 + int(np.sum(proba > proba[di[probe]]))
        tag = "(known +)" if probe in pos else "(candidate)"
        print(f"\n  {probe}: score={proba[di[probe]]:.3f}, overall rank {r}/{len(drugs)} {tag}")
