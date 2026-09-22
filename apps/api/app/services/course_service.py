import json
from pathlib import Path

import pandas as pd

from app.database import connection
from app.services.job_service import split_skills


def seed_courses() -> None:
    source = pd.read_csv(Path(__file__).resolve().parents[4] / "data" / "courses.csv")
    with connection() as db:
        for row in source.itertuples():
            db.execute(
                "INSERT OR IGNORE INTO courses (name, partner, skills, placement_rate, employer_validation) VALUES (?, ?, ?, ?, ?)",
                (row.course, row.institute, json.dumps(split_skills(row.skills)), row.placement_rate, row.employer_validation),
            )


def list_courses() -> list[dict]:
    seed_courses()
    with connection() as db:
        rows = db.execute("SELECT * FROM courses WHERE status = 'published' ORDER BY id").fetchall()
    return [{**dict(row), "course": row["name"], "skills": json.loads(row["skills"])} for row in rows]


def list_enrollments(student_id: str) -> list[dict]:
    with connection() as db:
        rows = db.execute(
            """
            SELECT course_enrollments.course_id, courses.name, course_enrollments.enrolled_at
            FROM course_enrollments
            JOIN courses ON courses.id = course_enrollments.course_id
            WHERE course_enrollments.student_id = ?
            ORDER BY course_enrollments.enrolled_at DESC, course_enrollments.id DESC
            """,
            (student_id,),
        ).fetchall()
    return [{"course_id": row["course_id"], "course": row["name"], "enrolled_at": row["enrolled_at"]} for row in rows]


def enroll_student(course_id: int, student_id: str) -> dict:
    seed_courses()
    with connection() as db:
        course = db.execute("SELECT id, name FROM courses WHERE id = ? AND status = 'published'", (course_id,)).fetchone()
        if course is None:
            raise ValueError("Course not found")
        db.execute(
            "INSERT OR IGNORE INTO course_enrollments (student_id, course_id) VALUES (?, ?)",
            (student_id, course_id),
        )
        enrollment = db.execute(
            "SELECT course_id, enrolled_at FROM course_enrollments WHERE student_id = ? AND course_id = ?",
            (student_id, course_id),
        ).fetchone()
    return {"course_id": enrollment["course_id"], "course": course["name"], "enrolled_at": enrollment["enrolled_at"]}


def create_course(name: str, partner: str, skills: list[str], placement_rate: float = 0, employer_validation: float = 0) -> dict:
    with connection() as db:
        cursor = db.execute(
            "INSERT INTO courses (name, partner, skills, placement_rate, employer_validation, status) VALUES (?, ?, ?, ?, ?, 'published')",
            (name, partner, json.dumps(skills), placement_rate, employer_validation),
        )
        return {"id": cursor.lastrowid, "course": name, "partner": partner, "skills": skills, "placement_rate": placement_rate, "employer_validation": employer_validation, "status": "published"}