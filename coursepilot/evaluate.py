"""Reproducible ranking evaluation. Default data are authored demo scenarios.

Run: python -m coursepilot.evaluate --benchmark path.json --output output/evaluation
All eligible candidates must have explicit judgments. Missing is never irrelevant.
"""
import argparse
import csv
import json
import math
from pathlib import Path
import numpy as np
from .catalogue import ROOT, eligibility
from .engine import Recommender, Profile, METHODS

def ranking_metrics(ranked, judgments, k):
    if k < 1 or len(ranked) != len(set(ranked)):
        raise ValueError("Invalid cutoff or duplicate recommendations")
    if any(code not in judgments for code in ranked):
        raise ValueError("Unjudged recommendation")
    relevant = {code for code, grade in judgments.items() if grade >= 2}
    hits = len(set(ranked[:k]) & relevant)
    gains = [2 ** judgments[code] - 1 for code in ranked[:k]]
    dcg = sum(g / math.log2(i + 2) for i, g in enumerate(gains))
    ideal = sorted((2 ** g - 1 for g in judgments.values()), reverse=True)[:k]
    idcg = sum(g / math.log2(i + 2) for i, g in enumerate(ideal))
    return {"precision_at_k": hits / k,
            "recall_at_k": hits / len(relevant) if relevant else None,
            "ndcg_at_k": dcg / idcg if idcg else None,
            "returned_count": len(ranked[:k])}

def validate_benchmark(data, engine):
    if data.get("label_origin") not in {"authored_demo", "human"}:
        raise ValueError("Benchmark must declare authored_demo or human label_origin")
    if not data.get("profiles"):
        raise ValueError("No profiles")
    seen_ids, seen_participants = set(), {}
    for case in data["profiles"]:
        if case["id"] in seen_ids:
            raise ValueError("Duplicate profile id")
        seen_ids.add(case["id"])
        if case["split"] not in {"development", "test"}:
            raise ValueError("Unknown split")
        participant = case["participant_id"]
        if participant in seen_participants and seen_participants[participant] != case["split"]:
            raise ValueError("Participant leakage across splits")
        seen_participants[participant] = case["split"]
        p = Profile(**case["profile"])
        engine.validate(p)
        judgments = case["judgments"]
        if not set(judgments).issubset(engine.by_code):
            raise ValueError("Unknown judged course")
        if any(type(v) is not int or not 0 <= v <= 3 for v in judgments.values()):
            raise ValueError("Grades must be integers 0..3")
        eligible = {c["code"] for c in engine.courses if eligibility(c, set(p.completed))[0]}
        if eligible - judgments.keys():
            raise ValueError(f"Incomplete judgments for {case['id']}")
    if data.get("dataset_version") != engine.version:
        raise ValueError("Benchmark catalogue fingerprint differs; revalidate labels")

def mean_ci(values, seed=42):
    values = np.asarray([v for v in values if v is not None], dtype=float)
    if not len(values):
        return {"mean": None, "low": None, "high": None, "n": 0}
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=(2000, len(values)), replace=True).mean(axis=1)
    return {"mean": float(values.mean()), "low": float(np.quantile(samples, .025)),
            "high": float(np.quantile(samples, .975)), "n": len(values)}

def evaluate(benchmark, output, k=5, split="test"):
    engine = Recommender()
    data = json.loads(Path(benchmark).read_text(encoding="utf-8"))
    validate_benchmark(data, engine)
    selected = [c for c in data["profiles"] if c["split"] == split]
    if not selected:
        raise ValueError("Selected split contains no profiles")
    # Fixed before evaluation; these are design weights, not learned parameters.
    variants = [(m, m, .75, False, False) for m in METHODS] + [
        ("text_only", "tfidf", 1., True, False),
        ("topics_only", "hybrid", 0., False, True),
    ]
    rows = []
    for case in selected:
        original = Profile(**case["profile"])
        eligible = {c["code"] for c in engine.courses if eligibility(c, set(original.completed))[0]}
        qrels = {c: g for c, g in case["judgments"].items() if c in eligible}
        for name, method, alpha, no_interests, no_query in variants:
            p = Profile("" if no_query else original.query,
                        {} if no_interests else original.interests, original.completed)
            for seed in range(20) if method == "random" else [42]:
                result = engine.recommend(p, k, method, alpha, seed)
                codes = [r["code"] for r in result["recommendations"]]
                metrics = ranking_metrics(codes, qrels, k)
                rows.append({"profile_id": case["id"], "participant_id": case["participant_id"],
                    "method": name, "seed": seed, **metrics,
                    "violation_count": sum(c not in eligible for c in codes),
                    "eligible_count": len(eligible), "latency_ms": result["latency_ms"],
                    "recommendations": "|".join(codes)})
    summary = []
    for name, *_ in variants:
        method_rows = [r for r in rows if r["method"] == name]
        item = {"method": name, "profiles": len(selected)}
        for metric in ("precision_at_k", "recall_at_k", "ndcg_at_k"):
            # Average random seeds within profiles, then profiles within people;
            # cluster bootstrap people so repeated profiles don't inflate N.
            participants = {}
            for case in selected:
                values = [r[metric] for r in method_rows if r["profile_id"] == case["id"] and r[metric] is not None]
                if values:
                    participants.setdefault(case["participant_id"], []).append(float(np.mean(values)))
            item[metric] = mean_ci([float(np.mean(v)) for v in participants.values()])
        item["violations"] = sum(r["violation_count"] for r in method_rows)
        item["catalogue_coverage"] = len({c for r in method_rows for c in r["recommendations"].split("|") if c}) / sum(c["category"] == "elective" for c in engine.courses)
        item["latency_p95_ms"] = float(np.percentile([r["latency_ms"] for r in method_rows], 95))
        summary.append(item)
    payload = {"label_origin": data["label_origin"], "split": split, "k": k,
        "dataset_version": engine.version, "profiles": len(selected),
        "participants": len({c['participant_id'] for c in selected}),
        "random_seeds": list(range(20)), "hybrid_alpha": .75,
        "notes": ["Precision divides by requested K, including unfilled slots.",
                  "Recall and NDCG exclude profiles with zero eligible relevant gain from their means.",
                  "All methods use identical prerequisite and completed-course filters.",
                  "Random coverage is a union over 20 seeds, not directly comparable to single-run coverage.",
                  "Intervals resample participants; authored-demo intervals only describe fixture variability.",
                  "In-process latency includes explanation generation; it is not a network load test."],
        "summary": summary}
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with (out / "per_profile.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    lines = [f"# CoursePilot evaluation ({data['label_origin']})", "",
             f"Split: {split}; profiles: {len(selected)}; K: {k}; dataset: {engine.version}.", "",
             "**Authored scenarios are software checks, not evidence of student satisfaction.**" if data["label_origin"] == "authored_demo" else "Human judgments; see study protocol and collection provenance.", "",
             "| Method | Precision | Recall | NDCG | Violations |", "|---|---:|---:|---:|---:|"]
    def fmt(value):
        return "N/A" if value is None else f"{value:.3f}"
    for row in summary:
        lines.append(f"| {row['method']} | {fmt(row['precision_at_k']['mean'])} | {fmt(row['recall_at_k']['mean'])} | {fmt(row['ndcg_at_k']['mean'])} | {row['violations']} |")
    lines += ["", *payload["notes"]]
    (out / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    return payload

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, default=ROOT / "data/evaluation/benchmark_demo.json")
    parser.add_argument("--output", type=Path, default=ROOT / "output/evaluation")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--split", choices=["development", "test"], default="test")
    args = parser.parse_args()
    result = evaluate(args.benchmark, args.output, args.k, args.split)
    print(f"Evaluated {result['profiles']} {result['label_origin']} profiles; results: {args.output}")

if __name__ == "__main__":
    main()
