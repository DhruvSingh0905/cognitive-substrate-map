"""Real quantitative magnitudes, each tagged by its confidence rung (spec §3 honesty rule).

Rungs (high -> low):  literature·in-brain  >  IUPHAR·potency  >  OmniPath·sign-only  >  unknown
LINCS L1000 expression z-scores would slot between potency and sign-only, but its live
APIs are down (SigCom 502) and the bulk signature matrix is a ~50GB GEO download — so it's
flagged, not faked.
"""
import functools
import requests

IUPHAR = "https://www.guidetopharmacology.org/services"

# Gold rung: literature, in-brain, cited. value = measured change in expression.
LITERATURE = {
    ("Carbamazepine", "BDNF"): ("+123%",       "literature·in-brain",    "Chang 2009, rat frontal cortex (PMC2637936)"),
    ("Lamotrigine",   "BDNF"): ("+28%",        "literature·in-brain",    "Chang 2009, rat frontal cortex (PMC2637936)"),
    ("Fluoxetine",    "BDNF"): ("↑ (CREB-dep)", "literature·directional", "hippocampus/PFC, CREB-dependent"),
    ("Ketamine",      "BDNF"): ("↑ (via pCREB)","literature·directional", "PMC11642200"),
}


@functools.lru_cache(maxsize=1024)
def _symbol(target_id: int):
    try:
        d = requests.get(f"{IUPHAR}/targets/{target_id}/geneProteinInformation", timeout=30).json()
        for x in d:
            if x.get("species") == "Human" and x.get("geneSymbol"):
                return x["geneSymbol"]
    except Exception:
        pass
    return None


def iuphar_potency(drug: str) -> dict:
    """{gene: (label, status, source)} of binding potency for a drug, from IUPHAR."""
    try:
        lig = requests.get(f"{IUPHAR}/ligands", params={"name": drug}, timeout=30).json()
        if not lig:
            return {}
        lid = lig[0]["ligandId"]
        inter = requests.get(f"{IUPHAR}/ligands/{lid}/interactions", timeout=30).json()
    except Exception:
        return {}
    out = {}
    for i in inter:
        aff = i.get("affinity")
        sym = _symbol(i.get("targetId"))
        if sym and aff and sym not in out:
            out[sym] = (f"{i.get('affinityType','pKi')} {aff}", "IUPHAR·potency",
                        "guidetopharmacology.org")
    return out


def drug_magnitudes(drugs: list[str]) -> list[dict]:
    """Assemble drug->gene magnitude edges from literature (gold) + IUPHAR (potency)."""
    edges = []
    for d in drugs:
        for (dd, gene), (val, status, src) in LITERATURE.items():
            if dd == d:
                edges.append({"drug": d, "gene": gene, "value": val, "status": status, "source": src})
        for gene, (val, status, src) in iuphar_potency(d).items():
            edges.append({"drug": d, "gene": gene, "value": val, "status": status, "source": src})
    return edges
