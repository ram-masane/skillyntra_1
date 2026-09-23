from pathlib import Path

import pandas as pd
from fastapi import APIRouter

from backend.services.course_service import calculate_course_alignment, calculate_course_health
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
        return {
            "course": course,
            "taught": [],
            "required": [],
            "missing": [],
            "covered": [],
            "alignment": 0,
            "placement_rate": 0,
            "employer_validation": 0,
            "health_score": 0,
            "health_status": "At Risk",
            "status": "At Risk",
        }
    row = row.iloc[0]
    taught = split_skills(row.skills)
    alignment_result = calculate_course_alignment(taught, JOBS)
    health = calculate_course_health(row, JOBS)
    return {
        "course": course,
        "taught": taught,
        "required": alignment_result["required_skills"],
        "missing": alignment_result["missing"],
        "covered": alignment_result["covered"],
        "alignment": alignment_result["alignment"],
        "placement_rate": health["placement"],
        "employer_validation": health["employer"],
        "health_score": health["score"],
        "health_status": health["status"],
        "status": "Healthy" if alignment_result["alignment"] >= 70 else "Needs Update" if alignment_result["alignment"] >= 40 else "At Risk",
    }
