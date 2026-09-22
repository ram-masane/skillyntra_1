from __future__ import annotations

import pandas as pd

from apps.api.app.services.job_service import split_skills, JobService


def skill_demand(jobs: pd.DataFrame) -> pd.DataFrame:
    return JobService.__new__(JobService).skill_demand(jobs)


def get_relevant_jobs_for_course(course_skills: list[str], jobs: pd.DataFrame) -> pd.DataFrame:
    """
    Find jobs that are relevant to a course based on skill overlap.
    
    A job is relevant if it requires at least one skill taught in the course.
    This ensures alignment is measured against relevant industry demand,
    not the entire dataset.
    """
    if not course_skills:
        return pd.DataFrame(columns=jobs.columns)
    
    course_skills_lower = {s.lower() for s in course_skills}
    
    def has_overlap(skills_str: str) -> bool:
        job_skills = {s.lower() for s in split_skills(skills_str)}
        return bool(course_skills_lower & job_skills)
    
    mask = jobs["skills"].apply(has_overlap)
    return jobs[mask]


def calculate_course_alignment(course_skills: list[str], jobs: pd.DataFrame) -> dict:
    """
    Calculate course alignment against relevant industry demand.
    
    Process:
    1. Find jobs relevant to the course (skill overlap)
    2. Calculate skill demand from those relevant jobs
    3. Compare course skills to demanded skills
    4. Alignment = covered_demand_signals / total_demand_signals * 100
    
    Returns dict with: alignment (0-100), covered_skills, missing_skills, relevant_job_count
    """
    taught = course_skills
    if not taught:
        return {"alignment": 0, "covered": [], "missing": [], "relevant_jobs": 0, "required_skills": []}
    
    # Get jobs relevant to this course
    relevant_jobs = get_relevant_jobs_for_course(taught, jobs)
    if relevant_jobs.empty:
        return {"alignment": 0, "covered": [], "missing": [], "relevant_jobs": 0, "required_skills": []}
    
    # Calculate skill demand from relevant jobs only
    demand = skill_demand(relevant_jobs)
    if demand.empty:
        return {"alignment": 0, "covered": [], "missing": [], "relevant_jobs": len(relevant_jobs), "required_skills": []}
    
    # Compare course skills to demanded skills
    taught_norm = {skill.lower() for skill in taught}
    required_skills = demand["skill"].tolist()
    
    covered = [skill for skill in required_skills if skill.lower() in taught_norm]
    missing = [skill for skill in required_skills if skill.lower() not in taught_norm]
    
    # Alignment = sum of demand signals for covered skills / total demand signals * 100
    demand_map = dict(zip(demand["skill"].str.lower(), demand["job_signals"]))
    covered_signals = sum(demand_map.get(skill.lower(), 0) for skill in covered)
    total_signals = max(1, int(demand["job_signals"].sum()))
    alignment = round(covered_signals / total_signals * 100)
    
    return {
        "alignment": min(100, alignment),
        "covered": covered,
        "missing": missing,
        "relevant_jobs": len(relevant_jobs),
        "required_skills": required_skills
    }


def calculate_course_health(course: pd.Series, jobs: pd.DataFrame) -> dict:
    """
    Calculate overall course health score.
    
    Inputs (all on 0-100 scale):
    - alignment: skill coverage of relevant industry demand (45% weight)
    - placement_rate: historical placement rate from course data (30% weight)
    - employer_validation: employer validation score from course data (25% weight)
    
    Weights sum to 100%. All inputs are already on comparable 0-100 scale.
    
    Returns dict with: alignment, placement, employer, score, status, skills
    """
    taught = split_skills(course.get("skills", ""))
    alignment_result = calculate_course_alignment(taught, jobs)
    alignment = alignment_result["alignment"]
    placement = float(course.get("placement_rate", 0))
    employer = float(course.get("employer_validation", 0))
    
    # Composite score with documented weights
    # alignment 45%: how well course covers relevant market demand
    # placement 30%: historical placement outcomes
    # employer 25%: employer validation of course relevance
    score = round(0.45 * alignment + 0.30 * placement + 0.25 * employer)
    
    status = "Healthy" if score >= 75 else "Needs Update" if score >= 50 else "At Risk"
    
    return {
        "alignment": alignment,
        "placement": placement,
        "employer": employer,
        "score": score,
        "status": status,
        "skills": taught,
        "covered_skills": alignment_result["covered"],
        "missing_skills": alignment_result["missing"],
        "relevant_jobs": alignment_result["relevant_jobs"]
    }