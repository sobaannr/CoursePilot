import csv
import importlib.util
import json
import pytest
from coursepilot.catalogue import ROOT
from coursepilot.engine import Recommender
from coursepilot.study import csv_text

spec=importlib.util.spec_from_file_location("feedback",ROOT/"scripts/summarize_feedback.py")
feedback=importlib.util.module_from_spec(spec);spec.loader.exec_module(feedback)

def test_feedback_uses_participant_means(tmp_path):
    e=Recommender()
    base={"method":"tfidf","dataset_version":e.version,"response_type":"post_ranking_feedback","consent":True}
    rows=[{**base,"participant_id":"test-a","course_code":"CS4053","rating_1_to_5":5},
          {**base,"participant_id":"test-a","course_code":"CS4051","rating_1_to_5":5},
          {**base,"participant_id":"test-b","course_code":"CS4053","rating_1_to_5":1}]
    path=tmp_path/"synthetic_test_feedback.csv";path.write_text(csv_text(rows),encoding="utf-8")
    result=feedback.summarize(path)
    assert result["summary"][0]["relevance_1_to_5"]["mean"]==3
    assert result["summary"][0]["participants"]==2
    rows.append(rows[0]);path.write_text(csv_text(rows),encoding="utf-8")
    with pytest.raises(ValueError,match="Duplicate"): feedback.summarize(path)

def test_report_accepts_optional_human_result_layout(tmp_path):
    # Synthetic test doubles are written only to pytest's temporary directory.
    spec=importlib.util.spec_from_file_location("report",ROOT/"scripts/build_report.py")
    report=importlib.util.module_from_spec(spec);spec.loader.exec_module(report)
    metrics=json.loads((ROOT/"output/evaluation/metrics.json").read_text())
    human={**metrics,"label_origin":"human"}
    ratings={"summary":[{"method":"tfidf","participants":2,"ratings":10,
        "relevance_1_to_5":{"mean":3,"low":1,"high":5}}]}
    path=tmp_path/"synthetic_layout_check.pdf"
    report.build_report(metrics,human,ratings,path)
    assert len(report.PdfReader(path).pages)==3
