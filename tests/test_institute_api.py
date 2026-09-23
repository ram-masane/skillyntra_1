from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

import pandas as pd

from app.routes.institute import alignment
from backend.services.course_service import calculate_course_health


def _jobs(df_data):
    return pd.DataFrame(df_data, columns=["job_id", "skills"])


def test_institute_alignment_exposes_health_fields():
    result = alignment("Data Analytics")
    # Existing fields preserved
    assert "course" in result
    assert "taught" in result
    assert "required" in result
    assert "missing" in result
    assert "alignment" in result
    assert "status" in result
    # New health fields
    assert "covered" in result
    assert "placement_rate" in result
    assert "employer_validation" in result
    assert "health_score" in result
    assert "health_status" in result


def test_institute_alignment_covered_only_demanded_and_taught():
    result = alignment("Data Analytics")
    taught_lower = {s.lower() for s in result["taught"]}
    for skill in result["covered"]:
        assert skill.lower() in taught_lower, f"covered skill {skill} not taught by course"


def test_institute_alignment_required_is_industry_demand():
    result = alignment("Data Analytics")
    assert isinstance(result["required"], list)
    assert len(result["required"]) > 0


def test_institute_alignment_missing_is_required_not_covered():
    result = alignment("Data Analytics")
    covered_lower = {s.lower() for s in result["covered"]}
    for skill in result["missing"]:
        assert skill.lower() not in covered_lower, f"missing skill {skill} is covered"


def test_institute_alignment_missing_and_required_consistent():
    result = alignment("Data Analytics")
    covered_lower = {s.lower() for s in result["covered"]}
    required_lower = {s.lower() for s in result["required"]}
    missing_lower = {s.lower() for s in result["missing"]}
    # Every required skill is either covered or missing
    assert required_lower == covered_lower | missing_lower


def test_institute_alignment_health_score_matches_canonical():
    result = alignment("Data Analytics")
    row = pd.Series({
        "skills": "Python;SQL;Power BI;Statistics",
        "placement_rate": 70,
        "employer_validation": 82,
    })
    jobs = pd.read_csv(Path(__file__).resolve().parents[1] / "data" / "jobs.csv")
    health = calculate_course_health(row, jobs)
    assert result["health_score"] == health["score"]
    assert result["health_status"] == health["status"]


def test_institute_alignment_status_thresholds_unchanged():
    # Healthy >= 75, Needs Update >= 50, At Risk < 50
    result = alignment("Data Analytics")
    score = result["health_score"]
    expected = "Healthy" if score >= 75 else "Needs Update" if score >= 50 else "At Risk"
    assert result["health_status"] == expected


def test_institute_alignment_unknown_course_safe():
    result = alignment("Nonexistent Course")
    assert result["course"] == "Nonexistent Course"
    assert result["taught"] == []
    assert result["required"] == []
    assert result["missing"] == []
    assert result["covered"] == []
    assert result["alignment"] == 0
    assert result["placement_rate"] == 0
    assert result["employer_validation"] == 0
    assert result["health_score"] == 0
    assert result["health_status"] == "At Risk"
    assert result["status"] == "At Risk"


def test_institute_alignment_another_course():
    result = alignment("Industrial IoT")
    assert result["course"] == "Industrial IoT"
    assert "covered" in result
    assert "health_score" in result
    assert "health_status" in result
    assert "placement_rate" in result
    assert "employer_validation" in result