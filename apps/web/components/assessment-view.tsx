"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { CheckCircle2, CircleAlert } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
type Question = { id: number; question: string; options: string[]; skill: string };
type Assessment = { id: number; title: string; course_id: number; course_name: string; partner: string; passing_score: number; skills: string[]; questions?: Question[] };
type Result = { score: number; passed: boolean; demonstrated: string[]; improvement: string[] };

export default function AssessmentView() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [available, setAvailable] = useState<Assessment[]>([]);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState("");
  const searchParams = useSearchParams();
  const assessmentId = searchParams.get("assessment_id");
  const courseId = searchParams.get("course_id");
  useEffect(() => {
    const query = courseId ? `&course_id=${courseId}` : "";
    fetch(`${API}/api/assessments?student_id=demo-student${query}`)
      .then((response) => { if (!response.ok) throw new Error(); return response.json(); })
      .then((items: Assessment[]) => {
        setAvailable(items);
        const selected = items.find((item) => String(item.id) === assessmentId) ?? items[0];
        if (!selected) return;
        return fetch(`${API}/api/workflow/assessments/${selected.id}`).then((response) => { if (!response.ok) throw new Error(); return response.json(); }).then((data) => { setAssessment(data); setQuestions(data.questions); });
      })
      .catch(() => setError("No enrolled partner assessment could be loaded. Enroll in a course first."));
  }, [assessmentId, courseId]);
  async function submit() {
    if (!assessment) return;
    const response = await fetch(`${API}/api/workflow/assessments/${assessment.id}/grade`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ student_id: "demo-student", answers }) });
    if (response.ok) setResult(await response.json()); else setError((await response.json()).detail ?? "Assessment could not be submitted.");
  }
  return <section className="assessment-view">{error && <div className="error-box">{error}</div>}{available.length > 1 && <label className="wide-select">Choose partner assessment<select value={assessment?.id ?? ""} onChange={(event) => { const next = available.find((item) => item.id === Number(event.target.value)); if (next) window.location.href = `/student/assessments?assessment_id=${next.id}&course_id=${next.course_id}`; }}>{available.map((item) => <option value={item.id} key={item.id}>{item.title} · {item.partner}</option>)}</select></label>}{result ? <div className={result.passed ? "result-box pass" : "result-box fail"}><div className="result-icon">{result.passed ? <CheckCircle2 /> : <CircleAlert />}</div><div className="panel-kicker">Industry validation result</div><h2>{result.score}% · {result.passed ? "Passed" : "Needs another attempt"}</h2><p>{result.passed ? `${assessment?.title} by ${assessment?.partner} is now an Industry Validated skill signal.` : "Review the improvement areas and try again."}</p><div className="result-columns"><div><b>Skills demonstrated</b>{result.demonstrated.map((skill) => <span key={skill}>{skill}</span>)}</div><div><b>Needs improvement</b>{result.improvement.map((skill) => <span key={skill}>{skill}</span>)}</div></div><button onClick={() => { setResult(null); setAnswers({}); }}>Retake assessment</button></div> : assessment ? <div className="assessment-card"><div className="panel-kicker">Company assessment · {assessment.partner}</div><h2>{assessment.title}</h2><p>{assessment.course_name} · Passing score {assessment.passing_score}%</p>{questions.map((question) => <fieldset key={question.id}><legend>{question.id}. {question.question}</legend>{question.options.map((option) => <label key={option}><input type="radio" name={`question-${question.id}`} checked={answers[question.id] === option} onChange={() => setAnswers((current) => ({ ...current, [question.id]: option }))} />{option}</label>)}</fieldset>)}<button disabled={Object.keys(answers).length !== questions.length} onClick={submit}>Submit assessment</button></div> : !error && <div className="loading-box">Loading enrolled partner assessments...</div>}</section>;
}
