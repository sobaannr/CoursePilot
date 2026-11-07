"""Explainable content-based ranking with hard prerequisite constraints."""
from dataclasses import dataclass, field
import math
import random
import time
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
from .catalogue import load_catalogue, fingerprint, eligibility
from .text import tokenize

METHODS = ("tfidf", "hybrid", "keyword", "random")

@dataclass
class Profile:
    query: str = ""
    interests: dict[str, float] = field(default_factory=dict)
    completed: list[str] = field(default_factory=list)

class Recommender:
    def __init__(self, catalogue=None):
        self.catalogue = catalogue if catalogue is not None else load_catalogue()
        self.courses = self.catalogue["courses"]
        self.by_code = {c["code"]: c for c in self.courses}
        self.version = fingerprint(self.catalogue)
        self.tags = sorted({t for c in self.courses for t in c["tags"]})
        self.vectorizer = TfidfVectorizer(tokenizer=tokenize, token_pattern=None,
                                         lowercase=False, sublinear_tf=True, norm="l2")
        # Tags influence only the explicit topic component, not document TF-IDF.
        self.documents = [c["title"] + " " + c["description"] for c in self.courses]
        self.matrix = self.vectorizer.fit_transform(self.documents).tocsr()
        self.terms = self.vectorizer.get_feature_names_out()

    def validate(self, profile):
        if not isinstance(profile.query, str) or len(profile.query) > 5000:
            raise ValueError("Query must be text of at most 5000 characters")
        unknown = set(profile.completed) - self.by_code.keys()
        if unknown:
            raise ValueError("Unknown completed course codes: " + ", ".join(sorted(unknown)))
        if len(profile.completed) != len(set(profile.completed)):
            raise ValueError("Duplicate completed courses")
        for tag, weight in profile.interests.items():
            if tag not in self.tags:
                raise ValueError(f"Unknown interest: {tag}")
            if not isinstance(weight, (int, float)) or not math.isfinite(weight) or not 0 < weight <= 5:
                raise ValueError("Interest weights must be finite numbers in (0, 5]")

    def profile_vector(self, profile):
        vectors, weights = [], []
        if tokenize(profile.query):
            vector = self.vectorizer.transform([profile.query])
            if vector.nnz:
                vectors.append(vector)
                weights.append(1.0)
        if profile.interests:
            total = sum(profile.interests.values())
            interest_vector = csr_matrix((1, self.matrix.shape[1]), dtype=float)
            for tag, weight in profile.interests.items():
                interest_vector += self.vectorizer.transform([tag]) * (weight / total)
            if interest_vector.nnz:
                vectors.append(normalize(interest_vector))
                weights.append(1.0)
        if not vectors:
            return csr_matrix((1, self.matrix.shape[1]), dtype=float)
        return normalize(sum(v * w for v, w in zip(vectors, weights))).tocsr()

    def recommend(self, profile, k=5, method="tfidf", alpha=0.75, seed=42):
        start = time.perf_counter()
        self.validate(profile)
        if not isinstance(k, int) or isinstance(k, bool) or not 1 <= k <= 20:
            raise ValueError("K must be an integer between 1 and 20")
        if method not in METHODS:
            raise ValueError("Unknown ranking method")
        if not math.isfinite(alpha) or not 0 <= alpha <= 1:
            raise ValueError("Alpha must be between 0 and 1")
        completed = set(profile.completed)
        q = self.profile_vector(profile)
        tfidf = (self.matrix @ q.T).toarray().ravel()
        query_tokens = set(tokenize(profile.query + " " + " ".join(profile.interests)))
        exclusions, candidates = [], []
        rng = random.Random(seed)
        effective_alpha = alpha if profile.interests else 1.0
        total_interest = sum(profile.interests.values())
        for idx, course in enumerate(self.courses):
            ok, reason = eligibility(course, completed)
            if not ok:
                exclusions.append({"code": course["code"], "title": course["title"], "reason": reason})
                continue
            matched_tags = sorted(set(course["tags"]) & profile.interests.keys())
            topic = sum(profile.interests[t] for t in matched_tags) / total_interest if total_interest else 0.0
            common = sorted(query_tokens & set(tokenize(self.documents[idx])))
            keyword = len(common) / len(query_tokens) if query_tokens else 0.0
            similarity = float(np.clip(tfidf[idx], 0, 1))
            weights = {"tfidf": (1.0, 0.0), "hybrid": (effective_alpha, 1 - effective_alpha)}
            if method in weights:
                wt, wp = weights[method]
                score = wt * similarity + wp * topic
            elif method == "keyword":
                wt, wp, score = 0.0, 0.0, keyword
            else:
                wt, wp, score = 0.0, 0.0, rng.random()
            # Abstain on zero evidence for deterministic rankers. Random remains
            # a nonpersonalized baseline and may return items with no overlap.
            if method != "random" and score <= 1e-12:
                continue
            contributions = self.matrix[idx].multiply(q).tocsr()
            order = sorted(zip(contributions.indices, contributions.data),
                           key=lambda x: (-x[1], self.terms[x[0]]))
            terms = [{"term": str(self.terms[j]), "cosine_contribution": float(value),
                      "score_contribution": float(wt * value)} for j, value in order]
            candidates.append({
                **course, "score": float(score), "tfidf_similarity": similarity,
                "topic_match": topic, "keyword_match": keyword,
                "components": {"tfidf": wt * similarity, "topics": wp * topic,
                               "keyword": keyword if method == "keyword" else 0.0,
                               "random": score if method == "random" else 0.0},
                "matched_tags": matched_tags, "matched_keywords": common,
                "term_contributions": terms, "eligibility": reason,
            })
        candidates.sort(key=lambda c: (-c["score"], c["code"]))
        warnings = ["Public catalogue rules; Karachi batch applicability and current offerings are unverified."]
        if not candidates:
            warnings.append("No eligible courses with matching evidence. Add interests or revise your profile.")
        elif len(candidates) < k:
            warnings.append(f"Only {len(candidates)} eligible courses have matching evidence.")
        if method == "random":
            warnings.append("Random is an evaluation baseline, not a personalized recommendation.")
        return {"recommendations": candidates[:k], "excluded": exclusions,
                "eligible_count": len(self.courses) - len(exclusions),
                "matching_count": len(candidates), "method": method,
                "alpha": effective_alpha, "k": k, "dataset_version": self.version,
                "model_version": "1.0.0", "warnings": warnings,
                "latency_ms": round((time.perf_counter() - start) * 1000, 3)}
