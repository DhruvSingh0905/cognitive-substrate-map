"""Curated brain-cognition seed genes + cascade triage (spec §2, §4)."""

NEUROTRANSMITTER = {
    "cholinergic":   ["CHRNA7", "CHRNA4", "CHRNB2", "ACHE", "CHAT", "SLC18A3"],
    "glutamatergic": ["GRIN1", "GRIN2A", "GRIN2B", "GRIA1", "GRIA2", "GRM5", "GRM2"],
    "dopaminergic":  ["DRD1", "DRD2", "DRD3", "DRD4", "DRD5", "COMT", "TH", "SLC6A3", "DDC"],
    "serotonergic":  ["HTR1A", "HTR2A", "SLC6A4", "TPH2"],
    "gabaergic":     ["GABRA1", "GABRB2", "GAD1", "GAD2", "SLC6A1"],
}
PLASTICITY_CASCADES = {
    "camp_pka_creb":   ["ADCY1", "PRKACA", "CREB1", "CREBBP"],
    "immediate_early": ["FOS", "FOSB", "FOSL1", "FOSL2", "JUN", "JUNB", "JUND",
                        "EGR1", "ARC", "NR4A1", "BDNF"],  # full AP-1 family
    "rho_ras_gtpase":  ["RHOA", "RAC1", "CDC42", "HRAS", "RASGRF1", "KALRN"],
    "core_plasticity": ["NTRK2", "MTOR", "CAMK2A", "CAMK2B"],
}
NEUROINFLAMMATION = ["TREM2", "IL1B", "TNF", "NLRP3", "CX3CR1",
                     "NFKB1", "NFKB2", "RELA", "RELB", "REL"]  # full NF-kB family
CLEARANCE         = ["AQP4", "SQSTM1", "BECN1"]
METABOLIC         = ["PRKAA1", "PRKAA2", "PRKAB1", "PRKAG1"]

# BBB / systemic interface — how body-wide state (glucose, arousal, stress, hormones)
# drives the brain core. Modeled as DRIVERS, not clean knobs (systemic, high-pleiotropy).
SYSTEMIC_INPUT = {
    "fuel_transport":    ["SLC2A1", "SLC7A5"],              # GLUT1, LAT1
    "metabolic_hormone": ["INSR", "LEPR", "THRA", "THRB"],  # insulin/leptin/thyroid receptors
    "catecholamine":     ["ADRB1", "ADRB2", "ADRA2A"],      # epi/norepi
    "steroid":           ["AR", "ESR1", "ESR2", "NR3C1"],   # testosterone/estrogen/cortisol
    "adenosine":         ["ADORA1", "ADORA2A"],             # caffeine axis (A1 + A2A)
}

# Out of intervention scope — load-bearing/oncogenic if perturbed in the adult brain.
DEVELOPMENTAL_TRAP = ["NOTCH1", "NOTCH2", "CTNNB1", "WNT3A", "SHH", "GLI1", "HES1", "DLL1"]
# Disease-cascade reference / readouts, not knobs.
DISEASE_READOUT    = ["APP", "PSEN1", "PSEN2", "MAPT", "MECP2", "APOE"]


def intervention_seeds() -> set[str]:
    genes: set[str] = set()
    for group in (NEUROTRANSMITTER, PLASTICITY_CASCADES):
        for names in group.values():
            genes.update(names)
    genes.update(NEUROINFLAMMATION, CLEARANCE, METABOLIC)
    return genes


def input_seeds() -> set[str]:
    genes: set[str] = set()
    for names in SYSTEMIC_INPUT.values():
        genes.update(names)
    return genes


def classify(gene: str) -> str:
    if gene in DEVELOPMENTAL_TRAP:
        return "trap"
    if gene in DISEASE_READOUT:
        return "readout"
    if gene in input_seeds():
        return "input"
    if gene in intervention_seeds():
        return "intervention"
    return "expanded"
