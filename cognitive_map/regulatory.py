"""Directed, signed regulatory edges from OmniPath.

Fills the layer PrimeKG lacks: PrimeKG `protein_protein` is *undirected physical* PPI,
so transcriptional/signaling regulation (JUN->target, PRKACA->CREB1, with a sign) is
invisible there. OmniPath integrates signaling (curated) + CollecTRI/DoRothEA TF->target,
each edge directed and signed (activation/inhibition) with provenance.
"""
import io
import numpy as np
import pandas as pd
import requests

API = "https://omnipathdb.org/interactions"
DATASETS = "omnipath,collectri,dorothea"


def _truthy(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin(("true", "1"))


def fetch_regulatory(genes: list[str], timeout: int = 180) -> pd.DataFrame:
    """Directed signed regulatory edges with BOTH endpoints in `genes`.

    Columns: source, target, directed (bool), sign (+1 activation / -1 inhibition /
    0 ambiguous), n_sources (int), sources (str).
    """
    params = {
        "partners": ",".join(sorted(set(genes))),
        "source_target": "AND",          # both endpoints must be in the set
        "genesymbols": "1",
        "datasets": DATASETS,
        "dorothea_levels": "A,B,C",      # higher-confidence TF->target only
        "fields": "sources,references",
    }
    r = requests.get(API, params=params, timeout=timeout)
    r.raise_for_status()
    if r.text.lstrip().startswith("Something is not"):
        raise RuntimeError("OmniPath query error: " + r.text[:200])

    cols = ["source", "target", "directed", "sign", "n_sources", "sources"]
    df = pd.read_csv(io.StringIO(r.text), sep="\t")
    if df.empty:
        return pd.DataFrame(columns=cols)

    stim = _truthy(df.get("consensus_stimulation", df["is_stimulation"]))
    inhib = _truthy(df.get("consensus_inhibition", df["is_inhibition"]))
    sign = np.where(stim & ~inhib, 1, np.where(inhib & ~stim, -1, 0))

    src = df["sources"].fillna("")
    out = pd.DataFrame({
        "source": df["source_genesymbol"],
        "target": df["target_genesymbol"],
        "directed": _truthy(df["is_directed"]),
        "sign": sign,
        "n_sources": src.apply(lambda s: len(s.split(";")) if s else 0),
        "sources": src,
    })
    out = out[out["source"] != out["target"]]            # drop self-loops for the graph
    return out.drop_duplicates(subset=["source", "target"]).reset_index(drop=True)[cols]
