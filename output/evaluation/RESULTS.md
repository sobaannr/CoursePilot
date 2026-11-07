# CoursePilot evaluation (authored_demo)

Split: test; profiles: 12; K: 5; dataset: 4b43a113a2064582.

**Authored scenarios are software checks, not evidence of student satisfaction.**

| Method | Precision | Recall | NDCG | Violations |
|---|---:|---:|---:|---:|
| tfidf | 0.533 | 0.879 | 0.897 | 0 |
| hybrid | 0.550 | 0.900 | 0.922 | 0 |
| keyword | 0.450 | 0.751 | 0.864 | 0 |
| random | 0.060 | 0.096 | 0.077 | 0 |
| text_only | 0.483 | 0.796 | 0.834 | 0 |
| topics_only | 0.500 | 0.850 | 0.869 | 0 |

Precision divides by requested K, including unfilled slots.
Recall and NDCG exclude profiles with zero eligible relevant gain from their means.
All methods use identical prerequisite and completed-course filters.
Random coverage is a union over 20 seeds, not directly comparable to single-run coverage.
Intervals resample participants; authored-demo intervals only describe fixture variability.
In-process latency includes explanation generation; it is not a network load test.