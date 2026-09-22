from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.course_service import enroll_student, list_courses as stored_courses, list_enrollments

router = APIRouter(prefix="/api/courses", tags=["courses"])
class Course(BaseModel):
    id: int
    course: str
    partner: str
    skills: list[str]
    placement_rate: float
    employer_validation: float


class Enrollment(BaseModel):
    course_id: int
    course: str
    enrolled_at: str


class EnrollmentRequest(BaseModel):
    student_id: str = "demo-student"


@router.get("", response_model=list[Course])
def list_courses() -> list[Course]:
    return [Course(**course) for course in stored_courses()]


@router.get("/enrollments", response_model=list[Enrollment])
def get_enrollments(student_id: str = Query("demo-student", min_length=1)) -> list[Enrollment]:
    return [Enrollment(**enrollment) for enrollment in list_enrollments(student_id)]


@router.post("/{course_id}/enroll", response_model=Enrollment)
def enroll(course_id: int, payload: EnrollmentRequest) -> Enrollment:
    try:
        return Enrollment(**enroll_student(course_id, payload.student_id))
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
