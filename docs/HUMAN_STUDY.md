# Human evaluation protocol and instruments

**Status: not yet conducted.** Included demo profiles are fictional. Nothing in this package is a real student response.

## Aim and recruitment

Assess whether recommendations fit students' stated interests, and whether explanations are understandable. Recruit consenting FAST students through a channel the team is authorized to use. Target 20–30 participants if practical; report actual counts, year distribution, recruitment method, missing responses and convenience-sampling limitations. Participation must not affect grades. Do not collect names, roll numbers, marks or contact details in the dataset.

Assign anonymous participant IDs and designate development/test participants before inspecting ratings. Keep all data from one participant in the same split. With a small group, emphasize descriptive results and uncertainty rather than strong population claims. Freeze the catalogue, code and chosen weights before held-out evaluation. Keep a private dated study log.

## Consent text

“CoursePilot is a student project evaluating elective recommendations. You may choose whether to participate and stop at any time. We request your topic interests, completed course codes and relevance ratings, linked only to an anonymous study ID. Your ratings will be used for this course project; only anonymous summaries will be included in the report. Do not enter your name, roll number or grades. You can ask the team to remove your response using your study ID before the stated analysis deadline. No response is sent automatically by the app.”

The team must state its actual retention/deletion date and withdrawal deadline before collection. Do not silently treat clicking a recommendation as consent.

## Phase A: independent judgments for offline metrics

1. Participant selects **My own profile**, enters goals/interests and completed courses, and clicks **Prepare study profile without rankings**. Do not first show recommendations.
2. In **Student study**, review consent, then download the anonymous profile JSON and blank randomized judgment CSV.
3. Participant rates *every eligible candidate* based on the shown course description and their own interests. No model names, scores or ranking are in this packet. The order is randomized using a fixed seed for reproducibility; coordinator can issue varied seeds using `judgment_packet` if counterbalancing is desired.
4. Use this scale: **1** not relevant; **2** slightly relevant; **3** moderately relevant; **4** relevant; **5** very relevant. Unknown/unrated remains blank and is not an irrelevant label. Allow participants to consult official descriptions. Record withdrawal rather than forcing uninformed ratings.
5. If some ratings remain blank, finish them or exclude that participant from complete-catalogue ranking metrics and report the exclusion. Do not fill blanks with zero. This can be time-consuming for 54 candidates; pilot the burden before recruiting the full group.
6. Team gathers files through an approved channel, keeps them in `data/human/private/`, and combines the profile objects into one JSON and rating rows into one CSV. Assign each profile's predeclared `development` or `test` split. Check duplicates rather than averaging repeated submissions silently.

Example combined profile schema (replace values with actual consented data; do not submit this example as a participant):

```json
{"dataset_version":"COPY_FROM_EXPORTED_PROFILE","profiles":[{"participant_id":"P-example","consent":true,"split":"test","profile":{"query":"actual goal","interests":{},"completed":[]}}]}
```

CSV required columns: `participant_id,course_code,rating_1_to_5`. Extra descriptive columns in exported packets are accepted. Grades used for ranking metrics map 1/2 -> 0, 3 -> 1, 4 -> 2, 5 -> 3; grades 2–3 count as relevant.

```powershell
.venv\Scripts\python.exe scripts\import_human_study.py --profiles data/human/private/profiles.json --ratings data/human/private/ratings.csv
.venv\Scripts\python.exe -m coursepilot.evaluate --benchmark data/human/private/benchmark.json --output output/human_evaluation
```

The importer rejects missing consent, unknown IDs, duplicates, incomplete judgments and stale catalogue versions. The evaluator enforces participant separation across splits. This phase allows comparison of all rankers against the same independent judgments.

## Phase B: recommendation relevance and explanation pilot

After Phase A is saved, the student can view a shortlist and rate each recommendation 1–5 in the study tab. Export the feedback CSV. This is post-ranking feedback, affected by presentation and explanations; do not mix it into Phase A labels. The current UI exposes the method name, so this pilot is **not blinded**. Do not describe it as a randomized A/B test.

If the team performs a separate blinded comparison, use anonymized method labels and counterbalance order outside the app; document the procedure. This is optional, not an implemented claim.

Optional interview questions for the team to record manually:

- Was the reason for each recommendation clear? (1 very unclear – 5 very clear)
- Did the system suggest an option you had not considered? (yes/no)
- Which recommendation was least useful, and why?
- Did any prerequisite or course classification appear incorrect?

Combine feedback exports using the same CSV columns, then run:

```powershell
.venv\Scripts\python.exe scripts\summarize_feedback.py --input data/human/private/shortlist_feedback.csv --output output/human_evaluation/feedback_summary.json
```

The script validates consent and response type, rejects duplicate participant/method/course rows, and reports participant-averaged relevance and a participant bootstrap interval. It reports only observed responses, not assumed missing ratings. Keep the feedback sample size distinct from the full-judgment sample size.

## Reporting and limitations

Report per-method Precision@5, Recall@5 and NDCG@5, eligible-pool size, coverage, no-result cases and constraint violations. Inspect confidence intervals and raw per-profile results. Small samples and overlapping courses limit conclusions. Human judgments reflect perceived interest, not subsequent course enjoyment, learning or grades. With self-ratings, inter-rater agreement is not meaningful across different personal profiles; do not invent agreement statistics.

Regenerate the report with the real metric and optional feedback paths described in README. Complete the actual sample description, dates and collection procedure before submission. The generator can insert results but cannot attest that recruitment or consent truly occurred.
