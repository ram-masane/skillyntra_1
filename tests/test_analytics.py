from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from backend.services.analytics import skill_gap
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
