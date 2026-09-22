from fastapi import APIRouter, HTTPException, Query

from app.schemas import JobOptions, JobPage, JobRecord, MarketSummary, SkillDemand
from app.services.job_service import JobService, split_skills

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def record(row) -> JobRecord:
    return JobRecord(
        job_id=row.job_id,
        job_title=row.job_title,
        domain=row.domain,
        company=row.company,
        location=row.location,
        state=row.state,
        employment_type=row.employment_type,
        seniority=row.seniority,
        salary_min_lpa=row.salary_min_lpa,
        salary_max_lpa=row.salary_max_lpa,
        experience_min_years=row.experience_min_years,
        experience_max_years=row.experience_max_years,
        job_description=row.job_description,
        skills=split_skills(row.skills),
    )


service = JobService(__import__("pathlib").Path(__file__).resolve().parents[4] / "data" / "jobs.csv")


@router.get("/summary", response_model=MarketSummary)
def summary() -> MarketSummary:
    jobs = service.jobs
    demand = service.skill_demand().head(10)
    return MarketSummary(
        jobs=len(jobs),
        roles=int(jobs.job_title.nunique()),
        skills=int(service.skill_demand().skill.nunique()),
        average_salary_lpa=round(float(((jobs.salary_min_lpa + jobs.salary_max_lpa) / 2).mean()), 1),
        top_skills=[SkillDemand(skill=row.skill, job_signals=int(row.job_signals)) for row in demand.itertuples()],
    )


@router.get("/options", response_model=JobOptions)
def options() -> JobOptions:
    return JobOptions(
        domains=sorted(service.jobs.domain.unique().tolist()),
        locations=sorted(service.jobs.location.unique().tolist()),
        states=sorted(service.jobs.state.unique().tolist()),
        seniorities=sorted(service.jobs.seniority.unique().tolist()),
    )


@router.get("", response_model=JobPage)
def list_jobs(
    search: str = "",
    domain: str = "",
    location: str = "",
    state: str = "",
    seniority: str = "",
    min_salary: float | None = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> JobPage:
    matches = service.filter(search, domain, location, state, seniority, min_salary)
    start = (page - 1) * page_size
    rows = matches.iloc[start:start + page_size]
    return JobPage(items=[record(row) for row in rows.itertuples()], total=len(matches), page=page, page_size=page_size)


@router.get("/{job_id}", response_model=JobRecord)
def get_job(job_id: str) -> JobRecord:
    matches = service.jobs[service.jobs.job_id.eq(job_id)]
    if matches.empty:
        raise HTTPException(status_code=404, detail="Job signal not found")
    row = matches.iloc[0]
    return record(row)
