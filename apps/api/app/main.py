import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import assessments, careers, courses, government, institute, jobs, skills, workflow

app = FastAPI(title="Skillyntra API", version="0.1.0")

_frontend_origin = os.environ.get("FRONTEND_ORIGIN", "").strip()
_frontend_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
if _frontend_origin:
    _frontend_origins.extend(
        origin.strip() for origin in _frontend_origin.split(",") if origin.strip()
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(jobs.router)
app.include_router(skills.router)
app.include_router(careers.router)
app.include_router(courses.router)
app.include_router(assessments.router)
app.include_router(institute.router)
app.include_router(government.router)
app.include_router(workflow.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "skillyntra-api", "mode": "prototype"}
