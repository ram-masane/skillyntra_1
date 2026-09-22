"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { BadgeCheck, Clock3, Sparkles } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
type Course = { id: number; course: string; partner: string; skills: string[]; placement_rate: number; employer_validation: number };
type Enrollment = { course_id: number; course: string; enrolled_at: string };
type Assessment = { id: number; title: string; course_id: number; partner: string; passing_score: number; skills: string[] };

export default function CoursesView() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [enrolled, setEnrolled] = useState<number[]>([]);
  const [assessments, setAssessments] = useState<Record<number, Assessment[]>>({});
  const [enrolling, setEnrolling] = useState<number | null>(null);
  const [error, setError] = useState("");
  const searchParams = useSearchParams();
  const missing = (searchParams.get("missing") ?? "").split(",").map((skill) => skill.trim().toLowerCase()).filter(Boolean);
  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/courses`),
      fetch(`${API}/api/courses/enrollments?student_id=demo-student`),
    ])
      .then(async ([coursesResponse, enrollmentsResponse]) => {
        if (!coursesResponse.ok || !enrollmentsResponse.ok) throw new Error();
        const loadedCourses: Course[] = await coursesResponse.json();
        const enrollments: Enrollment[] = await enrollmentsResponse.json();
        setCourses(loadedCourses);
        setEnrolled(enrollments.map((enrollment) => enrollment.course_id));
        await Promise.all(enrollments.map(async (enrollment) => {
          const response = await fetch(`${API}/api/assessments?course_id=${enrollment.course_id}&student_id=demo-student`);
          if (response.ok) {
            const items: Assessment[] = await response.json();
            setAssessments((current) => ({ ...current, [enrollment.course_id]: items }));
          }
        }));
      })
      .catch(() => setError("Partner courses could not be loaded."));
  }, []);

  async function enroll(courseId: number) {
    setEnrolling(courseId);
    setError("");
    try {
      const response = await fetch(`${API}/api/courses/${courseId}/enroll`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: "demo-student" }),
      });
      if (!response.ok) throw new Error();
      setEnrolled((current) => current.includes(courseId) ? current : [...current, courseId]);
      const assessmentsResponse = await fetch(`${API}/api/assessments?course_id=${courseId}&student_id=demo-student`);
      if (assessmentsResponse.ok) {
        const items: Assessment[] = await assessmentsResponse.json();
        setAssessments((current) => ({ ...current, [courseId]: items }));
      }
    } catch {
      setError("Enrollment could not be saved. Please try again.");
    } finally {
      setEnrolling(null);
    }
  }

  const rankedCourses = [...courses].sort((left, right) => {
    const score = (course: Course) => course.skills.filter((skill) => missing.includes(skill.toLowerCase())).length;
    return score(right) - score(left);
  });
  return <section className="courses-view">{missing.length > 0 && <div className="section-banner"><Sparkles size={18} /><span>Recommended for your gap: courses are ranked by how many missing skills they cover.</span></div>}{error && <div className="error-box">{error}</div>}<div className="course-grid">{rankedCourses.map((course) => { const isEnrolled = enrolled.includes(course.id); const covered = course.skills.filter((skill) => missing.includes(skill.toLowerCase())); const courseAssessments = assessments[course.id] ?? []; return <article className="market-course" key={course.id}><div className="course-top"><span><Sparkles size={14} /> Industry aligned</span><BadgeCheck size={19} color="#4b9b63" /></div><h2>{course.course}</h2><p className="course-partner">by {course.partner}</p>{missing.length > 0 && <p className="course-partner">Recommended because it covers {covered.length} of {missing.length} missing skills{covered.length > 0 ? `: ${covered.join(", ")}` : ""}.</p>}<div className="course-skills">{course.skills.map((skill) => <span key={skill}>{skill}</span>)}</div><div className="course-data"><span><Clock3 size={14} /> Partner programme</span><strong>{course.placement_rate}% placement relevance</strong></div><button className={isEnrolled ? "enrolled" : ""} disabled={isEnrolled || enrolling === course.id} onClick={() => enroll(course.id)}>{isEnrolled ? "Enrolled" : enrolling === course.id ? "Saving..." : "Enroll in course"}</button>{isEnrolled && <div className="course-followup">{courseAssessments.length > 0 ? courseAssessments.map((assessment) => <Link key={assessment.id} href={`/student/assessments?assessment_id=${assessment.id}&course_id=${course.id}`}>Take {assessment.title} <span>with {assessment.partner}</span></Link>) : <span>Partner assessment will appear here when published.</span>}</div>}</article>; })}</div>{courses.length === 0 && !error && <div className="loading-box">Loading partner courses...</div>}</section>;
}
