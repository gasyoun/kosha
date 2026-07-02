"""kosha — fast Sanskrit dictionary lookup service.

FastAPI entry point. Honest stub: serves only / and /health until the
Phase-1 data layer exists (see PHASE1_PLAN.md).
"""
import json
import os
import sys

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

app = FastAPI(
    title=os.getenv("API_TITLE", "kosha"),
    description=os.getenv("API_DESCRIPTION", "Fast Sanskrit Dictionary Lookup"),
    version=os.getenv("API_VERSION", "0.1.0"),
)

try:
    origins = json.loads(os.getenv("CORS_ORIGINS", '["*"]'))
except json.JSONDecodeError:
    origins = ["*"]

# NB: allow_credentials must stay False while origins may be ["*"] —
# Starlette silently drops the wildcard otherwise.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "kosha — Sanskrit Dictionary Lookup", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
