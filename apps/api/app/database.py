from pathlib import Path
import sqlite3

BASE = Path(__file__).resolve().parents[3]
DB_PATH = BASE / "data" / "skillyntra.db"


def connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def init_db() -> None:
    with connection() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                partner TEXT NOT NULL,
                skills TEXT NOT NULL,
                placement_rate REAL NOT NULL DEFAULT 0,
                employer_validation REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'published'
            );
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                course_id INTEGER NOT NULL,
                passing_score INTEGER NOT NULL,
                skills TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'published',
                FOREIGN KEY(course_id) REFERENCES courses(id)
            );
            CREATE TABLE IF NOT EXISTS assessment_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                options TEXT NOT NULL,
                answer TEXT NOT NULL,
                skill TEXT NOT NULL,
                FOREIGN KEY(assessment_id) REFERENCES assessments(id)
            );
            CREATE TABLE IF NOT EXISTS skill_validations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                skill TEXT NOT NULL,
                assessment_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                validated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'Industry Validated',
                UNIQUE(student_id, skill, assessment_id)
            );
            CREATE TABLE IF NOT EXISTS course_enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                course_id INTEGER NOT NULL,
                enrolled_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_id, course_id),
                FOREIGN KEY(course_id) REFERENCES courses(id)
            );
            """
        )
        validation_columns = {row["name"] for row in db.execute("PRAGMA table_info(skill_validations)")}
        if "validated_at" not in validation_columns:
            db.execute("ALTER TABLE skill_validations ADD COLUMN validated_at TEXT")
            db.execute("UPDATE skill_validations SET validated_at = CURRENT_TIMESTAMP WHERE validated_at IS NULL")


init_db()