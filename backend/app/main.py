from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import upload, insights, questions


app = FastAPI(title="Sortlytics API")


# Allow frontend (running on a different port) to call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Existing endpoints
app.include_router(
    upload.router,
    prefix="/api",
    tags=["upload"]
)

app.include_router(
    insights.router,
    prefix="/api",
    tags=["insights"]
)


# Phase 4 — Fixed question endpoint
app.include_router(
    questions.router,
    prefix="/api",
    tags=["questions"]
)


@app.get("/")
def health_check():

    return {
        "status": "Sortlytics backend is running"
    }