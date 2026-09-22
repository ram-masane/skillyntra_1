from __future__ import annotations

import re
import pandas as pd


def split_skills(value) -> list[str]:
    if pd.isna(value):
        return []
    return [skill.strip() for skill in re.split(r",|;|\|", str(value)) if skill.strip()]


def skill_rows(jobs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, job in jobs.iterrows():
        for skill in split_skills(job.get("skills", "")):
            rows.append({
                "skill": skill,
                "job_id": job.get("job_id", ""),
                "job_title": job.get("job_title", ""),
                "domain": job.get("domain", ""),
                "location": job.get("location", ""),
                "state": job.get("state", ""),
            })
    return pd.DataFrame(rows, columns=["skill", "job_id", "job_title", "domain", "location", "state"])


def skill_demand(jobs: pd.DataFrame) -> pd.DataFrame:
    rows = skill_rows(jobs)
    if rows.empty:
        return pd.DataFrame(columns=["skill", "job_signals"])
    return rows.groupby("skill")["job_id"].nunique().reset_index(name="job_signals").sort_values(
        ["job_signals", "skill"], ascending=[False, True]
    )


def filter_jobs(jobs: pd.DataFrame, search="", career="All", domain="All", city="All", state="All", seniority="All", min_salary=None, max_experience=None) -> pd.DataFrame:
    result = jobs.copy()
    if search:
        searchable = result["job_title"].fillna("") + " " + result["company"].fillna("") + " " + result["skills"].fillna("")
        result = result[searchable.str.contains(search, case=False, na=False)]
    for column, value in [("job_title", career), ("domain", domain), ("location", city), ("state", state), ("seniority", seniority)]:
        if value and value != "All":
            result = result[result[column].eq(value)]
    if min_salary is not None:
        result = result[result["salary_max_lpa"].ge(min_salary)]
    if max_experience is not None:
        result = result[result["experience_min_years"].le(max_experience)]
    return result


def role_skills(jobs: pd.DataFrame, role: str, location="All", limit=8) -> list[str]:
    matching = jobs[jobs["job_title"].eq(role)]
    if location != "All":
        local = matching[matching["location"].eq(location)]
        if not local.empty:
            matching = local
    demand = skill_demand(matching)
    return demand.head(limit)["skill"].tolist()


def career_summary(jobs: pd.DataFrame, role: str, location="All") -> dict:
    matching = jobs[jobs["job_title"].eq(role)]
    if location != "All":
        local = matching[matching["location"].eq(location)]
        if not local.empty:
            matching = local
    if matching.empty:
        return {"jobs": 0, "skills": [], "salary": None, "experience": "-", "locations": []}
    salary = ((matching["salary_min_lpa"] + matching["salary_max_lpa"]) / 2).mean()
    experience = f"{matching['experience_min_years'].min():g}-{matching['experience_max_years'].max():g} years"
    return {
        "jobs": len(matching),
        "skills": skill_demand(matching).head(6)["skill"].tolist(),
        "salary": round(float(salary), 1),
        "experience": experience,
        "locations": matching["location"].value_counts().head(5).index.tolist(),
    }