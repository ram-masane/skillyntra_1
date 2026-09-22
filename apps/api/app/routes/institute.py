from pathlib import Path

import pandas as pd
from fastapi import APIRouter

from backend.services.course_service import calculate_course_alignment
from app.services.job_service import split_skills

router = APIRouter(prefix="/api/institute", tags=["institute"])
COURSES = pd.read_csv(Path(__file__).resolve().parents[4] / "data" / "courses.csv")
JOBS = pd.read_csv(Path(__file__).resolve().parents[4] / "data" / "jobs.csv")


@router.get("/programs")
def programs() -> list[str]:
    return sorted(COURSES.course.tolist())


@router.get("/programs/{course}")
def alignment(course: str) -> dict:
    row = COURSES[COURSES.course.eq(course)]
    if row.empty:
        return {"course": course, "taught": [], "required": [], "missing": [], "alignment": 0, "status": "At Risk"}
    taught = split_skills(row.iloc[0].skills)
    result = calculate_course_alignment(taught, JOBS)
    return {
        "course": course,
        "taught": taught,
        "required": result["required_skills"],
        "missing": result["missing"],
        "alignment": result["alignment"],
        "status": "Healthy" if result["alignment"] >= 70 else "Needs Update" if result["alignment"] >= 40 else "At Risk"
    }
