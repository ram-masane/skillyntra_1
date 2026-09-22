"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Check, MapPin, TrendingUp } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
type Summary = { role: string; jobs: number; required_skills: string[]; average_salary_lpa: number | null; experience: string; locations: string[]; matched?: string[]; missing?: string[]; readiness?: number };

export default function CareerCopilotView() {
  const [roles, setRoles] = useState<string[]>([]);
  const [role, setRole] = useState("");
  const [summary, setSummary] = useState<Summary | null>(null);
  const [known, setKnown] = useState<string[]>([]);
  const [error, setError] = useState("");

  useEffect(() => { fetch(`${API}/api/careers/roles`).then((response) => response.json()).then((items: string[]) => { setRoles(items); setRole(items[0] ?? ""); }).catch(() => setError("Career paths could not be loaded.")); }, []);
  useEffect(() => { if (!role) return; fetch(`${API}/api/careers/${encodeURIComponent(role)}`).then((response) => response.json()).then((data) => { setSummary(data); setKnown([]); }).catch(() => setError("Career intelligence could not be loaded.")); }, [role]);

  function analyze() { if (!role) return; const params = new URLSearchParams(known.map((skill) => ["known_skills", skill])); fetch(`${API}/api/careers/${encodeURIComponent(role)}/gap?${params}`).then((response) => response.json()).then(setSummary).catch(() => setError("Skill gap could not be calculated.")); }
  function toggle(skill: string) { setKnown((current) => current.includes(skill) ? current.filter((item) => item !== skill) : [...current, skill]); }

  return <section className="career-view">
    <div className="career-controls"><label>Target career<select value={role} onChange={(event) => setRole(event.target.value)}>{roles.map((item) => <option key={item}>{item}</option>)}</select></label><button onClick={analyze}><TrendingUp size={16} /> Analyze readiness</button></div>
    {error && <div className="error-box">{error}</div>}
    {summary && <><div className="career-metrics"><article><strong>{summary.jobs}</strong><span>Relevant job signals</span></article><article><strong>{summary.average_salary_lpa ? `₹${summary.average_salary_lpa} LPA` : "-"}</strong><span>Average salary midpoint</span></article><article><strong>{summary.experience}</strong><span>Observed experience range</span></article><article><strong>{summary.locations[0] ?? "-"}</strong><span>Top hiring location</span></article></div><div className="career-grid"><article className="career-panel"><div className="panel-kicker">Market requirements</div><h2>What does {summary.role} require?</h2><p>These priority skills are calculated from matching job records, not a hardcoded career list.</p><div className="skill-select">{summary.required_skills.map((skill) => <button className={known.includes(skill) ? "selected" : ""} key={skill} onClick={() => toggle(skill)}><span>{known.includes(skill) ? <Check size={14} /> : <span className="skill-dot" />}</span>{skill}</button>)}</div><button className="primary-action" onClick={analyze}>Calculate my skill gap <ArrowRight size={16} /></button></article><article className="career-panel readiness"><div className="panel-kicker">Readiness snapshot</div><h2>{summary.readiness === undefined ? "Select skills you already know" : `${summary.readiness}% market readiness`}</h2>{summary.readiness !== undefined && <><div className="progress"><span style={{ width: `${summary.readiness}%` }} /></div><div className="gap-columns"><div><b>Matched</b>{summary.matched?.map((skill) => <span className="gap-item good" key={skill}><Check size={14} />{skill}</span>)}</div><div><b>To build</b>{summary.missing?.map((skill) => <span className="gap-item" key={skill}><MapPin size={14} />{skill}</span>)}</div></div><Link className="primary-action" href={`/student/courses?career=${encodeURIComponent(summary.role)}&missing=${encodeURIComponent((summary.missing ?? []).join(","))}`}>Build my missing skills <ArrowRight size={16} /></Link></>}</article></div></>}
  </section>;
}
