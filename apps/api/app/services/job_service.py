from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {
    "job_id", "job_title", "domain", "company", "location", "state",
    "employment_type", "seniority", "salary_min_lpa", "salary_max_lpa",
    "experience_min_years", "experience_max_years", "job_description", "skills",
}


def split_skills(value: object) -> list[str]:
    return [skill.strip() for skill in re.split(r",|;|\|", str(value or "")) if skill.strip()]


class JobService:
    def __init__(self, csv_path: Path):
        self.jobs = pd.read_csv(csv_path)
        missing = REQUIRED_COLUMNS.difference(self.jobs.columns)
        if missing:
            raise ValueError(f"jobs.csv is missing columns: {sorted(missing)}")
        if self.jobs["job_id"].isna().any() or self.jobs["job_id"].duplicated().any():
            raise ValueError("jobs.csv must contain unique, non-empty job_id values")
        numeric = ["salary_min_lpa", "salary_max_lpa", "experience_min_years", "experience_max_years"]
        for column in numeric:
            self.jobs[column] = pd.to_numeric(self.jobs[column], errors="raise")

    def filter(self, search: str = "", domain: str = "", location: str = "", state: str = "", seniority: str = "", min_salary: float | None = None) -> pd.DataFrame:
        result = self.jobs
        if search:
            text = result["job_title"] + " " + result["company"] + " " + result["skills"]
            result = result[text.str.contains(search, case=False, na=False)]
        for column, value in (("domain", domain), ("location", location), ("state", state), ("seniority", seniority)):
            if value:
                result = result[result[column].eq(value)]
        if min_salary is not None:
            result = result[result["salary_max_lpa"].ge(min_salary)]
        return result

    def skill_demand(self, jobs: pd.DataFrame | None = None) -> pd.DataFrame:
        source = self.jobs if jobs is None else jobs
        rows = [(skill, job.job_id) for job in source.itertuples() for skill in split_skills(job.skills)]
        demand = pd.DataFrame(rows, columns=["skill", "job_id"])
        if demand.empty:
            return pd.DataFrame(columns=["skill", "job_signals"])
        return demand.groupby("skill")["job_id"].nunique().reset_index(name="job_signals").sort_values(["job_signals", "skill"], ascending=[False, True])
