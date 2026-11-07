"""Rebuild source-backed metadata from the downloaded official PDF.

Input PDF must be downloaded separately; this command performs no network access.
Descriptions/tags and candidate roles are explicit curation in data/curation.tsv.
"""
import csv
import hashlib
import json
import re
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
URL = "https://drive.google.com/file/d/1lEyDHS2W41ixoCpD0wQdmYW7yaZeCAy9/view"

def build():
    source = ROOT / "data/sources/fast_computing_catalogue_2026.pdf"
    extracted = ROOT / "data/sources/catalogue_extracted.txt"
    # Cache is an extraction convenience, never the authority.
    if extracted.exists():
        pages = extracted.read_text(encoding="utf-8").split("\n\f\n")
    else:
        pages = [p.extract_text() for p in PdfReader(source).pages]
    records = {}
    for page_no, page in enumerate(pages, 1):
        match = re.search(r"Course Code:\s*([A-Z]{2}\d{4})", page)
        if match:
            records[match.group(1)] = (page_no, page)
    courses = []
    with (ROOT / "data/curation.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            page_no, text = records[row["code"]]
            title = re.search(r"Course Title:\s*(.*?)\s*Course Code:", text, re.S).group(1)
            raw = re.search(r"Pre-requisite\(s\):\s*(.*?)(?:Equivalent:|Core for Degree)", text, re.S).group(1)
            raw = " ".join(raw.split())
            prereqs = re.findall(r"[A-Z]{2}\d{4}", raw)
            core = re.search(r"Core for Degree Programs:\s*(.*?)\s*Elective for", text, re.S).group(1)
            is_elective = bool(re.search(r"Elective for Degree Programs:\s*BS", text))
            status = "catalogue" if prereqs or raw == "N/A" else "unknown"
            courses.append({
                "code": row["code"], "title": " ".join(title.split()),
                "description": row["description"], "credits": None,
                "credits_status": "Not specified on this catalogue page",
                "category": row["category"], "category_status": "project_curated_unverified_for_batch",
                "source_core_for": " ".join(core.split()),
                "source_elective_for_cs": is_elective,
                "tags": row["tags"].split(";"),
                "prerequisite_groups": [[code] for code in prereqs],
                "prerequisite_raw": raw, "prerequisite_status": status,
                "source_url": URL, "source_page": page_no,
                "offering_status": "unknown", "description_status": "curated_summary",
            })
    # The catalogue lists separate lab prerequisites without standalone lab pages.
    # Keep them explicit so selecting a theory course never silently waives a lab.
    labs = {}
    for course in courses:
        for group in course["prerequisite_groups"]:
            for code in group:
                if code.startswith("CL"):
                    labs.setdefault(code, course["source_page"])
    for code, page in labs.items():
        parent = next(c for c in courses if c["code"] == "CS" + code[2:])
        courses.append({"code": code, "title": parent["title"] + " (lab component)",
            "description": "Laboratory component linked to " + parent["title"] + ".",
            "credits": None, "credits_status": "Not specified in prerequisite reference",
            "category": "support", "category_status": "prerequisite_reference_only",
            "source_core_for": "Not separately specified", "source_elective_for_cs": False,
            "tags": parent["tags"], "prerequisite_groups": [], "prerequisite_raw": "Not specified",
            "prerequisite_status": "unknown", "source_url": URL, "source_page": page,
            "offering_status": "unknown", "description_status": "derived_lab_label"})
    result = {
        "name": "CoursePilot public FAST computing catalogue subset",
        "version": "2026.10.11", "retrieved_on": "2026-10-11",
        "source_url": URL, "source_discovery_url": "https://nu.edu.pk/Admissions/ProgramOffered",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "scope": "National 2026 catalogue; project-curated elective pool, not a verified Karachi 2023-batch plan.",
        "limitations": [
            "The source marks many specialization courses as core. Project candidate roles are explicitly curated and require batch verification.",
            "N/A prerequisites mean none listed in this source, not an authoritative waiver.",
            "Credit hours absent from course pages are null, never guessed.",
            "Offering availability, seats, timetable and batch rules are unknown.",
            "Descriptions and topic tags are project-curated summaries, not official course outlines.",
        ],
        "courses": sorted(courses, key=lambda c: c["code"]),
    }
    (ROOT / "data/courses.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    with (ROOT / "data/courses.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(result["courses"][0]))
        writer.writeheader()
        for c in result["courses"]:
            writer.writerow({k: json.dumps(v) if isinstance(v, (list, dict)) else v for k,v in c.items()})
    print(f"Built {len(courses)} rows; {sum(c['category']=='elective' for c in courses)} candidate electives.")

if __name__ == "__main__":
    build()
