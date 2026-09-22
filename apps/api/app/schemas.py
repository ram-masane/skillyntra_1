from pydantic import BaseModel, Field


class JobRecord(BaseModel):
    job_id: str
    job_title: str
    domain: str
    company: str
    location: str
    state: str
    employment_type: str
    seniority: str
    salary_min_lpa: float
    salary_max_lpa: float
    experience_min_years: float
    experience_max_years: float
    job_description: str
    skills: list[str]


class JobPage(BaseModel):
    items: list[JobRecord]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)


class SkillDemand(BaseModel):
    skill: str
    job_signals: int


class MarketSummary(BaseModel):
    jobs: int
    roles: int
    skills: int
    average_salary_lpa: float | None
    top_skills: list[SkillDemand]


class JobOptions(BaseModel):
    domains: list[str]
    locations: list[str]
    states: list[str]
    seniorities: list[str]
