import copy
import math
import pytest
from coursepilot.catalogue import load_catalogue, eligibility
from coursepilot.engine import Recommender, Profile
from coursepilot.text import tokenize

@pytest.fixture(scope="module")
def engine():
    return Recommender()

def complete(engine):
    return [c["code"] for c in engine.courses if c["category"] != "elective"]

def test_source_data_contract():
    data = load_catalogue()
    assert 60 <= len(data["courses"]) <= 80
    assert data["source_sha256"] and all(c["source_page"] > 0 for c in data["courses"])
    assert all(c["credits"] is None or c["credits"] > 0 for c in data["courses"])

def test_preprocessing():
    assert tokenize("The algorithms and matrices in NLP") == ["algorithm", "matrix", "natural", "language", "processing"]

@pytest.mark.parametrize("method",["tfidf","hybrid","keyword","random"])
def test_constraints_apply_to_every_ranker(engine, method):
    p = Profile("data databases neural learning", {"databases":3,"deep learning":3}, [])
    r = engine.recommend(p,20,method)
    codes = {c["code"] for c in r["recommendations"]}
    assert "CS4087" not in codes  # Both database theory and lab are required.
    assert "CS4045" not in codes
    assert all(eligibility(c, set())[0] for c in r["recommendations"])

def test_lab_is_not_implicitly_waived(engine):
    c = engine.by_code["CS4087"]
    assert not eligibility(c,{"CS2005"})[0]
    assert eligibility(c,{"CS2005","CL2005"})[0]

def test_or_alternatives_and_unknown():
    course = {"code":"X", "category":"elective", "prerequisite_status":"catalogue", "prerequisite_groups":[["A","B"],["C"]]}
    assert eligibility(course,{"B","C"})[0]
    assert not eligibility(course,{"B"})[0]
    assert not eligibility({**course,"prerequisite_status":"unknown"},{"B","C"})[0]

def test_completed_courses_never_return(engine):
    p = Profile("recommendation personalized filtering", {}, complete(engine)+["CS4053"])
    assert "CS4053" not in [c["code"] for c in engine.recommend(p)["recommendations"]]

@pytest.mark.parametrize("method",["tfidf","hybrid"])
def test_explanations_reconstruct_score(engine,method):
    p = Profile("recommendation personalized filtering", {"recommender systems":5,"machine learning":1}, complete(engine))
    result = engine.recommend(p,10,method)
    assert result["recommendations"]
    for c in result["recommendations"]:
        assert 0 <= c["score"] <= 1
        assert sum(t["cosine_contribution"] for t in c["term_contributions"]) == pytest.approx(c["tfidf_similarity"])
        assert sum(c["components"].values()) == pytest.approx(c["score"])
        assert sum(t["score_contribution"] for t in c["term_contributions"]) == pytest.approx(c["components"]["tfidf"])

def test_no_evidence_abstains(engine):
    for query in ["", "the and or", "zzzzqxyw"]:
        assert engine.recommend(Profile(query),5)["recommendations"] == []

def test_all_completed_returns_empty(engine):
    assert not engine.recommend(Profile("machine learning",{},list(engine.by_code)))["recommendations"]

def test_seed_determinism(engine):
    p=Profile("",{},complete(engine))
    a=engine.recommend(p,10,"random",seed=7)
    b=engine.recommend(p,10,"random",seed=7)
    assert a["recommendations"] == b["recommendations"]

@pytest.mark.parametrize("profile",[
    Profile("x",{},["FAKE1000"]), Profile("x",{"unknown":2}),
    Profile("x",{"machine learning":float("nan")}),
    Profile("x",{"machine learning":0}), Profile("x",{},["CS1002","CS1002"]),
])
def test_invalid_profiles_fail(engine,profile):
    with pytest.raises(ValueError): engine.recommend(profile)

def test_weight_changes_ranking(engine):
    p=Profile("",{"machine learning":5,"cybersecurity":1},complete(engine))
    q=Profile("",{"machine learning":1,"cybersecurity":5},complete(engine))
    assert engine.recommend(p,5,"hybrid")["recommendations"][0]["code"] != engine.recommend(q,5,"hybrid")["recommendations"][0]["code"]

def test_oov_query_preserves_known_interests(engine):
    r=engine.recommend(Profile("xxzzxy",{"recommender systems":5},complete(engine)))
    assert r["recommendations"][0]["code"] == "CS4053"
