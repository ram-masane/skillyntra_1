from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.services.analytics import skill_gap, curriculum_alignment

def test_skill_gap():
    matched, missing, readiness = skill_gap(
        ["Python", "SQL", "IoT"],
        ["Python", "SQL"]
    )
    assert matched == ["Python", "SQL"]
    assert missing == ["IoT"]
    assert readiness == 67

def test_curriculum_alignment():
    score, covered, missing = curriculum_alignment(
        ["Python", "SQL"],
        ["Python", "SQL", "IoT"]
    )
    assert score == 67
    assert "IoT" in missing
