# Verification record

Public release verified 7 November 2026. Earlier smoke-test and PDF observations below were recorded in the local course workspace.

## Automated checks

`python -m pytest -q --tb=short`

**41 passed, zero failures/errors/skips** on the exact public source copy. Initial sandbox runs encountered Windows temporary-directory access errors; the complete suite passed when rerun outside that sandbox. Checks cover catalogue integrity, preprocessing, all rankers' eligibility behavior, explicit lab requirements, completed courses, score reconstruction, no-evidence abstention, seeded behavior, invalid inputs, API routes, metric hand calculations, benchmark completeness/versioning, participant leakage, consent, CSV export safety, feedback aggregation, UI flows and optional-human-results report pagination.

One dependency deprecation warning was emitted: the installed Starlette test client warns about its HTTPX compatibility path. The API tests passed; this is not reported as an application failure.

## Live smoke test

The Streamlit health route on localhost port 8517 returned 200. The separately running Uvicorn API on localhost port 8017 returned a healthy dataset fingerprint and five hybrid recommendations for a fictional recommendation-systems query. CS4053 was first. Every returned score equalled the sum of its components. The original smoke-test artifact is retained in the local course workspace and excluded from the public repository.

## Evaluation

`python -m coursepilot.evaluate` completed for 12 authored test profiles, comparing four rankers and two ablations. Every measured method recorded zero violations of the encoded constraints. Results and per-profile rows are in `output/evaluation/`. These are diagnostic fictional scenarios, not a human study. Dataset fingerprint: `4b43a113a2064582`.

## UI and PDF inspection

The app was opened in the in-app browser; the fictional AI-engineer profile returned recommendations and exposed explanation controls. Streamlit AppTest separately exercised the recommendation path and study preparation without rankings.

All three report pages and the one-page proposal were rendered and visually inspected. No clipping or overflow was observed. The generator asserts their page counts. A test also checks three-page report pagination with synthetic optional human-result inputs written only to a test temporary directory; these are not included in the delivered report.

## Environment and limits

Python 3.12 on Windows; installed versions are recorded in `requirements-lock.txt`. Direct run, tests, evaluation and PDF generation were exercised. Docker files and a CI workflow are included, but the Docker daemon was unavailable, so no container build/run is claimed. The workflow has not been executed on GitHub. No load test, public deployment, real student study or departmental curriculum verification has been performed.

