import json
from fastapi import HTTPException

from app.database import connection

DEMO_QUESTIONS = [
    {"question": "Which library is widely used for tabular data in Python?", "options": ["NumPy", "Pandas", "Flask", "Pygame"], "answer": "Pandas", "skill": "Python"},
    {"question": "Which SQL clause filters rows?", "options": ["GROUP BY", "WHERE", "ORDER BY", "AS"], "answer": "WHERE", "skill": "SQL"},
    {"question": "Which chart compares categories most directly?", "options": ["Bar chart", "Scatter only", "Map only", "Gauge only"], "answer": "Bar chart", "skill": "Data Visualization"},
    {"question": "What does KPI stand for?", "options": ["Key Performance Indicator", "Known Python Interface", "Kernel Process Index", "Key Program Input"], "answer": "Key Performance Indicator", "skill": "Data Analysis"},
    {"question": "Which measure is a common average?", "options": ["Mean", "Mode only", "Range only", "Count only"], "answer": "Mean", "skill": "Statistics"},
]


def ensure_demo_assessment() -> int:
    from app.services.course_service import seed_courses
    seed_courses()
    with connection() as db:
        existing = db.execute("SELECT id FROM assessments WHERE title = 'Python for Data Analysis'").fetchone()
        if existing:
            return existing["id"]
        course = db.execute("SELECT id FROM courses WHERE name = 'Data Analytics'").fetchone()
    return create_assessment("Python for Data Analysis", course["id"], 60, [question["skill"] for question in DEMO_QUESTIONS], DEMO_QUESTIONS)["id"]


def create_assessment(title: str, course_id: int, passing_score: int, skills: list[str], questions: list[dict]) -> dict:
    with connection() as db:
        if not db.execute("SELECT id FROM courses WHERE id = ? AND status = 'published'", (course_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Published course not found")
        cursor = db.execute("INSERT INTO assessments (title, course_id, passing_score, skills) VALUES (?, ?, ?, ?)", (title, course_id, passing_score, json.dumps(skills)))
        assessment_id = cursor.lastrowid
        for question in questions:
            db.execute("INSERT INTO assessment_questions (assessment_id, question, options, answer, skill) VALUES (?, ?, ?, ?, ?)", (assessment_id, question["question"], json.dumps(question["options"]), question["answer"], question["skill"]))
    return get_assessment(assessment_id)


def get_assessment(assessment_id: int) -> dict:
    with connection() as db:
        assessment = db.execute(
            """
            SELECT assessments.*, courses.name AS course_name, courses.partner
            FROM assessments JOIN courses ON courses.id = assessments.course_id
            WHERE assessments.id = ?
            """,
            (assessment_id,),
        ).fetchone()
        questions = db.execute("SELECT * FROM assessment_questions WHERE assessment_id = ? ORDER BY id", (assessment_id,)).fetchall()
    if not assessment:
        return {}
    return {**dict(assessment), "skills": json.loads(assessment["skills"]), "questions": [{**dict(q), "options": json.loads(q["options"]), "answer": None} for q in questions]}


def grade_assessment(assessment_id: int, student_id: str, answers: dict[int, str]) -> dict:
    with connection() as db:
        assessment = db.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,)).fetchone()
        if assessment is None:
            raise HTTPException(status_code=404, detail="Assessment not found")
        if not db.execute(
            "SELECT 1 FROM course_enrollments WHERE student_id = ? AND course_id = ?",
            (student_id, assessment["course_id"]),
        ).fetchone():
            raise HTTPException(status_code=403, detail="Enroll in the course before taking this assessment")
        questions = db.execute("SELECT * FROM assessment_questions WHERE assessment_id = ? ORDER BY id", (assessment_id,)).fetchall()
        correct = [q for q in questions if answers.get(q["id"]) == q["answer"]]
        score = round(len(correct) / max(1, len(questions)) * 100)
        passed = score >= assessment["passing_score"]
        demonstrated = [q["skill"] for q in correct]
        improvement = [q["skill"] for q in questions if answers.get(q["id"]) != q["answer"]]
        if passed:
            for skill in demonstrated:
                db.execute("INSERT OR IGNORE INTO skill_validations (student_id, skill, assessment_id, score, validated_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)", (student_id, skill, assessment_id, score))
    return {"score": score, "passed": passed, "demonstrated": demonstrated, "improvement": improvement}