from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from backend.services.analytics import skill_gap, evidence_scores
from backend.services.course_service import calculate_course_alignment, calculate_course_health


def _jobs(df_data):
    return pd.DataFrame(df_data, columns=["job_id", "skills"])


def test_skill_gap():
    matched, missing, readiness = skill_gap(
        ["Python", "SQL", "IoT"],
        ["Python", "SQL"]
    )
    assert matched == ["Python", "SQL"]
    assert missing == ["IoT"]
    assert readiness == 67


def test_alignment_empty_jobs():
    result = calculate_course_alignment(["Python"], _jobs([]))
    assert result["alignment"] == 0
    assert result["covered"] == []
    assert result["missing"] == []
    assert result["relevant_jobs"] == 0


def test_alignment_no_matching_skills():
    result = calculate_course_alignment(
        ["Python"],
        _jobs([{"job_id": 1, "skills": "Java;C++"}])
    )
    assert result["alignment"] == 0
    assert result["relevant_jobs"] == 0


def test_alignment_partial_coverage():
    result = calculate_course_alignment(
        ["Python"],
        _jobs([
            {"job_id": 1, "skills": "Python;Java"},
            {"job_id": 2, "skills": "Java;C++"},
        ])
    )
    assert result["alignment"] == 50
    assert "Python" in result["covered"]
    assert "Java" in result["missing"]


def test_alignment_full_coverage():
    result = calculate_course_alignment(
        ["Python", "Java"],
        _jobs([
            {"job_id": 1, "skills": "Python;Java"},
        ])
    )
    assert result["alignment"] == 100
    assert sorted(result["covered"]) == ["Java", "Python"]
    assert result["missing"] == []


def test_alignment_demand_weighted():
    result = calculate_course_alignment(
        ["Python", "SQL"],
        _jobs([
            {"job_id": 1, "skills": "Python;SQL;IoT"},
            {"job_id": 2, "skills": "Python;Java"},
            {"job_id": 3, "skills": "SQL;C++"},
        ])
    )
    assert result["alignment"] == 57
    assert "Python" in result["covered"]
    assert "SQL" in result["covered"]
    assert "IoT" in result["missing"]


def test_course_health():
    course = pd.Series({
        "skills": "Python;SQL",
        "placement_rate": 80,
        "employer_validation": 70,
    })
    jobs = _jobs([
        {"job_id": 1, "skills": "Python;SQL;IoT"},
        {"job_id": 2, "skills": "Python;Java"},
        {"job_id": 3, "skills": "SQL;C++"},
    ])
    result = calculate_course_health(course, jobs)
    assert result["score"] == round(0.45 * 57 + 0.30 * 80 + 0.25 * 70)
    assert result["status"] == ("Healthy" if result["score"] >= 75 else "Needs Update" if result["score"] >= 50 else "At Risk")
    assert "Python" in result["covered_skills"]
    assert "SQL" in result["covered_skills"]


def test_course_health_at_risk():
    course = pd.Series({
        "skills": "COBOL",
        "placement_rate": 20,
        "employer_validation": 10,
    })
    jobs = _jobs([
        {"job_id": 1, "skills": "Python;Java"},
    ])
    result = calculate_course_health(course, jobs)
    assert result["alignment"] == 0
    assert result["status"] == "At Risk"


def _ev_demand(skills, signals, confidences):
    return pd.DataFrame({"skill": skills, "job_signals": signals, "confidence": confidences})


def _ev_employer(skills, vals):
    return pd.DataFrame({"skill": skills, "employer_validation": vals})


def test_evidence_scores_normal():
    demand = _ev_demand(["Python", "Java"], [100, 50], ["High", "Medium"])
    employer = _ev_employer(["Python", "Java"], [80, 60])
    result = evidence_scores(demand, employer)
    assert result.iloc[0]["skill"] == "Python"
    assert result.iloc[0]["evidence_score"] == 93.0
    assert result.iloc[1]["skill"] == "Java"
    assert result.iloc[1]["evidence_score"] == 33.0


def test_evidence_scores_empty_demand():
    demand = _ev_demand([], [], [])
    employer = _ev_employer(["Python"], [80])
    result = evidence_scores(demand, employer)
    assert len(result) == 0
    assert "evidence_score" in result.columns


def test_evidence_scores_identical_job_signals():
    demand = _ev_demand(["Python", "Java"], [50, 50], ["High", "Medium"])
    employer = _ev_employer(["Python", "Java"], [80, 60])
    result = evidence_scores(demand, employer)
    assert result.iloc[0]["skill"] == "Python"
    assert result.iloc[0]["evidence_score"] == 70.5
    assert result.iloc[1]["skill"] == "Java"
    assert result.iloc[1]["evidence_score"] == 55.5


def test_evidence_scores_missing_employer_validation():
    demand = _ev_demand(["Python"], [100], ["High"])
    employer = _ev_employer(["Python"], [None])
    result = evidence_scores(demand, employer)
    # single row -> job_signals_norm=50; None -> 50
    # 50*0.45 + 50*0.35 + 100*0.20 = 60.0
    assert result.iloc[0]["evidence_score"] == 60.0


def test_evidence_scores_employer_below_zero():
    demand = _ev_demand(["Python"], [100], ["High"])
    employer = _ev_employer(["Python"], [-20])
    result = evidence_scores(demand, employer)
    # single row -> job_signals_norm=50; -20 clipped to 0
    # 50*0.45 + 0*0.35 + 100*0.20 = 42.5
    assert result.iloc[0]["evidence_score"] == 42.5


def test_evidence_scores_employer_above_100():
    demand = _ev_demand(["Python"], [100], ["High"])
    employer = _ev_employer(["Python"], [150])
    result = evidence_scores(demand, employer)
    # single row -> job_signals_norm=50; 150 clipped to 100
    # 50*0.45 + 100*0.35 + 100*0.20 = 77.5
    assert result.iloc[0]["evidence_score"] == 77.5


def test_evidence_scores_high_confidence():
    demand = _ev_demand(["Python"], [100], ["High"])
    employer = _ev_employer(["Python"], [50])
    result = evidence_scores(demand, employer)
    # 50*0.45 + 50*0.35 + 100*0.20 = 60.0
    assert result.iloc[0]["evidence_score"] == 60.0


def test_evidence_scores_medium_confidence():
    demand = _ev_demand(["Python"], [100], ["Medium"])
    employer = _ev_employer(["Python"], [50])
    result = evidence_scores(demand, employer)
    # 50*0.45 + 50*0.35 + 60*0.20 = 52.0
    assert result.iloc[0]["evidence_score"] == 52.0


def test_evidence_scores_low_confidence():
    demand = _ev_demand(["Python"], [100], ["Low"])
    employer = _ev_employer(["Python"], [50])
    result = evidence_scores(demand, employer)
    # 50*0.45 + 50*0.35 + 35*0.20 = 47.0
    assert result.iloc[0]["evidence_score"] == 47.0


def test_evidence_scores_unknown_confidence():
    demand = _ev_demand(["Python"], [100], ["Unknown"])
    employer = _ev_employer(["Python"], [50])
    result = evidence_scores(demand, employer)
    # unknown -> 60; 50*0.45 + 50*0.35 + 60*0.20 = 52.0
    assert result.iloc[0]["evidence_score"] == 52.0


def test_evidence_scores_bounded_0_to_100():
    demand = _ev_demand(["Python", "Java"], [100, 100], ["High", "Low"])
    employer = _ev_employer(["Python", "Java"], [1000, -50])
    result = evidence_scores(demand, employer)
    assert (result["evidence_score"] <= 100).all()
    assert (result["evidence_score"] >= 0).all()
