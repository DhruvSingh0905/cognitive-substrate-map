"""Phase 1 tests — assert against values validated 2026-06-27. Needs Neo4j running."""
import pytest
from cognitive_map.db import Graph
from cognitive_map.seeds import intervention_seeds, classify
from cognitive_map.brain_enrichment import is_brain_anatomy, brain_enrichment
from cognitive_map.node_attributes import node_attributes
from cognitive_map.expand import expand
from cognitive_map.build import build_substrate


@pytest.fixture(scope="module")
def g():
    graph = Graph()
    yield graph
    graph.close()


def test_db_connects(g):
    assert g.query("MATCH (n) RETURN count(n) AS n")[0]["n"] > 100_000


def test_seed_membership_and_classification():
    s = intervention_seeds()
    for gene in ["GRIN2B", "BDNF", "DRD2", "CREB1", "ARC", "PRKAA1"]:
        assert gene in s
    assert classify("NOTCH1") == "trap"
    assert classify("MECP2") == "readout"
    assert classify("GRIN2B") == "intervention"
    assert classify("ZZZ_UNKNOWN") == "expanded"


def test_anatomy_matcher():
    assert is_brain_anatomy("cerebral cortex")
    assert is_brain_anatomy("hippocampus")
    assert not is_brain_anatomy("liver")


def test_brain_enrichment_separates_brain_from_systemic(g):
    e = brain_enrichment(g, ["GRIN2B", "BDNF", "AGTR1", "INS"])
    assert e["GRIN2B"] > 0.40
    assert e["AGTR1"] < 0.15
    assert e["GRIN2B"] > e["BDNF"] > e["AGTR1"]
    assert e["INS"] == 0.0


def test_node_attributes_for_bdnf(g):
    a = node_attributes(g, ["BDNF"])["BDNF"]
    assert a["n_diseases"] > 0
    assert isinstance(a["pathways"], list)
    assert a["promiscuity"] >= 0


def test_expansion_filters_hubs_and_excludes_seeds(g):
    neighbors = expand(g, ["BDNF"], cutoff=100)
    assert "BDNF" not in neighbors
    assert "ALB" not in neighbors
    assert "ABCB1" not in neighbors
    assert len(neighbors) > 0


def test_build_produces_scoped_table(g):
    df = build_substrate(g)
    assert (df["gene"] == "GRIN2B").any()
    for col in ["gene", "klass", "brain_enrichment", "n_diseases",
                "promiscuity", "direction", "tradeoff", "evidence_grade"]:
        assert col in df.columns
    grin = df.loc[df["gene"] == "GRIN2B", "brain_enrichment"].iloc[0]
    assert grin > df["brain_enrichment"].median()
    assert df["direction"].isna().all()
    assert df["tradeoff"].isna().all()
