import json

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.database import connection
from app.services.assessment_service import ensure_demo_assessment, get_assessment, grade_assessment

router = APIRouter(prefix="/api/assessments", tags=["assessments"])

class AnswerSheet(BaseModel):
    answers: dict[int, str]


@router.get("")
def list_assessments(course_id: int | None = Query(default=None), student_id: str = Query(default="demo-student")) -> list[dict]:
    if course_id is not None:
        with connection() as db:
            course = db.execute("SELECT name FROM courses WHERE id = ?", (course_id,)).fetchone()
        if course and course["name"] == "Data Analytics":
            ensure_demo_assessment()
    with connection() as db:
        query = """
            SELECT assessments.id, assessments.title, assessments.course_id, assessments.passing_score,
                   assessments.skills, courses.name AS course_name, courses.partner
            FROM assessments JOIN courses ON courses.id = assessments.course_id
            JOIN course_enrollments ON course_enrollments.course_id = assessments.course_id
            WHERE course_enrollments.student_id = ?
        """
        params: list[object] = [student_id]
        if course_id is not None:
            query += " AND assessments.course_id = ?"
            params.append(course_id)
        query += " ORDER BY assessments.id DESC"
        rows = db.execute(query, params).fetchall()
    return [{**dict(row), "skills": json.loads(row["skills"])} for row in rows]


@router.get("/demo")
def get_demo_assessment() -> dict:
    assessment_id = ensure_demo_assessment()
    assessment = get_assessment(assessment_id)
    return {"id": assessment_id, "title": assessment["title"], "duration_minutes": 5, "passing_score": assessment["passing_score"], "questions": assessment["questions"]}


@router.post("/demo/grade")
def grade_demo(sheet: AnswerSheet) -> dict:
    return grade_assessment(ensure_demo_assessment(), "demo-student", sheet.answers)
