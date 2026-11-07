import copy
import json
import pytest
from coursepilot.catalogue import ROOT
from coursepilot.engine import Recommender
from coursepilot.evaluate import ranking_metrics, validate_benchmark

def test_metrics_against_hand_calculation():
    r=ranking_metrics(["b","a"],{"a":3,"b":0,"c":2},2)
    assert r["precision_at_k"] == .5
    assert r["recall_at_k"] == .5
    assert r["ndcg_at_k"] == pytest.approx((7/1.5849625)/(7+3/1.5849625))

def test_abstention_penalizes_precision():
    r=ranking_metrics(["a"],{"a":3,"b":2},5)
    assert r["precision_at_k"] == .2
    assert r["recall_at_k"] == .5

def test_no_relevant_items_is_undefined():
    r=ranking_metrics([],{"a":0},5)
    assert r["recall_at_k"] is None and r["ndcg_at_k"] is None

def test_unjudged_is_not_irrelevant():
    with pytest.raises(ValueError): ranking_metrics(["a"],{},5)

def benchmark():
    return json.loads((ROOT/"data/evaluation/benchmark_demo.json").read_text())

def test_demo_origin_and_labels():
    data=benchmark()
    assert data["label_origin"]=="authored_demo"
    validate_benchmark(data,Recommender())

def test_leakage_guard():
    data=benchmark()
    data["profiles"][-1]["participant_id"]=data["profiles"][0]["participant_id"]
    with pytest.raises(ValueError,match="leakage"): validate_benchmark(data,Recommender())

def test_missing_judgments_rejected():
    data=benchmark()
    data["profiles"][0]["judgments"].pop("CS4053")
    with pytest.raises(ValueError,match="Incomplete"): validate_benchmark(data,Recommender())

def test_version_mismatch_rejected():
    data=benchmark();data["dataset_version"]="wrong"
    with pytest.raises(ValueError,match="fingerprint"): validate_benchmark(data,Recommender())
