"""Target-state vector — the learning/encoding-optimal brain state.

Synthesized from 5 parallel literature-research agents (2026-06-27). Each row is a
DECISION to hand-verify: direction (up/down/setpoint), shape (monotone/inverted_U/
uncertain), role (knob = actionable target · readout = gauge, NOT a knob · input =
systemic driver, high-pleiotropy), confidence, and a one-line mechanism.

HARD FINDINGS from the research (read before trusting any row):
  1. SETPOINTS DOMINATE. Almost nothing is monotone "up." Neuromodulators, E/I balance,
     cortisol, AMPK, mTOR are inverted-U — "more" is wrong.
  2. KNOB vs READOUT. The immediate-early / AP-1 genes (FOS/FOSB/FOSL1/2/JUN/JUNB/JUND)
     are ACTIVITY MARKERS, not levers. So are the disease genes (APP/PSEN/MAPT/MECP2/APOE).
     Tuning a readout is as useless as tuning a hub. ARC/EGR1/NR4A1 are the effector-IEGs
     that DO drive consolidation.
  3. RATIO TERMS. Some targets are ratios, not per-node values: GluN2A/2B, GluA1/2,
     GABA supply/reuptake, D1/D2, GR/MR. The sim needs these as joint constraints.
  4. CROSS-AGENT AGREEMENT: mTOR came back setpoint/inverted-U from TWO independent agents
     (plasticity + inflammation). AMPK↔mTOR is the metabolic balance node.
  5. CEILINGS: every glutamatergic "up" is hard-capped by the excitotoxicity ceiling.
  6. UNWIRED: CHRNB2, DRD5, GRM2 are in-target but were pruned (no OmniPath edges) —
     researched here, flagged, not yet controllable.

Citations live in the 5 agent evidence reports; PMIDs are literature-grounded but need a
verify-pass (agents cite from knowledge, not a live PubMed query). Directions are CNS
setpoints for a modeled awake-encoding window — NOT medical advice, dosing, or actuators.
"""

# (gene, system, role, direction, shape, confidence, note)
TARGET_STATE = [
    # ---- PLASTICITY CASCADE — the transcription/translation spine (mostly KNOBS) ----
    ("ADCY1",  "plasticity", "knob",    "up",       "inverted_U", "high",   "Ca/CaM coincidence cAMP source for L-LTP; top of cAMP->PKA->CREB"),
    ("PRKACA", "plasticity", "knob",    "up",       "inverted_U", "high",   "PKA phosphorylates CREB-S133; gates early->late LTP"),
    ("CREB1",  "plasticity", "knob",    "up",       "inverted_U", "high",   "master activity TF; sets engram-allocation threshold; the convergence hub"),
    ("CREBBP", "plasticity", "knob",    "up",       "monotone",   "high",   "CBP HAT coactivator; chromatin-permissive for memory genes (HDACi target)"),
    ("BDNF",   "plasticity", "knob",    "up",       "inverted_U", "high",   "CREB target+activator; L-LTP; ceiling = hyperexcitability (Val66Met)"),
    ("NTRK2",  "plasticity", "knob",    "up",       "inverted_U", "high",   "TrkB fans BDNF into ERK/PI3K-mTOR/PLCg; ceiling = epileptogenic"),
    ("EGR1",   "plasticity", "knob",    "up",       "inverted_U", "high",   "Zif268 driver of late-LTP + reconsolidation (genuine driver, not tag)"),
    ("ARC",    "plasticity", "knob",    "up",       "inverted_U", "high",   "effector-IEG; AMPAR endocytosis + spine actin; bidirectional (excess=LTD-like)"),
    ("NR4A1",  "plasticity", "knob",    "up",       "inverted_U", "medium", "CREB/CBP-dependent consolidation; weaker than NR4A2"),
    ("CAMK2A", "plasticity", "knob",    "up",       "inverted_U", "high",   "T286 bistable LTP switch; GluN2B anchoring + GluA1; balanced vs PP1"),
    ("CAMK2B", "plasticity", "knob",    "up",       "inverted_U", "medium", "F-actin bundling/spine targeting of the holoenzyme; regulatory"),
    ("MTOR",   "plasticity", "knob",    "setpoint", "inverted_U", "high",   "translation for L-LTP vs autophagy/proteostasis suppression (2-agent agree)"),
    ("RAC1",   "plasticity", "knob",    "up",       "inverted_U", "high",   "CaMKII->kalirin/Tiam1->Rac1->actin; spine growth; antagonizes RhoA"),
    ("CDC42",  "plasticity", "knob",    "up",       "inverted_U", "high",   "spine-specific new-spine formation via N-WASP/Arp2/3"),
    ("HRAS",   "plasticity", "knob",    "up",       "inverted_U", "medium", "Ras->Raf->ERK->CREB/Egr1/Arc; SynGAP is the brake (inverted-U)"),
    ("RHOA",   "plasticity", "knob",    "setpoint", "inverted_U", "medium", "RhoA/ROCK constrains spines; balance vs Rac1/Cdc42, NOT 'up'"),
    ("KALRN",  "plasticity", "knob",    "up",       "inverted_U", "medium", "Rac1-GEF (kalirin-7); spine growth; necessity cortical>hippocampal (flag)"),
    ("RASGRF1","plasticity", "knob",    "uncertain","uncertain",  "low",    "NR2B->ERK(LTP) vs NR2A->p38(LTD); memory role amygdala-specific — genuinely uncertain"),
    # immediate-early / AP-1 — READOUTS, not knobs
    ("FOS",    "plasticity", "readout", "marker",   "n/a",        "medium", "activity tag / AP-1; used as engram marker — a GAUGE not a lever"),
    ("FOSB",   "plasticity", "readout", "marker",   "n/a",        "low",    "acute IEG; dFosB is a CHRONIC-adaptation accumulator (addiction), not encoding"),
    ("FOSL1",  "plasticity", "readout", "marker",   "n/a",        "low",    "Fos-family AP-1; no established hippocampal-encoding role"),
    ("FOSL2",  "plasticity", "readout", "marker",   "n/a",        "low",    "Fos-family AP-1; activity-correlate, not a driver"),
    ("JUN",    "plasticity", "readout", "marker",   "n/a",        "medium", "c-Jun AP-1 partner; also JNK stress/apoptosis axis; mostly a tag"),
    ("JUNB",   "plasticity", "readout", "marker",   "n/a",        "low",    "often ANTAGONIZES c-Jun targets; ambiguous polarity"),
    ("JUND",   "plasticity", "readout", "marker",   "n/a",        "low",    "constitutive AP-1 buffer/counterweight; not activity-instructive"),

    # ---- FAST NEUROTRANSMISSION — encoding gate + LTP induction ----
    ("CHRNA7", "cholinergic","knob",    "up",       "inverted_U", "medium", "a7 Ca2+ gates LTP ~100ms pre-input; couples ACh->glutamate encoding"),
    ("CHRNA4", "cholinergic","knob",    "up",       "inverted_U", "medium", "a4b2 attentional gain; upstream filter (obligate w/ CHRNB2)"),
    ("CHRNB2", "cholinergic","knob",    "up",       "inverted_U", "medium", "obligate a4 partner; UNWIRED (no OmniPath edge)"),
    ("ACHE",   "cholinergic","knob",    "down",     "inverted_U", "medium", "modest reduction prolongs ACh tone (AChEi mechanism); over-suppress=desensitize"),
    ("CHAT",   "cholinergic","knob",    "up",       "inverted_U", "medium", "rate-limiting ACh synthesis; the ACh budget ceiling"),
    ("SLC18A3","cholinergic","knob",    "up",       "inverted_U", "medium", "VAChT vesicular loading; even modest loss impairs recognition"),
    ("GRIN1",  "glutamate",  "knob",    "up",       "inverted_U", "high",   "obligate NMDAR subunit; coincidence detector; HARD excitotoxicity ceiling"),
    ("GRIN2A", "glutamate",  "knob",    "setpoint", "inverted_U", "medium", "fast kinetics; the GluN2A/2B RATIO is the setpoint"),
    ("GRIN2B", "glutamate",  "knob",    "up",       "inverted_U", "high",   "long coincidence window (Doogie); sharpest excitotoxic ceiling"),
    ("GRIA1",  "glutamate",  "knob",    "up",       "inverted_U", "high",   "GluA1 AMPAR insertion = expression arm of LTP"),
    ("GRIA2",  "glutamate",  "knob",    "setpoint", "inverted_U", "high",   "edited GluA2 = Ca2+-impermeable safety; the plasticity/excitotox gate"),
    ("GRM5",   "glutamate",  "knob",    "up",       "inverted_U", "high",   "mGluR5 potentiates NMDA via Homer-Shank; bidirectional (LTP+LTD)"),
    ("GRM2",   "glutamate",  "knob",    "uncertain","inverted_U", "low",    "mGluR2 autoreceptor: protects ceiling OR starves induction; UNWIRED"),
    ("GABRA1", "gaba",       "knob",    "setpoint", "inverted_U", "medium", "E/I balance; builds gamma rhythms; too much blocks LTP induction"),
    ("GABRB2", "gaba",       "knob",    "setpoint", "inverted_U", "low",    "common GABA_A subunit; same E/I setpoint; thin specific evidence"),
    ("GAD1",   "gaba",       "knob",    "setpoint", "inverted_U", "medium", "GAD67 baseline GABA supply; the E/I floor (KO neonatal-lethal, inferred)"),
    ("GAD2",   "gaba",       "knob",    "setpoint", "inverted_U", "medium", "GAD65 phasic/demand GABA; tunes inhibition during encoding"),
    ("SLC6A1", "gaba",       "knob",    "setpoint", "inverted_U", "medium", "GAT-1 reuptake; inverse lever on GABA tone (E/I setpoint)"),

    # ---- NEUROMODULATORS — the inverted-U setpoints (Arnsten/Yerkes-Dodson) ----
    ("DRD1",   "dopamine",   "knob",    "setpoint", "inverted_U", "high",   "PFC D1 tunes WM delay-firing; both too-low/high collapse it (core inverted-U)"),
    ("DRD2",   "dopamine",   "knob",    "setpoint", "inverted_U", "medium", "striatal gating/updating; D1/D2 = stability-vs-flexibility axis"),
    ("DRD3",   "dopamine",   "knob",    "setpoint", "uncertain",  "low",    "limbic motivation/salience; weak direct WM evidence"),
    ("DRD4",   "dopamine",   "knob",    "setpoint", "inverted_U", "low",    "cortical D4 attention (7R variant); part of PFC DA ensemble"),
    ("DRD5",   "dopamine",   "knob",    "setpoint", "inverted_U", "low",    "D1-class hippocampal LTP gating; UNWIRED (no OmniPath edge)"),
    ("COMT",   "dopamine",   "knob",    "setpoint", "inverted_U", "high",   "sets PFC DA tone (warrior/worrier); WHERE you sit on the D1 curve — person-dependent"),
    ("TH",     "dopamine",   "knob",    "setpoint", "inverted_U", "high",   "rate-limiting for DA AND NE; global gain, not a directional lever"),
    ("SLC6A3", "dopamine",   "knob",    "setpoint", "inverted_U", "high",   "DAT striatal clearance (COMT's cortical counterpart)"),
    ("DDC",    "dopamine",   "knob",    "setpoint", "monotone",   "medium", "shared DA+5HT synthesis; permissive bottleneck, not a tuning lever"),
    ("HTR1A",  "serotonin",  "knob",    "setpoint", "inverted_U", "medium", "5-HT1A auto+heteroreceptor; calm-vs-alert gain"),
    ("HTR2A",  "serotonin",  "knob",    "setpoint", "inverted_U", "medium", "cortical excitability/gain; opposes 5-HT1A"),
    ("SLC6A4", "serotonin",  "knob",    "setpoint", "inverted_U", "medium", "SERT sets 5-HT tone (5-HTTLPR); couples to stress reactivity"),
    ("TPH2",   "serotonin",  "knob",    "setpoint", "inverted_U", "medium", "rate-limiting brain 5-HT synthesis; global 5-HT gain"),
    ("ADRB1",  "noradren",   "knob",    "setpoint", "inverted_U", "medium", "b1 arousal + amygdala emotional-memory (Yerkes-Dodson)"),
    ("ADRB2",  "noradren",   "knob",    "setpoint", "inverted_U", "medium", "b2 hippocampal plasticity + emotional memory (propranolol blocks)"),
    ("ADRA2A", "noradren",   "knob",    "setpoint", "inverted_U", "high",   "PFC a2A closes HCN -> strengthens WM at MODERATE NE (guanfacine); high NE impairs"),
    ("ADORA1", "adenosine",  "input",   "down",     "monotone",   "high",   "A1 sleep pressure; brakes ACh/excitatory tone; caffeine target (bounded)"),
    ("ADORA2A","adenosine",  "input",   "down",     "monotone",   "high",   "A2A-D2 heteromer brakes dopamine; caffeine target; pro-arousal when blocked"),

    # ---- NEUROINFLAMMATION — brakes on plasticity (mostly DOWN, family is not one axis) ----
    ("IL1B",   "inflammation","knob",   "down",     "inverted_U", "high",   "high IL-1b impairs NMDAR-LTP+BDNF; low tonic REQUIRED for LTP (not zero)"),
    ("TNF",    "inflammation","knob",   "down",     "inverted_U", "high",   "chronic TNF suppresses LTP; constitutive needed for synaptic scaling"),
    ("NLRP3",  "inflammation","knob",   "down",     "monotone",   "high",   "inflammasome->IL-1b; the metabolism->inflammation bridge (AMPK suppresses it)"),
    ("NFKB1",  "inflammation","knob",   "down",     "inverted_U", "medium", "p50: glial=inflammatory(down) BUT neuronal NF-kB needed for CREB-LTP"),
    ("NFKB2",  "inflammation","knob",   "down",     "monotone",   "low",    "non-canonical chronic glial inflammation (w/ RELB)"),
    ("RELA",   "inflammation","knob",   "down",     "inverted_U", "medium", "p65 master transactivator of IL1B/TNF; glial pool = main brake on LTP/BDNF"),
    ("RELB",   "inflammation","knob",   "down",     "monotone",   "low",    "non-canonical chronic inflammation partner of p52"),
    ("REL",    "inflammation","knob",   "setpoint", "inverted_U", "low",    "c-Rel is NEUROPROTECTIVE/survival — do NOT lump with RELA"),
    ("CX3CR1", "inflammation","knob",   "setpoint", "inverted_U", "medium", "neuron->microglia calming; needed for pruning+LTP; bidirectional"),
    ("TREM2",  "inflammation","knob",   "setpoint", "inverted_U", "medium", "microglial clearance (protective) vs chronic DAM (toxic); do NOT flatten to down"),
    ("AQP4",   "clearance",  "knob",    "setpoint", "inverted_U", "high",   "glymphatic clearance; POLARIZATION not bulk; sleep-dominant (trades off w/ encoding)"),
    ("SQSTM1", "clearance",  "knob",    "setpoint", "inverted_U", "medium", "p62 autophagy adaptor; buildup activates NF-kB; low steady-state = healthy flux"),
    ("BECN1",  "clearance",  "knob",    "setpoint", "inverted_U", "medium", "autophagy nucleation; excess dismantles spines/AMPARs (vs mTOR)"),
    ("PRKAA1", "metabolic",  "knob",    "setpoint", "inverted_U", "medium", "AMPKa1; energy+autophagy; chronic-high suppresses mTOR translation"),
    ("PRKAA2", "metabolic",  "knob",    "setpoint", "inverted_U", "high",   "AMPKa2 REQUIRED for LTP but over-activation blocks consolidation — sharpest inverted-U"),
    ("PRKAB1", "metabolic",  "knob",    "setpoint", "inverted_U", "low",    "AMPK b-subunit scaffold; tunes assembly"),
    ("PRKAG1", "metabolic",  "knob",    "setpoint", "inverted_U", "low",    "AMPK g AMP-sensor; sets the energy-charge threshold"),

    # ---- SYSTEMIC INPUTS — BBB/hormone drivers (high-pleiotropy, setpoints) ----
    ("SLC2A1", "input",      "input",   "up",       "monotone",   "high",   "GLUT1 BBB glucose; gates fuel for the ENTIRE cascade"),
    ("SLC7A5", "input",      "input",   "setpoint", "inverted_U", "medium", "LAT1 imports monoamine precursors + T3/T4; competitive balance, feeds mTOR"),
    ("INSR",   "input",      "input",   "up",       "inverted_U", "medium", "brain insulin->PI3K/AKT->mTOR; AKT-|GSK3b lowers tau; IDE ties Ab clearance"),
    ("LEPR",   "input",      "input",   "up",       "inverted_U", "medium", "leptin facilitates NMDA-LTP via JAK2/STAT3+PI3K (shared w/ INSR)"),
    ("THRA",   "input",      "input",   "setpoint", "inverted_U", "high",   "brain-dominant TRa; T3 programs BDNF/neurogenesis; euthyroid setpoint"),
    ("THRB",   "input",      "input",   "setpoint", "inverted_U", "medium", "TRb; less CNS-neuron-dominant than TRa; pituitary TSH feedback"),
    ("AR",     "input",      "input",   "up",       "inverted_U", "low",    "androgens raise CA1 spines (partly via aromatization->estradiol); sex/context-dependent"),
    ("ESR1",   "input",      "input",   "up",       "inverted_U", "medium", "estradiol/ERa raises spines + NMDA + CREB->BDNF; critical-window; cortisol blunts"),
    ("ESR2",   "input",      "input",   "up",       "inverted_U", "low",    "ERb plasticity/memory; weaker human validation"),
    ("NR3C1",  "input",      "input",   "setpoint", "inverted_U", "high",   "cortisol GR/MR: acute-moderate aids, chronic-high ->|BDNF, atrophy, insulin resist, tau"),

    # ---- DISEASE READOUTS — gauges, NOT knobs ----
    ("APP",    "readout",    "readout", "down",     "monotone",   "high",   "amyloidogenic Ab42 impairs synapses; healthy = low; IDE competes w/ insulin"),
    ("PSEN1",  "readout",    "readout", "setpoint", "monotone",   "high",   "g-secretase core; FAD mutation raises Ab42:40; a gauge not a knob"),
    ("PSEN2",  "readout",    "readout", "setpoint", "monotone",   "high",   "alt g-secretase; rarer lower-penetrance FAD"),
    ("MAPT",   "readout",    "readout", "down",     "monotone",   "high",   "phospho-tau tangles track decline; GSK3b(insulin)+cortisol raise tau-P"),
    ("MECP2",  "readout",    "readout", "setpoint", "inverted_U", "high",   "dosage-sensitive (Rett/duplication both severe); regulates BDNF; dev gauge"),
    ("APOE",   "readout",    "readout", "setpoint", "non_monotone","high",  "e4 ->|Ab clearance +inflammation +tau; e2 protective; fixed genotype gauge"),
]

ROLES = ("knob", "input", "readout")
DIRECTIONS = ("up", "down", "setpoint", "uncertain", "marker")
SHAPES = ("monotone", "inverted_U", "uncertain", "n/a", "non_monotone")

# Ratio-terms the sim must specify JOINTLY (not per-node):
RATIO_TERMS = {
    "GluN2A/2B": ("GRIN2A", "GRIN2B", "coincidence-window kinetics"),
    "GluA1/2":   ("GRIA1", "GRIA2", "drive vs Ca2+-safety"),
    "GABA_supply/reuptake": ("GAD1", "SLC6A1", "E/I tone"),
    "D1/D2":     ("DRD1", "DRD2", "stability vs flexibility"),
    "GR/MR":     ("NR3C1", None, "cortisol acute-vs-chronic dial"),
}

UNWIRED = ["CHRNB2", "DRD5", "GRM2"]  # in-target, pruned (no OmniPath edges), not yet controllable


def to_dataframe():
    import pandas as pd
    return pd.DataFrame(TARGET_STATE, columns=[
        "gene", "system", "role", "direction", "shape", "confidence", "note"])
