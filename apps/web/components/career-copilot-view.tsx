"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Check } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
type Summary = { role: string; jobs: number; required_skills: string[]; average_salary_lpa: number | null; experience: string; locations: string[]; matched?: string[]; missing?: string[]; readiness?: number };

export default function CareerCopilotView() {
  const [roles, setRoles] = useState<string[]>([]);
  const [role, setRole] = useState("");
  const [summary, setSummary] = useState<Summary | null>(null);
  const [selectedSkillsByCareer, setSelectedSkillsByCareer] = useState<Record<string, string[]>>({});
  const known = selectedSkillsByCareer[role] ?? [];
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API}/api/careers/roles`)
      .then((response) => response.json())
      .then((items: string[]) => {
        setRoles(items);
        setRole(items[0] ?? "");
      })
      .catch(() => setError("Career paths could not be loaded."));
  }, []);

  useEffect(() => {
    if (!role) return;
    fetch(`${API}/api/careers/${encodeURIComponent(role)}`)
      .then((response) => response.json())
      .then((data) => {
        setSummary(data);
        setSelectedSkillsByCareer((prev) => {
          const saved = prev[role] ?? [];
          if (saved.length === 0) return prev;
          const filtered = saved.filter((skill) => data.required_skills.includes(skill));
          if (filtered.length === saved.length) return prev;
          return { ...prev, [role]: filtered };
        });
      })
      .catch(() => setError("Career intelligence could not be loaded."));
  }, [role]);

  function analyze() {
    if (!role) return;
    setLoading(true);
    const params = new URLSearchParams(known.map((skill) => ["known_skills", skill]));
    fetch(`${API}/api/careers/${encodeURIComponent(role)}/gap?${params}`)
      .then((response) => response.json())
      .then(setSummary)
      .catch(() => setError("Skill gap could not be calculated."))
      .finally(() => setLoading(false));
  }

  function toggle(skill: string) {
    setSelectedSkillsByCareer((current) => {
      const existing = current[role] ?? [];
      const next = existing.includes(skill) ? existing.filter((item) => item !== skill) : [...existing, skill];
      return { ...current, [role]: next };
    });
  }

  return (
    <section className="career-view">
      <div className="career-controls">
        <label>
          Target career
          <select value={role} onChange={(event) => setRole(event.target.value)}>
            {roles.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
      </div>
      {error && <div className="error-box">{error}</div>}
      {summary && (
        <>
          <div className="career-metrics">
            <article>
              <strong>{summary.jobs}</strong>
              <span>Relevant job signals</span>
            </article>
            <article>
              <strong>{summary.average_salary_lpa ? `₹${summary.average_salary_lpa} LPA` : "-"}</strong>
              <span>Average salary midpoint</span>
            </article>
            <article>
              <strong>{summary.experience}</strong>
              <span>Observed experience range</span>
            </article>
            <article>
              <strong>{summary.locations[0] ?? "-"}</strong>
              <span>Top hiring location</span>
            </article>
          </div>
          <div className="career-grid">
            <article className="career-panel">
              <div className="panel-kicker">Market requirements</div>
              <h2>What does {summary.role} require?</h2>
              <p>These priority skills are calculated from matching job records, not a hardcoded career list.</p>
              <div className="skill-select">
                {summary.required_skills.map((skill) => (
                  <button className={known.includes(skill) ? "selected" : ""} key={skill} onClick={() => toggle(skill)}>
                    <span>{known.includes(skill) ? <Check size={14} /> : <span className="skill-dot" />}</span>
                    {skill}
                  </button>
                ))}
              </div>
              <p className="helper-text">Select the skills you already know to calculate your skill gap.</p>
              <button className="primary-action" onClick={analyze} disabled={loading || known.length === 0}>
                {loading ? "Analyzing..." : "Analyze My Career Fit"} <ArrowRight size={16} />
              </button>
            </article>
            <article className="career-panel readiness">
              <div className="panel-kicker">CAREER READINESS</div>
              <h2>{summary.readiness === undefined ? "Select skills you already know" : `${summary.readiness}%`}</h2>
              {summary.readiness !== undefined && (
                <>
                  <p className="readiness-subtext">Based on the selected career's industry-required skills.</p>
                  <div className="progress"><span style={{ width: `${summary.readiness}%` }} /></div>
                  <p className="readiness-summary">
                    You match {summary.matched?.length ?? 0} of {summary.required_skills.length} required skills.
                  </p>
                  <p className="what-this-means">
                    Matched skills are requirements you already selected as known. To Build skills are requirements you have not selected yet.
                  </p>
                  <div className="gap-columns">
                    <div>
                      <h3>MATCHED</h3>
                      {(summary.matched?.length ?? 0) > 0 ? (
                        summary.matched?.map((skill) => (
                          <span className="gap-item good" key={skill}>
                            <Check size={14} aria-hidden="true" />
                            <span>Matched</span>
                            <span>{skill}</span>
                          </span>
                        ))
                      ) : (
                        <span className="gap-item empty">No required skills matched yet.</span>
                      )}
                    </div>
                    <div>
                      <h3>TO BUILD</h3>
                      {(summary.missing?.length ?? 0) > 0 ? (
                        summary.missing?.map((skill) => (
                          <span className="gap-item" key={skill}>
                            <ArrowRight size={14} aria-hidden="true" />
                            <span>To Build</span>
                            <span>{skill}</span>
                          </span>
                        ))
                      ) : (
                        <span className="gap-item empty">You currently match all listed required skills.</span>
                      )}
                    </div>
                  </div>
                  <Link
                    className="primary-action"
                    href={`/student/courses?career=${encodeURIComponent(summary.role)}&missing=${encodeURIComponent((summary.missing ?? []).join(","))}`}
                  >
                    Build My Missing Skills <ArrowRight size={16} />
                  </Link>
                </>
              )}
            </article>
          </div>
        </>
      )}
    </section>
  );
}