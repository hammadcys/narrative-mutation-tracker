

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from pipeline import run_pipeline, ask_question

app = FastAPI(
    title="Misinformation Trail Tracker API",
    description="Traces how viral claims mutate across Pakistani and South Asian media.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    claim: str
    date_from: str | None = None
    date_to: str | None = None

    @field_validator("claim")
    @classmethod
    def claim_must_be_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 5:
            raise ValueError("Claim must be at least 5 characters.")
        return v[:500]

class QuestionRequest(BaseModel):
    question: str

@app.get("/health")
def health():
    return {"status": "ok", "service": "Misinformation Trail Tracker"}

@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    result = run_pipeline(request.claim, request.date_from, request.date_to)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result

@app.post("/ask")
def ask(request: QuestionRequest):
    question = request.question.strip()[:500]
    if len(question) < 5:
        raise HTTPException(status_code=400, detail="Question must be at least 5 characters.")
    return ask_question(question)
