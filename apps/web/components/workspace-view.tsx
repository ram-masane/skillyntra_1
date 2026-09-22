"use client";

import { useEffect, useState } from "react";
import { ArrowRight, CheckCircle2, Download, FileBarChart, Gauge, Users } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
type Skill = { skill: string; job_signals: number };
type Validation = { id: number; skill: string; score: number; status: string; validated_at: string; assessment: string; course: string; partner: string };
type District = { district: string; priority_skill: string; demand: number; capacity: number; gap: number; status: string };

const copy: Record<string, { title: string; description: string; kicker: string }> = {
  "skill-intelligence": { title: "Skill Intelligence", description: "See which skills repeat across the 1,200 synthetic job signals and compare demand by market slice.", kicker: "Demand evidence" },
  "my-skills": { title: "My Skills", description: "Your durable validation record lives here after a company assessment is passed.", kicker: "Student evidence" },
  students: { title: "Students", description: "Review the learner pipeline connected to published partner courses and assessments.", kicker: "Talent pipeline" },
  analytics: { title: "Company Analytics", description: "Track published learning, assessment readiness, and the skills your partner workspace validates.", kicker: "Partner intelligence" },
  "course-health": { title: "Course Health", description: "Compare course alignment, placement relevance, and employer validation to prioritize updates.", kicker: "Institute intelligence" },
  "industry-demand": { title: "Industry Demand", description: "Use current job signals to understand the capabilities your curriculum should cover.", kicker: "Demand evidence" },
  recommendations: { title: "Recommendations", description: "Turn missing market skills into clear curriculum actions for the next programme revision.", kicker: "Action queue" },
  "skill-demand": { title: "Skill Demand", description: "Rank the skills appearing most often across the primary labour-market dataset.", kicker: "Government intelligence" },
  "training-capacity": { title: "Training Capacity", description: "Compare district capacity with observed demand and identify where expansion is needed.", kicker: "Capacity planning" },
  reports: { title: "Reports", description: "Prepare a concise planning view from the current synthetic demand and capacity signals.", kicker: "Planning reports" },
};

export default function WorkspaceView({ role, section }: { role: string; section: string }) {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [validations, setValidations] = useState<Validation[]>([]);
  const [districts, setDistricts] = useState<District[]>([]);
  const [alignment, setAlignment] = useState<{ alignment: number; missing: string[] } | null>(null);
  const [error, setError] = useState("");
  const content = copy[section] ?? { title: "Dashboard", description: "A connected view of demand, learning, and validation for this workspace.", kicker: `${role} overview` };
  function exportPlanning() {
    const header = "District,Priority Skill,Demand,Capacity,Gap,Status";
    const rows = districts.map((item) => [item.district, item.priority_skill, item.demand, item.capacity, item.gap, item.status].join(","));
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([[header, ...rows].join("\n")], { type: "text/csv" }));
    link.download = "skillyntra-district-planning.csv";
    link.click();
    URL.revokeObjectURL(link.href);
  }

  useEffect(() => {
    if (["skill-intelligence", "industry-demand", "skill-demand", "course-health", "recommendations", "analytics"].includes(section)) fetch(`${API}/api/skills/demand`).then((response) => response.json()).then(setSkills).catch(() => setError("Demand signals could not be loaded."));
    if (section === "my-skills") fetch(`${API}/api/workflow/skills/demo-student`).then((response) => response.json()).then(setValidations).catch(() => setError("Validation records could not be loaded."));
    if (["training-capacity", "reports"].includes(section)) fetch(`${API}/api/government/districts`).then((response) => response.json()).then(setDistricts).catch(() => setError("District planning data could not be loaded."));
    if (["course-health", "recommendations"].includes(section)) fetch(`${API}/api/institute/programs/Data%20Analytics`).then((response) => response.json()).then(setAlignment).catch(() => setError("Course health could not be loaded."));
  }, [section]);

  if (section === "my-skills") return <section className="workspace-view"><div className="section-banner"><CheckCircle2 size={20} /><span>Self-reported skills are separate from partner-validated evidence. Industry validation is issued after a passing company assessment.</span></div>{error && <div className="error-box">{error}</div>}{validations.length === 0 && !error && <div className="empty-box"><strong>No Industry Validated skills yet</strong><span>Open an enrolled course assessment, pass it, and your verified skills will appear here.</span></div>}<div className="validation-grid">{validations.map((item) => <article className="validation-card" key={`${item.skill}-${item.id}`}><CheckCircle2 size={20} /><div><strong>{item.skill}</strong><span>{item.status} · score {item.score}%</span><span>Validated by {item.partner} · {item.course}</span><span>Assessment: {item.assessment} · Validation ID: VAL-{String(item.id).padStart(6, "0")}</span><span>Validated on {item.validated_at}</span></div></article>)}</div></section>;
  if (["training-capacity", "reports"].includes(section)) return <section className="workspace-view"><div className="action-row"><span>Four districts from the planning dataset</span><button onClick={exportPlanning}><Download size={15} /> Export planning view</button></div><div className="district-mini-grid">{districts.map((item) => <article className="panel" key={item.district}><h3>{item.district}</h3><p>Priority: <strong>{item.priority_skill}</strong></p><div className="mini-stat"><b>{item.gap}</b><span>capacity gap</span></div><span className={item.gap > 0 ? "badge-warning" : "badge-good"}>{item.status}</span></article>)}</div></section>;
  if (["skill-intelligence", "industry-demand", "skill-demand"].includes(section)) return <section className="workspace-view"><div className="demand-heading"><div><strong>Top skills by job signals</strong><span>Calculated from data/jobs.csv</span></div><ArrowRight size={18} /></div><div className="demand-list">{skills.slice(0, 15).map((item, index) => <div className="demand-row" key={item.skill}><span>{String(index + 1).padStart(2, "0")}</span><strong>{item.skill}</strong><i><b style={{ width: `${Math.max(8, item.job_signals / Math.max(1, skills[0]?.job_signals ?? 1) * 100)}%` }} /></i><em>{item.job_signals}</em></div>)}</div></section>;
  if (["course-health", "recommendations"].includes(section)) return <section className="workspace-view"><div className="section-banner"><Gauge size={20} /><span>Course health combines market alignment with placement and employer signals.</span></div>{alignment && <div className="panel-grid"><article className="panel"><div className="metric">{alignment.alignment}%</div><h3>Data Analytics alignment</h3><p>Current course alignment against the top market requirements.</p></article><article className="panel"><div className="metric">{alignment.missing.length}</div><h3>Skills to review</h3><p>Missing skills detected from the same market-demand calculation.</p></article><article className="panel"><div className="metric">Action</div><h3>Next recommendation</h3><p>Add {alignment.missing.slice(0, 5).join(", ")} coverage.</p></article></div>}</section>;
  if (["students", "analytics"].includes(section)) return <section className="workspace-view"><div className="panel-grid"><article className="panel"><Users size={20} /><div className="metric">Demo pipeline</div><h3>Student evidence</h3><p>Assessment results and validation records are stored against a demo student identity.</p></article><article className="panel"><FileBarChart size={20} /><div className="metric">{skills.length || 55}</div><h3>Skills in market view</h3><p>Use the demand evidence to shape course and assessment design.</p></article></div></section>;
  return <section className="workspace-view"><div className="loop" aria-label="Skillyntra intelligence loop"><span>Industry demand</span><b>-&gt;</b><span>Skill gap</span><b>-&gt;</b><span>Learning</span><b>-&gt;</b><span>Validation</span><b>-&gt;</b><span>Opportunity</span></div><section className="panel-grid"><article className="panel"><div className="metric">1,200</div><h3>Job signals</h3><p>The primary synthetic labour-market dataset powering this workspace.</p></article><article className="panel"><div className="metric">Connected</div><h3>{content.title}</h3><p>{content.description}</p></article><article className="panel"><div className="metric">No dead ends</div><h3>Next action</h3><p>Use the visible workspace navigation to continue through the demo story.</p></article></section></section>;
}
