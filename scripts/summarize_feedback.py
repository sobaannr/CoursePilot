"""Summarize real, consented post-ranking 1–5 feedback without making qrels."""
import argparse
import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coursepilot.engine import Recommender
from coursepilot.evaluate import mean_ci

def summarize(path):
    engine=Recommender()
    groups=defaultdict(lambda:defaultdict(list))
    seen=set()
    with Path(path).open(encoding="utf-8-sig",newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("consent","").lower() != "true" or row.get("response_type") != "post_ranking_feedback":
                raise ValueError("Only explicitly consented post-ranking feedback is accepted")
            if row.get("dataset_version") != engine.version:
                raise ValueError("Dataset version mismatch")
            pid,method,code=row["participant_id"],row["method"],row["course_code"]
            if not pid.strip() or method not in {"tfidf","hybrid"} or code not in engine.by_code:
                raise ValueError("Invalid participant, method or course")
            key=(pid,method,code)
            if key in seen: raise ValueError("Duplicate participant/method/course response")
            seen.add(key)
            rating=int(row["rating_1_to_5"])
            if rating not in range(1,6): raise ValueError("Ratings must be 1..5")
            groups[method][pid].append(rating)
    if not seen: raise ValueError("No feedback rows")
    results=[]
    for method,participants in sorted(groups.items()):
        results.append({"method":method,"participants":len(participants),
            "ratings":sum(len(v) for v in participants.values()),
            "relevance_1_to_5":mean_ci([sum(v)/len(v) for v in participants.values()])})
    return {"label_origin":"human_feedback","dataset_version":engine.version,
        "source_sha256":hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "notes":"Unblinded post-ranking feedback; participant-averaged. Not a complete relevance benchmark.",
        "summary":results}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--input",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    args=p.parse_args();result=summarize(args.input)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(f"Saved feedback summary: {args.output}")
