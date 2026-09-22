"use client";

import { useEffect, useState } from "react";
import { Search, SlidersHorizontal } from "lucide-react";

type Job = { job_id: string; job_title: string; domain: string; company: string; location: string; state: string; seniority: string; salary_min_lpa: number; salary_max_lpa: number; experience_min_years: number; experience_max_years: number; skills: string[] };
type Options = { domains: string[]; locations: string[]; states: string[]; seniorities: string[] };
type JobPage = { items: Job[]; total: number; page: number; page_size: number };

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export default function LabourMarketView() {
  const [options, setOptions] = useState<Options>({ domains: [], locations: [], states: [], seniorities: [] });
  const [jobs, setJobs] = useState<JobPage | null>(null);
  const [query, setQuery] = useState("");
  const [domain, setDomain] = useState("");
  const [location, setLocation] = useState("");
  const [seniority, setSeniority] = useState("");
  const [page, setPage] = useState(1);
  const [error, setError] = useState("");

  useEffect(() => { fetch(`${API}/api/jobs/options`).then((response) => response.json()).then(setOptions).catch(() => setError("Market filters could not be loaded.")); }, []);
  useEffect(() => {
    const params = new URLSearchParams({ page: String(page), page_size: "12" });
    if (query) params.set("search", query);
    if (domain) params.set("domain", domain);
    if (location) params.set("location", location);
    if (seniority) params.set("seniority", seniority);
    fetch(`${API}/api/jobs?${params}`).then((response) => { if (!response.ok) throw new Error(); return response.json(); }).then(setJobs).catch(() => setError("Job signals could not be loaded."));
  }, [query, domain, location, seniority, page]);

  function selectFilter(setter: (value: string) => void, value: string) { setter(value); setPage(1); }

  return <section className="market-view">
    <div className="section-banner"><span>Prototype mode · synthetic labour-market data. These are observed demo records, not live Maharashtra statistics.</span></div>
    <div className="market-toolbar"><label className="search-field"><Search size={17} /><input value={query} onChange={(event) => selectFilter(setQuery, event.target.value)} placeholder="Search role, company or skill" /></label><span className="filter-mark"><SlidersHorizontal size={16} /> {jobs?.total ?? "-"} matching signals</span></div>
    <div className="filter-row"><select aria-label="Domain" value={domain} onChange={(event) => selectFilter(setDomain, event.target.value)}><option value="">All domains</option>{options.domains.map((item) => <option key={item}>{item}</option>)}</select><select aria-label="Location" value={location} onChange={(event) => selectFilter(setLocation, event.target.value)}><option value="">All locations</option>{options.locations.map((item) => <option key={item}>{item}</option>)}</select><select aria-label="Seniority" value={seniority} onChange={(event) => selectFilter(setSeniority, event.target.value)}><option value="">All seniority levels</option>{options.seniorities.map((item) => <option key={item}>{item}</option>)}</select></div>
    {error && <div className="error-box">{error}</div>}
    {!jobs && !error && <div className="loading-box">Loading market signals...</div>}
    {jobs && jobs.items.length === 0 && <div className="empty-box"><strong>No matching job signals</strong><span>Try widening the search or clearing a filter.</span></div>}
    <div className="job-grid">{jobs?.items.map((job) => <article className="job-card" key={job.job_id}><div className="job-top"><span className="job-domain">{job.domain}</span><span className="job-seniority">{job.seniority}</span></div><h3>{job.job_title}</h3><p className="job-company">{job.company} · {job.location}, {job.state}</p><p className="job-meta">₹{job.salary_min_lpa.toFixed(1)} - ₹{job.salary_max_lpa.toFixed(1)} LPA <span>·</span> {job.experience_min_years}-{job.experience_max_years} years</p><div className="job-skills">{job.skills.slice(0, 5).map((skill) => <span key={skill}>{skill}</span>)}</div></article>)}</div>
    {jobs && jobs.total > jobs.page_size && <div className="pager"><button disabled={page === 1} onClick={() => setPage(page - 1)}>Previous</button><span>Page {page} of {Math.ceil(jobs.total / jobs.page_size)}</span><button disabled={page >= Math.ceil(jobs.total / jobs.page_size)} onClick={() => setPage(page + 1)}>Next</button></div>}
  </section>;
}