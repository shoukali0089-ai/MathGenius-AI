
from fastapi import FastAPI

app = FastAPI(
    title="MathGenius AI",
    description="Multilingual AI Mathematics Platform",
    version="0.1.0"
)

@app.get("/")
def home():
    return {
        "project": "MathGenius AI",
        "status": "running",
        "version": "0.1.0"
    }

@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "service": "math-engine-api"
    }
