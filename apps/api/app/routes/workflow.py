import sqlite3

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.database import connection
from app.services.assessment_service import create_assessment, get_assessment, grade_assessment
from app.services.course_service import create_course, list_courses

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


class CourseInput(BaseModel):
    name: str
    partner: str
    skills: list[str] = Field(min_length=1)
    placement_rate: float = 0
    employer_validation: float = 0


class AssessmentInput(BaseModel):
    title: str
    course_id: int
    passing_score: int = Field(ge=1, le=100)
    skills: list[str] = Field(min_length=1)
    questions: list[dict] = Field(min_length=1)


class GradeInput(BaseModel):
    student_id: str = "demo-student"
    answers: dict[int, str]


@router.get("/courses")
def courses() -> list[dict]:
    return list_courses()


@router.post("/courses")
def save_course(payload: CourseInput) -> dict:
    try:
        return create_course(payload.name, payload.partner, payload.skills, payload.placement_rate, payload.employer_validation)
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="A course with this name already exists") from error


@router.post("/assessments")
def save_assessment(payload: AssessmentInput) -> dict:
    return create_assessment(payload.title, payload.course_id, payload.passing_score, payload.skills, payload.questions)


@router.get("/assessments/{assessment_id}")
def assessment(assessment_id: int) -> dict:
    return get_assessment(assessment_id)


@router.post("/assessments/{assessment_id}/grade")
def grade(assessment_id: int, payload: GradeInput) -> dict:
    return grade_assessment(assessment_id, payload.student_id, payload.answers)


@router.get("/skills/{student_id}")
def validated_skills(student_id: str) -> list[dict]:
    with connection() as db:
        rows = db.execute(
            """
            SELECT skill_validations.id, skill_validations.skill, skill_validations.score,
                   skill_validations.status, skill_validations.validated_at,
                   assessments.title AS assessment, courses.name AS course, courses.partner
            FROM skill_validations
            JOIN assessments ON assessments.id = skill_validations.assessment_id
            JOIN courses ON courses.id = assessments.course_id
            WHERE skill_validations.student_id = ? ORDER BY skill_validations.id DESC
            """,
            (student_id,),
        ).fetchall()
    return [dict(row) for row in rows]