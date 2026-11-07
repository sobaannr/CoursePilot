"""Authored scenarios and judgments. NOT a human study or unbiased benchmark.

Positive grades below are manually specified for each fictional intent; all other
candidate electives receive explicit zero. No recommender output generates labels.
The authors know the catalogue: performance may be optimistic.
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coursepilot.catalogue import ROOT, load_catalogue, fingerprint

SCENARIOS = [
    ("search", "Build a search engine that indexes documents and ranks relevant results", {"information retrieval": 5, "natural language processing": 2}, {"CS4051":3,"CS4053":2,"CS4063":2,"CS4047":2,"CS4102":1}),
    ("vision", "Recognize objects in photographs and train neural networks for visual perception", {"computer vision":5,"deep learning":4}, {"CS4045":3,"CS4059":3,"CS4055":2,"CS4112":3,"CS4104":1}),
    ("data_platform", "Build reliable distributed data pipelines and analytical storage for large datasets", {"data engineering":5,"databases":3}, {"CS4083":3,"CS4033":3,"CS4109":3,"CS4087":2,"CS4058":2,"CS4080":2,"CS4064":1,"CS4073":1}),
    ("security", "Protect a company network and investigate vulnerabilities in communication protocols", {"cybersecurity":5,"networks":4}, {"CS4065":3,"CS4061":3,"CS4105":2,"CS4068":2,"CS4050":1,"CS4114":1}),
    ("mobile", "Develop useful phone applications with interfaces and connected services", {"mobile development":5,"human computer interaction":2}, {"CS4039":3,"CS4074":2,"CS4069":2,"CS4032":1,"CS4070":1}),
    ("mlops", "Deploy predictive models and monitor reliable machine learning services", {"mlops":5,"devops":4,"machine learning":2}, {"CS4085":3,"CS4067":3,"CS4037":2,"CS4075":2,"CS4104":2,"CS4112":1}),
    ("language", "Analyze reviews and build text classification and natural language applications", {"natural language processing":5,"machine learning":2}, {"CS4047":3,"CS4063":3,"CS4051":2,"CS4112":1,"CS4088":1,"CS4053":1}),
    ("game", "Create interactive games with rendering graphics and engaging gameplay", {"game development":5,"computer graphics":4}, {"CS4046":3,"CS4035":3,"CS4074":1,"CS4039":1}),
    ("finance", "Backtest automated trading strategies and analyze financial data and risk", {"finance":5,"data science":2}, {"CS4052":3,"CS4062":2,"CS4048":2,"CS4104":1,"CS4049":1}),
    ("geospatial", "Study environmental change using satellite imagery and geographic information", {"geospatial":5,"data science":2}, {"CS4040":3,"CS4086":3,"CS4055":2,"CS4048":1,"CS4059":1}),
    ("testing", "Improve software quality with automated tests and continuous integration", {"testing":5,"devops":3,"software engineering":2}, {"CS4036":3,"CS4067":3,"CS4118":2,"CS4057":1,"CS4044":1}),
    ("ux", "Research user needs and design accessible usable digital interfaces", {"human computer interaction":5,"design":4}, {"CS4074":3,"CS4069":3,"CS4032":1,"CS4070":1,"CS4039":1}),
    ("cloud", "Understand virtualized infrastructure and deploy secure cloud services", {"cloud computing":5,"cybersecurity":2}, {"CS4037":3,"CS4075":3,"CS4105":3,"CS4067":2,"CS4083":1}),
    ("robotics", "Apply learning algorithms to perception and decision making for robots", {"robotics":5,"machine learning":3}, {"CS4090":3,"CS4045":2,"CS4059":2,"CS4104":2,"CS4114":1,"CS4112":2}),
    ("recommendation", "Personalize item suggestions using user preferences and evaluate ranked recommendations", {"recommender systems":5,"information retrieval":3}, {"CS4053":3,"CS4051":3,"CS4038":2,"CS4080":1,"CS4104":1}),
    ("database", "Tune database queries and manage transactions backup and recovery", {"databases":5,"systems":2}, {"CS4087":3,"CS4073":3,"CS4064":3,"CS4033":1,"CS4058":1}),
    ("iot", "Build connected sensors with edge processing and secure messaging", {"internet of things":5,"networks":2}, {"CS4114":3,"CS4068":2,"CS4065":2,"CS4075":1,"CS4105":1}),
    ("management", "Lead a software team using agile planning estimation and project risk management", {"project management":5,"software engineering":2}, {"CS4044":3,"CS4057":3,"CS4036":1,"CS4118":2}),
]

def main():
    cat = load_catalogue()
    completed = [c["code"] for c in cat["courses"] if c["category"] != "elective"]
    profiles = []
    for i, (name, query, interests, positives) in enumerate(SCENARIOS):
        judgments = {c["code"]: positives.get(c["code"], 0) for c in cat["courses"] if c["category"] == "elective"}
        profiles.append({"id": name, "participant_id": "fictional_" + name,
            "split": "development" if i < 6 else "test",
            "profile": {"query": query, "interests": interests, "completed": completed},
            "judgments": judgments})
    data = {"label_origin": "authored_demo", "dataset_version": fingerprint(cat),
            "description": "18 authored fictional profiles; explicit grades 0..3, not student responses. Development/test partition is illustrative only. No tuning performed.",
            "profiles": profiles}
    out = ROOT / "data/evaluation"; out.mkdir(parents=True, exist_ok=True)
    (out / "benchmark_demo.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    print("Wrote 18 authored demo profiles (6 development, 12 test).")

if __name__ == "__main__":
    main()
