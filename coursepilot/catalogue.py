"""Validated, source-tracked course data."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOGUE = ROOT / "data" / "courses.json"

def load_catalogue(path=DEFAULT_CATALOGUE):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    courses = payload["courses"]
    ids = [c["code"] for c in courses]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate course codes")
    if not courses:
        raise ValueError("Empty catalogue")
    required = {"code", "title", "description", "credits", "category", "tags",
                "prerequisite_groups", "prerequisite_status", "source_url", "source_page"}
    for c in courses:
        if required - c.keys():
            raise ValueError(f"Missing fields in {c.get('code')}: {required - c.keys()}")
        if c["category"] not in {"core", "elective", "support"}:
            raise ValueError(f"Invalid category: {c['code']}")
        if c["prerequisite_status"] not in {"catalogue", "unknown"}:
            raise ValueError("Invalid prerequisite status")
        if not c["description"].strip() or not c["title"].strip():
            raise ValueError("Empty course text")
        for group in c["prerequisite_groups"]:
            if not group or not set(group).issubset(ids):
                raise ValueError(f"Unresolved prerequisite for {c['code']}: {group}")
    # OR alternatives must not be interpreted as an AND. Detect definite cycles
    # conservatively by traversing every edge (data should not contain any).
    by_id = {c["code"]: c for c in courses}
    def visit(code, active, done):
        if code in active:
            raise ValueError(f"Prerequisite cycle at {code}")
        if code in done:
            return
        active.add(code)
        for group in by_id[code]["prerequisite_groups"]:
            for other in group:
                visit(other, active, done)
        active.remove(code)
        done.add(code)
    done = set()
    for code in ids:
        visit(code, set(), done)
    return payload

def fingerprint(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]

def eligibility(course, completed):
    if course["code"] in completed:
        return False, "Already completed"
    if course["category"] != "elective":
        return False, "Not in the elective candidate pool"
    if course["prerequisite_status"] == "unknown":
        return False, "Prerequisite information needs verification"
    missing = [" or ".join(group) for group in course["prerequisite_groups"]
               if not set(group).intersection(completed)]
    if missing:
        return False, "Missing prerequisites: " + "; ".join(missing)
    return True, "Meets prerequisites listed in the public catalogue"
