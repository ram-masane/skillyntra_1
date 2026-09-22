from fastapi import APIRouter, Query

from app.routes.jobs import service

router = APIRouter(prefix="/api/careers", tags=["careers"])


@router.get("/roles", response_model=list[str])
def roles() -> list[str]:
    return sorted(service.jobs.job_title.unique().tolist())


@router.get("/{role}")
def career_summary(role: str, location: str = "") -> dict:
    matches = service.jobs[service.jobs.job_title.eq(role)]
    if location:
        local = matches[matches.location.eq(location)]
        if not local.empty:
            matches = local
    demand = service.skill_demand(matches).head(8)
    if matches.empty:
        return {"role": role, "jobs": 0, "required_skills": [], "average_salary_lpa": None, "experience": "-", "locations": []}
    midpoint = ((matches.salary_min_lpa + matches.salary_max_lpa) / 2).mean()
    return {
        "role": role,
        "jobs": len(matches),
        "required_skills": demand.skill.tolist(),
        "average_salary_lpa": round(float(midpoint), 1),
        "experience": f"{matches.experience_min_years.min():g}-{matches.experience_max_years.max():g} years",
        "locations": matches.location.value_counts().head(5).index.tolist(),
    }


@router.get("/{role}/gap")
def career_gap(role: str, known_skills: list[str] = Query(default=[]), location: str = "") -> dict:
    summary = career_summary(role, location)
    known = {skill.strip().lower() for skill in known_skills}
    matched = [skill for skill in summary["required_skills"] if skill.lower() in known]
    missing = [skill for skill in summary["required_skills"] if skill.lower() not in known]
    readiness = round(len(matched) / max(1, len(summary["required_skills"])) * 100)
    return {**summary, "matched": matched, "missing": missing, "readiness": readiness}
