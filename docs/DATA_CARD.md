# Dataset card

- **Name:** CoursePilot public FAST computing catalogue subset.
- **Version / retrieval:** 2026.10.11 / 11 October 2026.
- **Authority:** National University of Computer & Emerging Sciences, 2026 computing catalogue.
- **Discovery:** https://nu.edu.pk/Admissions/ProgramOffered
- **Source:** https://drive.google.com/file/d/1lEyDHS2W41ixoCpD0wQdmYW7yaZeCAy9/view
- **Rows:** 74 = 15 core course entries + 54 project candidate electives + 5 prerequisite lab references.
- **Files:** `courses.json` is authoritative for the application; `courses.csv` is a readable export; `curation.tsv` records authored summaries, tags and project roles.

## Selection and provenance

This is a bounded subset, not the whole 416-page catalogue. It covers CS foundations and specialization options relevant to a BS(CS) elective recommender. Codes, titles, prerequisite text and page numbers are extracted from official pages. Descriptions are concise project summaries, tags are manually curated, and separate lab labels are derived from explicit prerequisite references rather than invented standalone course pages. Source checksum is stored in the JSON.

The source frequently calls specialization courses “core,” even where a student might take them through elective slots. Therefore `source_core_for` and `source_elective_for_cs` retain what the source says, while `category` is the **project candidate role**. This role is provisional. No claim is made that all 54 candidates are approved Karachi electives for the user's batch. This is a documented deviation from the original proposal's intended batch-specific catalogue, accepted as a public-source starting point.

Credit-hour fields are present but null because the selected course pages do not provide them. Null means unknown, not zero. Do not replace them with a guessed “3”. Current offering availability is also unknown. The N/A prerequisite token is preserved and interpreted only as “none listed here.”

## Fields

| Field | Meaning |
|---|---|
| `code`, `title` | Catalogue identity; lab titles are clearly derived labels |
| `description`, `description_status` | Curated searchable summary, with provenance status |
| `credits`, `credits_status` | Nullable number and reason when absent |
| `category`, `category_status` | Project role, not verified batch eligibility |
| `source_core_for`, `source_elective_for_cs` | Source classification preserved separately |
| `tags` | Explicit curated interest vocabulary |
| `prerequisite_groups` | AND of OR code lists |
| `prerequisite_raw`, `prerequisite_status` | Original condition text and interpretation state |
| `source_url`, `source_page` | Public document and one-based PDF page |
| `offering_status` | Unknown pending semester confirmation |

## Validation and maintenance

The loader rejects empty/duplicate IDs, missing fields, unresolved prerequisite codes and cycles. The API rejects unknown completed codes. `scripts/build_catalogue.py` recreates the JSON from the official PDF and curation TSV. Review the actual source pages when changing extraction rules. Do not overwrite `courses.json` with a new curriculum without revisiting the labels and invalidating the benchmark fingerprint.

Before final submission, the team should have an instructor or approved batch plan confirm the candidate list, credits, prerequisites and course names. Record corrections with source/page/date. Do not silently claim those checks happened.

## Rights and privacy

The university retains rights in its catalogue. Public access is not a blanket open-data licence. This project distributes source-tracked metadata and short authored summaries for the course project, with attribution. Check permission before broader redistribution. The source PDF is not included in the submission ZIP. No student personal data, transcripts or real ratings are bundled. Human data should remain in ignored `data/human/private/`; publish only consented anonymous aggregate results.
