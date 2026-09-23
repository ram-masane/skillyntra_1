from pathlib import Path

import pandas as pd
from fastapi import APIRouter

from backend.services.course_service import calculate_course_alignment, calculate_course_health
from app.services.job_service import split_skills

router = APIRouter(prefix="/api/institute", tags=["institute"])
COURSES = pd.read_csv(Path(__file__).resolve().parents[4] / "data" / "courses.csv")
JOBS = pd.read_csv(Path(__file__).resolve().parents[4] / "data" / "jobs.csv")


def _build_curriculum_proposal(alignment_result: dict) -> dict:
    """Build structured curriculum update proposal from alignment result."""
    skill_demand = alignment_result.get("skill_demand", [])
    missing = alignment_result.get("missing", [])
    covered = alignment_result.get("covered", [])

    # Create lookup for job_signals by skill (case-insensitive)
    demand_map = {item["skill"].lower(): item["job_signals"] for item in skill_demand}

    # Build proposal for missing skills, prioritized by descending job_signals
    missing_with_signals = []
    for skill in missing:
        signals = demand_map.get(skill.lower(), 0)
        missing_with_signals.append({
            "skill": skill,
            "job_signals": signals,
        })

    # Sort by job_signals descending, then skill name for deterministic ordering
    missing_with_signals.sort(key=lambda x: (-x["job_signals"], x["skill"]))

    proposal_skills = []
    for idx, item in enumerate(missing_with_signals, start=1):
        skill = item["skill"]
        signals = item["job_signals"]
        recommendation = (
            f"Add or strengthen {skill} coverage because it is demanded by "
            f"{signals} relevant job signals."
        )
        proposal_skills.append({
            "skill": skill,
            "job_signals": signals,
            "priority": idx,
            "recommendation": recommendation
        })

    # Build keep list (covered skills with their demand signals)
    keep_skills = []
    for skill in covered:
        signals = demand_map.get(skill.lower(), 0)
        keep_skills.append({
            "skill": skill,
            "job_signals": signals
        })
    keep_skills.sort(key=lambda x: (-x["job_signals"], x["skill"]))

    return {
        "course": alignment_result.get("course", ""),
        "keep": keep_skills,
        "add_or_strengthen": proposal_skills,
        "has_proposal": len(proposal_skills) > 0,
        "message": (
            "Course currently covers all identified industry-required skills."
            if len(proposal_skills) == 0
            else None
        )
    }


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
            "curriculum_proposal": _build_curriculum_proposal({
                "course": course,
                "skill_demand": [],
                "missing": [],
                "covered": []
            })
        }
    row = row.iloc[0]
    taught = split_skills(row.skills)
    alignment_result = calculate_course_alignment(taught, JOBS)
    alignment_result["course"] = course  # Add course name for proposal builder
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
        "curriculum_proposal": _build_curriculum_proposal(alignment_result)
    }
