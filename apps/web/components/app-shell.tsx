"use client";

import Link from "next/link";
import { useState } from "react";
import { BarChart3, BookOpen, BriefcaseBusiness, ClipboardCheck, Compass, Factory, LayoutDashboard, Menu, Network, School, ShieldCheck, X } from "lucide-react";
import LabourMarketView from "./labour-market-view";
import CareerCopilotView from "./career-copilot-view";
import CoursesView from "./courses-view";
import AssessmentView from "./assessment-view";
import InstituteView from "./institute-view";
import GovernmentView from "./government-view";
import PartnerConsoleView from "./partner-console-view";
import WorkspaceView from "./workspace-view";

const configs = {
  student: { label: "Student", home: "Your career, made legible.", description: "Translate real job-market signals into a focused skill plan, then prove what you can do.", nav: [["Dashboard", "", LayoutDashboard], ["Career Copilot", "career-copilot", Compass], ["Labour Market", "labour-market", BriefcaseBusiness], ["Skill Intelligence", "skill-intelligence", BarChart3], ["Courses", "courses", BookOpen], ["Assessments", "assessments", ClipboardCheck], ["My Skills", "my-skills", ShieldCheck]] },
  company: { label: "Partner Company", home: "Build the talent pipeline.", description: "Publish relevant courses, assess capability, and turn strong performance into trusted skill signals.", nav: [["Dashboard", "", LayoutDashboard], ["Courses", "courses", BookOpen], ["Create Course", "courses/new", BookOpen], ["Assessments", "assessments", ClipboardCheck], ["Students", "students", School], ["Analytics", "analytics", BarChart3]] },
  institute: { label: "Training Institute", home: "Keep curriculum close to demand.", description: "See which capabilities industry needs and where your programmes can become more relevant.", nav: [["Dashboard", "", LayoutDashboard], ["Curriculum Alignment", "curriculum", Network], ["Course Health", "course-health", ShieldCheck], ["Industry Demand", "industry-demand", BarChart3], ["Recommendations", "recommendations", Compass]] },
  government: { label: "Government", home: "Plan for the skills districts need.", description: "Compare demand and training capacity to direct investment where shortages are clearest.", nav: [["Dashboard", "", LayoutDashboard], ["District Planner", "district-planner", Factory], ["Skill Demand", "skill-demand", BarChart3], ["Training Capacity", "training-capacity", School], ["Reports", "reports", BriefcaseBusiness]] },
} as const;

type Role = keyof typeof configs;

export default function AppShell({ role, section }: { role: string; section?: string }) {
  const currentRole: Role = role in configs ? role as Role : "student";
  const config = configs[currentRole];
  const [menuOpen, setMenuOpen] = useState(false);
  const activeSection = section ?? "";
  const activeView = config.nav.find(([, path]) => path === activeSection);
  const viewTitle = activeView?.[0] ?? config.home;
  const viewDescription = activeView
    ? `${activeView[0]} is connected to the same industry-demand picture and ready for the demo workflow.`
    : config.description;

  return <div className="shell">
    <aside className={`sidebar ${menuOpen ? "open" : ""}`}>
      <div className="logo"><strong>skillyntra<span>.</span></strong><small>{config.label} workspace</small></div>
      <div className="role-switch"><label htmlFor="role">Continue as</label><select id="role" value={currentRole} onChange={(event) => { window.location.href = `/${event.target.value}`; }}><option value="student">Student</option><option value="company">Partner Company</option><option value="institute">Training Institute</option><option value="government">Government</option></select></div>
      <nav className="nav" aria-label="Primary navigation"><div className="nav-label">Workspace</div>{config.nav.map(([label, path, Icon]) => <Link className={`nav-link ${activeSection === path ? "active" : ""}`} href={`/${currentRole}${path ? `/${path}` : ""}`} key={label} onClick={() => setMenuOpen(false)}><Icon size={17} strokeWidth={1.8} />{label}</Link>)}</nav>
      <div className="sidebar-note">Prototype mode · synthetic labour-market data<br /><strong>1,200 job signals</strong></div>
    </aside>
    <main className="main">
      <div className="topbar"><button className="mobile-menu" aria-label={menuOpen ? "Close navigation" : "Open navigation"} onClick={() => setMenuOpen(!menuOpen)}>{menuOpen ? <X size={20} /> : <Menu size={20} />}</button><div className="crumb">Skillyntra / {config.label}</div><div className="status"><i /> System online</div></div>
      <section className="content-header"><div className="eyebrow">{config.label} workspace</div><h1>{viewTitle}</h1><p>{viewDescription}</p></section>
      {activeSection === "labour-market" ? <LabourMarketView /> : activeSection === "career-copilot" ? <CareerCopilotView /> : currentRole === "company" && activeSection === "courses/new" ? <PartnerConsoleView /> : currentRole === "company" && activeSection === "assessments" ? <PartnerConsoleView assessment /> : activeSection === "courses" ? <CoursesView /> : activeSection === "assessments" ? <AssessmentView /> : currentRole === "institute" && activeSection === "curriculum" ? <InstituteView /> : currentRole === "government" && activeSection === "district-planner" ? <GovernmentView /> : <WorkspaceView role={currentRole} section={activeSection} />}
    </main>
  </div>;
}
