
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from backend.app.math_engine import solve_math


app = FastAPI(
    title="MathGenius AI",
    description="Multilingual AI Mathematics Platform",
    version="0.2.0"
)


class SolveRequest(BaseModel):
    problem: str = Field(min_length=1, max_length=200)


@app.get("/")
def home():
    return {
        "project": "MathGenius AI",
        "status": "running",
        "version": "0.2.0"
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "service": "math-engine-api"
    }


@app.post("/api/solve")
def solve(request: SolveRequest):
    try:
        return solve_math(request.problem)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )
