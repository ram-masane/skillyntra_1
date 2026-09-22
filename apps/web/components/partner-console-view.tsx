"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
type Course = { id: number; course: string; partner: string };

export default function PartnerConsoleView({ assessment = false }: { assessment?: boolean }) {
  const [step, setStep] = useState(1);
  const [published, setPublished] = useState(false);
  const [course, setCourse] = useState("");
  const [company, setCompany] = useState("");
  const [skills, setSkills] = useState("");
  const [assessmentTitle, setAssessmentTitle] = useState("");
  const [assessmentSkills, setAssessmentSkills] = useState("");
  const [passingScore, setPassingScore] = useState(60);
  const [courseId, setCourseId] = useState(2);
  const [questionText, setQuestionText] = useState("");
  const [questionOptions, setQuestionOptions] = useState("Option A, Option B, Option C, Option D");
  const [correctAnswer, setCorrectAnswer] = useState("Option A");
  const [questionSkill, setQuestionSkill] = useState("");
  const [courses, setCourses] = useState<Course[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!assessment) return;
    fetch(`${API}/api/courses`).then((response) => response.json()).then((items: Course[]) => { setCourses(items); if (items.length > 0) setCourseId(items[0].id); }).catch(() => setError("Published courses could not be loaded."));
  }, [assessment]);
  async function publishCourse() {
    const response = await fetch(`${API}/api/workflow/courses`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: course, partner: company, skills: skills.split(",").map((item) => item.trim()).filter(Boolean), placement_rate: 80, employer_validation: 85 }) });
    if (response.ok) setPublished(true); else setError((await response.json()).detail ?? "Course could not be published.");
  }
  async function saveAssessment() {
    const options = questionOptions.split(",").map((item) => item.trim()).filter(Boolean);
    const response = await fetch(`${API}/api/workflow/assessments`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title: assessmentTitle || "Partner Skill Check", course_id: courseId, passing_score: passingScore, skills: assessmentSkills.split(",").map((item) => item.trim()).filter(Boolean), questions: [{ question: questionText || "Partner skill question", options, answer: correctAnswer, skill: questionSkill || assessmentSkills.split(",")[0]?.trim() || "General" }] }) });
    if (response.ok) setPublished(true); else setError((await response.json()).detail ?? "Assessment could not be published.");
  }
  if (assessment) return <section className="builder-view"><div className="builder-card">{error && <div className="error-box">{error}</div>}<div className="panel-kicker">Assessment authoring</div><h2>Create a company skill check</h2><p>Define the assessment connected to a published course and its evaluated skills.</p><label>Exam title<input value={assessmentTitle} onChange={(event) => setAssessmentTitle(event.target.value)} placeholder="e.g. Data Analytics Partner Skill Check" /></label><label>Course<select value={courseId} onChange={(event) => setCourseId(Number(event.target.value))}>{courses.map((item) => <option value={item.id} key={item.id}>{item.course} · {item.partner}</option>)}</select></label><div className="builder-row"><label>Duration<input type="number" defaultValue="30" /></label><label>Passing score<input type="number" value={passingScore} onChange={(event) => setPassingScore(Number(event.target.value))} /></label></div><label>Skills evaluated<input value={assessmentSkills} onChange={(event) => setAssessmentSkills(event.target.value)} placeholder="Python, SQL, Data Analysis" /></label><label>Question<input value={questionText} onChange={(event) => setQuestionText(event.target.value)} placeholder="e.g. Which library is used for tabular data?" /></label><label>Options<input value={questionOptions} onChange={(event) => setQuestionOptions(event.target.value)} placeholder="Option A, Option B, Option C, Option D" /></label><div className="builder-row"><label>Correct answer<input value={correctAnswer} onChange={(event) => setCorrectAnswer(event.target.value)} /></label><label>Question skill<input value={questionSkill} onChange={(event) => setQuestionSkill(event.target.value)} placeholder="Python" /></label></div><button onClick={saveAssessment} disabled={courses.length === 0}>{published ? "Assessment published" : "Publish assessment"}</button>{published && <div className="success-box">Assessment published and attached to the selected course.</div>}</div></section>;
  return <section className="builder-view"><div className="stepper">{["Information", "Skills", "Modules", "Preview", "Publish"].map((label, index) => <span className={step === index + 1 ? "current" : step > index + 1 ? "done" : ""} key={label}>{index + 1}. {label}</span>)}</div><div className="builder-card"><div className="panel-kicker">Course creation · step {step} of 5</div>{step === 1 && <><h2>Course information</h2><p>Start with the partner course identity students will see in the marketplace.</p><label>Course name<input value={course} onChange={(event) => setCourse(event.target.value)} placeholder="e.g. Applied AI for Manufacturing" /></label><label>Partner company<input value={company} onChange={(event) => setCompany(event.target.value)} placeholder="e.g. Industry Partner" /></label></>}{step === 2 && <><h2>Skills covered</h2><p>Map the course to the skills students and the market can understand.</p><label>Skills<input value={skills} onChange={(event) => setSkills(event.target.value)} placeholder="Python, SQL, Machine Learning" /></label></>}{step === 3 && <><h2>Learning modules</h2><p>Add the learning structure before previewing the course.</p><label>Module 1<input placeholder="Foundations and context" /></label><label>Module 2<input placeholder="Applied project" /></label></>}{step === 4 && <><h2>Preview</h2><div className="preview-card"><strong>{course || "Untitled partner course"}</strong><span>{company || "Partner company"}</span><p>{skills || "Skills will appear here"}</p></div></>}{step === 5 && <><h2>Publish course</h2><p>Review complete. Publishing makes the course available in the partner marketplace.</p><button onClick={publishCourse}>{published ? "Course published" : "Publish course"}</button>{published && <div className="success-box">Course published successfully and is now in the marketplace.</div>}</>}{step < 5 && <button onClick={() => setStep(step + 1)} disabled={step === 1 && (!course || !company)}>Continue</button>}{step > 1 && step < 5 && <button className="secondary-button" onClick={() => setStep(step - 1)}>Back</button>}</div></section>;
}
