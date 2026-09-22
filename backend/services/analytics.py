from pathlib import Path
import pandas as pd

from backend.services.job_service import skill_demand

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "data"

def load_data():
    jobs = pd.read_csv(DATA / "jobs.csv")
    employer = pd.read_csv(DATA / "employer_feedback.csv")
    growth = pd.read_csv(DATA / "sector_growth.csv")
    placements = pd.read_csv(DATA / "placements.csv")
    capacity = pd.read_csv(DATA / "training_capacity.csv")
    courses = pd.read_csv(DATA / "courses.csv")
    return jobs, employer, growth, placements, capacity, courses

def role_requirements(jobs, role, district=None):
    role_column = "job_title" if "job_title" in jobs.columns else "role"
    location_column = "location" if "location" in jobs.columns else "district"
    x = jobs[jobs[role_column].eq(role)].copy()
    if district and district != "All":
        local = x[x[location_column].eq(district)]
        if not local.empty:
            x = local
    if x.empty:
        return []
    skills = x["skills"].fillna("").str.replace(";", ",", regex=False).str.split(",").explode()
    return sorted({skill.strip() for skill in skills if skill.strip()})

def evidence_scores(demand, employer):
    """
    Calculate evidence scores combining job demand, employer validation, and confidence.
    
    All inputs are normalized to 0-100 scale before weighting:
    - job_signals: min-max normalized to 0-100
    - employer_validation: already 0-100
    - confidence: High=100, Medium=60, Low=35 (mapped to 0-100 scale)
    
    Weights: job_signals 45%, employer_validation 35%, confidence 20%
    """
    m = demand.merge(employer, on="skill", how="left")
    m["employer_validation"] = m["employer_validation"].fillna(50)
    
    # Normalize job_signals to 0-100 using min-max scaling
    job_signals = m["job_signals"]
    if job_signals.max() > job_signals.min():
        job_signals_norm = (job_signals - job_signals.min()) / (job_signals.max() - job_signals.min()) * 100
    else:
        job_signals_norm = pd.Series(50, index=job_signals.index)  # Default to middle if all same
    
    confidence_map = {"High": 100, "Medium": 60, "Low": 35}
    confidence_norm = m["confidence"].map(confidence_map).fillna(60)
    
    m["evidence_score"] = (
        job_signals_norm * 0.45
        + m["employer_validation"] * 0.35
        + confidence_norm * 0.20
    ).round(1)
    return m.sort_values("evidence_score", ascending=False)

def skill_gap(required, current):
    current_norm = {x.strip().lower() for x in current}
    matched, missing = [], []
    for s in required:
        (matched if s.lower() in current_norm else missing).append(s)
    readiness = round(100 * len(matched) / max(1, len(required)))
    return matched, missing, readiness

def curriculum_alignment(course_skills, demand_skills):
    cs_norm = {x.strip().lower() for x in course_skills}
    ds_original = {x.strip(): x.strip().lower() for x in demand_skills}
    covered = [orig for orig, norm in ds_original.items() if norm in cs_norm]
    missing = [orig for orig, norm in ds_original.items() if norm not in cs_norm]
    score = round(100 * len(covered) / max(1, len(ds_original)))
    return score, sorted(covered), sorted(missing)

def district_gaps(capacity):
    x = capacity.copy()
    x["gap"] = x["estimated_demand"] - x["annual_capacity"]
    x["status"] = x["gap"].apply(lambda v: "SHORTAGE" if v > 0 else ("POTENTIAL OVERSUPPLY" if v < 0 else "BALANCED"))
    return x.sort_values("gap", ascending=False)

def course_health(courses, demand_map):
    rows = []
    for _, r in courses.iterrows():
        skills = r["skills"].split(";")
        demand_hits = sum(demand_map.get(s, 0) for s in skills)
        alignment = min(100, round(demand_hits * 12))
        placement = float(r["placement_rate"])
        employer = float(r["employer_validation"])
        health = round(0.45*alignment + 0.30*placement + 0.25*employer)
        rows.append([r["course"], alignment, placement, employer, health])
    return pd.DataFrame(rows, columns=["course","alignment","placement","employer_validation","health_score"]).sort_values("health_score", ascending=False)
