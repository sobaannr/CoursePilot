"""Human-study packets and validated imports, kept separate from demo fixtures."""
import csv
import io
import json
import random
from collections import defaultdict
from pathlib import Path
from .catalogue import eligibility
from .engine import Profile

def csv_text(rows):
    if not rows:
        return ""
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    # Neutralize spreadsheet formulas in text fields on exported CSVs.
    for row in rows:
        writer.writerow({k: "'" + v if isinstance(v, str) and v.lstrip().startswith(("=", "+", "-", "@")) else v for k,v in row.items()})
    return handle.getvalue()

def judgment_packet(engine, profile, participant_id, seed=42):
    engine.validate(profile)
    courses = [c for c in engine.courses if eligibility(c, set(profile.completed))[0]]
    random.Random(seed).shuffle(courses)
    return [{"participant_id": participant_id, "course_code": c["code"],
             "title": c["title"], "description": c["description"], "rating_1_to_5": ""}
            for c in courses]

def import_human_benchmark(profiles_path, ratings_path, engine):
    data = json.loads(Path(profiles_path).read_text(encoding="utf-8"))
    if data.get("dataset_version") != engine.version:
        raise ValueError("Study catalogue changed; regenerate and review packets")
    profiles = data.get("profiles", [])
    by_participant = {}
    for p in profiles:
        if p.get("consent") is not True:
            raise ValueError("Every participant must explicitly consent")
        participant = p["participant_id"]
        if not participant.strip() or participant in by_participant:
            raise ValueError("Use one unique, nonempty anonymous ID per participant")
        engine.validate(Profile(**p["profile"]))
        by_participant[participant] = p
    ratings = defaultdict(dict)
    with Path(ratings_path).open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            pid, code = row["participant_id"], row["course_code"]
            if pid not in by_participant or code not in engine.by_code:
                raise ValueError("Unknown participant or course")
            if code in ratings[pid]:
                raise ValueError("Duplicate participant/course rating")
            try:
                rating = int(row["rating_1_to_5"])
            except (ValueError, TypeError) as exc:
                raise ValueError("All judgment cells must contain an integer 1..5") from exc
            if rating not in range(1, 6):
                raise ValueError("Rating outside 1..5")
            ratings[pid][code] = {1:0, 2:0, 3:1, 4:2, 5:3}[rating]
    result = {"label_origin": "human", "dataset_version": engine.version,
              "description": "Human self-relevance judgments. Ratings 1/2->0, 3->1, 4->2, 5->3. One profile per participant.",
              "profiles": []}
    for pid, item in by_participant.items():
        eligible = {c["code"] for c in engine.courses if eligibility(c, set(item["profile"]["completed"]))[0]}
        if eligible != ratings[pid].keys():
            raise ValueError(f"Ratings for {pid} must cover exactly the eligible candidates")
        result["profiles"].append({"id": pid, "participant_id": pid, "split": item["split"],
            "profile": item["profile"], "judgments": ratings[pid]})
    from .evaluate import validate_benchmark
    validate_benchmark(result, engine)
    return result
