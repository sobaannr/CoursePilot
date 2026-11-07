import json
import pytest
from coursepilot.engine import Recommender, Profile
from coursepilot.study import csv_text, judgment_packet, import_human_benchmark

def test_packet_has_no_rank_or_score():
    e=Recommender(); rows=judgment_packet(e,Profile("data"),"P-test")
    assert rows
    assert all(r["rating_1_to_5"]=="" and "score" not in r for r in rows)
    assert len({r["course_code"] for r in rows})==len(rows)

def test_csv_formula_neutralization():
    assert "'=2+2" in csv_text([{"text":"=2+2"}])

def test_human_import_and_missing_rating(tmp_path):
    e=Recommender(); p=Profile("data")
    profiles={"dataset_version":e.version,"profiles":[{"participant_id":"P-test","consent":True,"split":"test","profile":{"query":p.query,"interests":{},"completed":[]}}]}
    pp=tmp_path/"profiles.json";pp.write_text(json.dumps(profiles))
    rows=judgment_packet(e,p,"P-test")
    for row in rows: row["rating_1_to_5"]=4
    rp=tmp_path/"ratings.csv";rp.write_text(csv_text(rows),encoding="utf-8")
    data=import_human_benchmark(pp,rp,e)
    assert data["label_origin"]=="human"
    rows[0]["rating_1_to_5"]=""
    rp.write_text(csv_text(rows),encoding="utf-8")
    with pytest.raises(ValueError,match="integer"): import_human_benchmark(pp,rp,e)

def test_consent_required(tmp_path):
    e=Recommender(); path=tmp_path/"p.json"
    path.write_text(json.dumps({"dataset_version":e.version,"profiles":[{"consent":False}]}))
    with pytest.raises(ValueError,match="consent"): import_human_benchmark(path,tmp_path/"unused",e)
