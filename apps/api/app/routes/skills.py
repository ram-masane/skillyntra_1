from fastapi import APIRouter

from app.routes.jobs import service
from app.schemas import SkillDemand

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("/demand", response_model=list[SkillDemand])
def skill_demand() -> list[SkillDemand]:
    return [SkillDemand(skill=row.skill, job_signals=int(row.job_signals)) for row in service.skill_demand().itertuples()]
