# Demonstration and viva preparation

## Five-minute demonstration

1. **Problem (30 seconds):** elective choices should match a student's interests while respecting completed courses and listed prerequisites. Explain the public-catalogue limitations up front.
2. **Profile (45 seconds):** choose the AI engineer preset or type a custom career goal, explain weighted interests and free text, and submit. State that scores are matching scores, not success probabilities.
3. **Explanation (60 seconds):** open a result; show the actual term products. Switch to the hybrid method, inspect text/topic components and show that the sum equals the score.
4. **Constraints (45 seconds):** select CS2001 without CL2001 in a test profile and search for neural perception. Show CS4045 in the exclusions. Completing theory alone does not satisfy its listed lab requirement.
5. **Experiments (60 seconds):** compare TF-IDF, hybrid, keyword and random, then ablations. Explain Precision/Recall/NDCG. Label authored results correctly; show real study results only after collection.
6. **Engineering and limits (40 seconds):** show the test command, source page links, API docs and study packet. State what has and has not been validated.

## Questions to prepare

**Why content-based filtering?** There is no real user–course interaction matrix in the proposal. Item descriptions and explicit interests permit cold-start recommendations. Fabricating collaborative interactions would not solve the data problem.

**Is this different from search?** It uses free-text retrieval plus a weighted persistent-in-session interest profile and eligibility constraints. It is a modest content-based recommender, not a learned behavioral personalization model.

**How does TF-IDF work?** Explain term frequency, inverse document frequency, L2 normalization and cosine similarity using `docs/METHODOLOGY.md`. Explain why a shared rare term may contribute more than a frequent one.

**How are the explanations faithful?** Each term's contribution is the product of the normalized item and profile coordinates. All products sum to the cosine score. In the hybrid, the two weighted components sum to the final score. No LLM invents the reasons.

**Why not use deep learning?** The catalogue is small and the brief requires explainability. A neural model is not automatically better, and explanation text would not make its internal score transparent.

**Where is the novelty?** The project combines transparent topic weighting, source-tracked prerequisite handling, abstention and measured ablations in a local advising use case. These are established techniques; avoid claiming a novel research algorithm.

**Does 0.8 mean an 80% chance the student will like the course?** No. It is an uncalibrated similarity/composite score.

**Why are precision and recall different?** Precision measures how many displayed slots are relevant; recall measures how much of the eligible relevant set was found. The full judged candidate set is required for recall.

**Can the reported scores prove usefulness?** Authored demo metrics cannot. Independent student judgments and a human relevance pilot provide stronger evidence but still do not establish educational outcomes.

**How did you prevent leakage?** No relevance labels feed TF-IDF. Weights are fixed in advance. Real participants cannot cross development/test splits; labels must match the catalogue fingerprint. Demo splits remain illustrative rather than unbiased.

**What if prerequisites are missing?** Unknown-status candidates are excluded. Source N/A is shown as none listed, with a warning that the batch policy may differ. We do not invent prerequisites or official credits.

**What did each member do?** Answer from the actual contribution log. Disclose AI assistance according to instructor policy and be able to explain every component you submit.

## Optional presentation outline

Problem and scope → catalogue/provenance → scoring and explanation → live demonstration → experiments → human study → limitations and next steps. A slide deck is not required by the provided brief; this outline supports an oral demo.

## CV wording after completion

“Built an explainable elective recommender with source-tracked metadata, prerequisite constraints and additive score explanations; compared four rankers using held-out student judgments and deployed a tested local API.”

Only use “held-out student judgments” after conducting that study; until then say “authored diagnostic scenarios.” Name your own contribution and replace generic claims with measured results. Do not claim public production deployment from a local demo.
