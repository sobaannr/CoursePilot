"""Stateless local API. No student profiles are persisted."""
from functools import lru_cache
from typing import Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from .engine import Recommender, Profile

app = FastAPI(title="CoursePilot", version="1.0.0",
              description="Explainable elective ranking against a public FAST catalogue.")

@lru_cache(maxsize=1)
def engine():
    return Recommender()

class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    query: str = Field(default="", max_length=5000)
    interests: dict[str, float] = Field(default_factory=dict)
    completed: list[str] = Field(default_factory=list, max_length=200)
    k: int = Field(default=5, ge=1, le=20, strict=True)
    method: Literal["tfidf", "hybrid", "keyword", "random"] = "tfidf"
    alpha: float = Field(default=0.75, ge=0, le=1)

@app.get("/health")
def health():
    return {"status": "ok", "dataset_version": engine().version}

@app.get("/courses")
def courses():
    return engine().catalogue

@app.post("/recommend")
def recommend(request: RecommendationRequest):
    try:
        return engine().recommend(Profile(request.query, request.interests, request.completed),
                                  request.k, request.method, request.alpha)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
