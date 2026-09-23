"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type ProposalSkill = {
  skill: string;
  job_signals: number;
  priority?: number;
  recommendation?: string;
};

type CurriculumProposal = {
  course: string;
  keep: ProposalSkill[];
  add_or_strengthen: ProposalSkill[];
  has_proposal: boolean;
  message: string | null;
};

type Alignment = {
  course: string;
  taught: string[];
  required: string[];
  missing: string[];
  covered: string[];
  alignment: number;
  status: string;
  placement_rate: number;
  employer_validation: number;
  health_score: number;
  health_status: string;
  curriculum_proposal: CurriculumProposal;
};

export default function InstituteView({ onCourseChange }: { onCourseChange: (course: string) => void }) {
  const [programs, setPrograms] = useState<string[]>([]);
  const [course, setCourse] = useState("");
  const [data, setData] = useState<Alignment | null>(null);
  const [error, setError] = useState("");
  const [showProposal, setShowProposal] = useState(false);
  const [proposalError, setProposalError] = useState("");

  useEffect(() => {
    fetch(`${API}/api/institute/programs`)
      .then((response) => response.json())
      .then((items: string[]) => {
        const nextCourse = items[0] ?? "";
        setPrograms(items);
        setCourse(nextCourse);
        onCourseChange(nextCourse);
      })
      .catch(() => setError("Training programmes could not be loaded."));
  }, []);

  useEffect(() => {
    if (course) {
      setShowProposal(false);
      setProposalError("");
      fetch(`${API}/api/institute/programs/${encodeURIComponent(course)}`)
        .then((response) => {
          if (!response.ok) throw new Error();
          return response.json();
        })
        .then(setData)
        .catch(() => setError("Curriculum alignment could not be loaded."));
    }
  }, [course]);

  const handleProposalClick = () => {
    if (data?.curriculum_proposal) {
      setShowProposal(true);
    }
  };

  const handleRetry = () => {
    if (course) {
      setProposalError("");
      fetch(`${API}/api/institute/programs/${encodeURIComponent(course)}`)
        .then((response) => {
          if (!response.ok) throw new Error();
          return response.json();
        })
        .then((newData) => {
          setData(newData);
          setShowProposal(true);
        })
        .catch(() => setProposalError("Failed to generate proposal. Please try again."));
    }
  };

  return (
    <section className="alignment-view">
      {error && <div className="error-box">{error}</div>}
      {!data && !error && <div className="loading-box">Loading curriculum alignment...</div>}
      <label className="wide-select">
        Training programme
        <select
          value={course}
          onChange={(event) => {
            const nextCourse = event.target.value;
            setCourse(nextCourse);
            onCourseChange(nextCourse);
            setShowProposal(false);
          }}
        >
          {programs.map((item) => (
            <option key={item}>{item}</option>
          ))}
        </select>
      </label>
      {data && (
        <>
          <div className="alignment-summary">
            <div>
              <strong>{data.alignment}%</strong>
              <span>Industry alignment</span>
            </div>
            <div>
              <strong>{data.health_status}</strong>
              <span>Course health</span>
            </div>
            <div>
              <strong>{data.missing.length}</strong>
              <span>Skills to add</span>
            </div>
          </div>
          <div className="alignment-grid">
            <article className="career-panel">
              <div className="panel-kicker">Current curriculum</div>
              <h2>Skills already taught</h2>
              <div className="tag-list">
                {data.taught.map((skill) => (
                  <span className="tag-good" key={skill}>Keep · {skill}</span>
                ))}
              </div>
            </article>
            <article className="career-panel">
              <div className="panel-kicker">Recommended curriculum update</div>
              <h2>Add or strengthen</h2>
              <p>These skills appear in high-demand observed job signals and are not covered by this programme.</p>
              <div className="tag-list">
                {data.missing.slice(0, 8).map((skill) => (
                  <span className="tag-warn" key={skill}>Add · {skill}</span>
                ))}
              </div>
              <button className="primary-action" onClick={handleProposalClick}>
                Generate curriculum update proposal
              </button>
              {showProposal && data.curriculum_proposal && (
                <div className="proposal-box">
                  {data.curriculum_proposal.message ? (
                    <div className="success-box">{data.curriculum_proposal.message}</div>
                  ) : (
                    <>
                      <h3>CURRICULUM UPDATE PROPOSAL</h3>
                      <p><strong>Course:</strong> {data.curriculum_proposal.course}</p>
                      <div className="proposal-section">
                        <h4>KEEP</h4>
                        <ul>
                          {data.curriculum_proposal.keep.map((item, idx) => (
                            <li key={idx}>
                              {item.skill} <span className="signals">({item.job_signals} job signals)</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className="proposal-section">
                        <h4>ADD / STRENGTHEN</h4>
                        <ol>
                          {data.curriculum_proposal.add_or_strengthen.map((item) => (
                            <li key={item.priority}>
                              <strong>{item.priority}. {item.skill}</strong>
                              <div className="proposal-detail">
                                <span>Industry demand: {item.job_signals} relevant job signals</span>
                                <span>Recommendation: {item.recommendation}</span>
                              </div>
                            </li>
                          ))}
                        </ol>
                      </div>
                    </>
                  )}
                  {proposalError && (
                    <div className="error-box">
                      {proposalError}
                      <button className="retry-btn" onClick={handleRetry}>Retry</button>
                    </div>
                  )}
                </div>
              )}
            </article>
          </div>
        </>
      )}
    </section>
  );
}
