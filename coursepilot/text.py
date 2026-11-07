"""Deterministic tokenization, stop-word removal and conservative lemmatization.

No model or corpus downloads occur during inference. The small domain lexicon is
deliberately inspectable; unfamiliar words are preserved, not aggressively stemmed.
"""
import re
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

LEMMAS = {
    "algorithms": "algorithm", "systems": "system", "networks": "network",
    "databases": "database", "models": "model", "languages": "language",
    "applications": "application", "recommendations": "recommendation",
    "recommenders": "recommender", "courses": "course", "students": "student",
    "images": "image", "features": "feature", "trees": "tree", "graphs": "graph",
    "queries": "query", "indices": "index", "matrices": "matrix",
    "processes": "process", "threads": "thread", "patterns": "pattern",
    "services": "service", "methods": "method", "techniques": "technique",
    "robots": "robot", "agents": "agent", "games": "game", "tests": "test",
    "requirements": "requirement", "vectors": "vector", "structures": "structure",
    "classifiers": "classifier", "protocols": "protocol", "attacks": "attack",
    "computers": "computer", "skills": "skill", "decisions": "decision",
    "documents": "document", "interfaces": "interface", "statistics": "statistics",
}
ALIASES = {"ai": "artificial intelligence", "ml": "machine learning",
           "nlp": "natural language processing", "cv": "computer vision",
           "dbms": "database management system", "iot": "internet things",
           "cybersecurity": "cyber security"}

def tokenize(text: str) -> list[str]:
    text = text.lower().replace("c++", " cpp ").replace("c#", " csharp ")
    raw = re.findall(r"[a-z][a-z0-9]*", text)
    expanded = [part for token in raw for part in ALIASES.get(token, token).split()]
    return [LEMMAS.get(token, token) for token in expanded
            if token not in ENGLISH_STOP_WORDS and len(token) > 1]
