from pathlib import Path
import re
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.assessment_service import DEFAULT_QUESTIONS, grade_answers
from backend.services.course_service import calculate_course_alignment, calculate_course_health
from backend.services.job_service import career_summary, filter_jobs, role_skills as service_role_skills, skill_demand as service_skill_demand

DATA = ROOT / "data"
st.set_page_config(page_title="Skillyntra", page_icon="✦", layout="wide", initial_sidebar_state="expanded")

# ---------------- DATA ----------------
@st.cache_data

def load_data():
    files = {
        "jobs": "jobs.csv", "employer": "employer_feedback.csv", "growth": "sector_growth.csv",
        "placements": "placements.csv", "capacity": "training_capacity.csv", "courses": "courses.csv"
    }
    return {k: pd.read_csv(DATA / f) for k, f in files.items()}

D = load_data()
jobs, employer, growth = D["jobs"], D["employer"], D["growth"]
placements, capacity, courses = D["placements"], D["capacity"], D["courses"]


def split_skills(v):
    if pd.isna(v): return []
    return [x.strip() for x in re.split(r",|;|\|", str(v)) if x.strip()]


def skill_rows(df):
    rows = []
    for _, r in df.iterrows():
        for s in split_skills(r.skills):
            rows.append({"skill": s, "job_title": r.job_title, "domain": r.domain, "location": r.location, "state": r.state})
    return pd.DataFrame(rows)


def demand_of(df):
    x = skill_rows(df)
    if x.empty: return pd.DataFrame(columns=["skill", "job_signals"])
    return x.groupby("skill").size().reset_index(name="job_signals").sort_values(["job_signals", "skill"], ascending=[False, True])


def role_skills(role, location="All"):
    x = jobs[jobs.job_title.eq(role)]
    if location != "All":
        y = x[x.location.eq(location)]
        if not y.empty: x = y
    q = skill_rows(x)
    return q.groupby("skill").size().sort_values(ascending=False).head(8).index.tolist() if not q.empty else []


def gap(req, known):
    k = {x.lower() for x in known}
    matched = [x for x in req if x.lower() in k]
    missing = [x for x in req if x.lower() not in k]
    return matched, missing, round(100 * len(matched) / max(1, len(req)))


def course_result(name):
    r = courses[courses.course.eq(name)]
    if r.empty: return [], 0, 0, 0, []
    r = r.iloc[0]
    taught = split_skills(r.skills)
    alignment_result = calculate_course_alignment(taught, jobs)
    align = alignment_result["alignment"]
    placement = float(r.placement_rate)
    emp = float(r.employer_validation)
    health = round(.45 * align + .30 * placement + .25 * emp)
    return taught, placement, align, health, alignment_result["missing"]


def cap_metrics(df):
    x = df.copy()
    x["gap"] = x.estimated_demand - x.annual_capacity
    x["status"] = x.gap.apply(lambda v: "SHORTAGE" if v > 0 else ("POTENTIAL OVERSUPPLY" if v < 0 else "BALANCED"))
    return x.sort_values("gap", ascending=False)


def money(v):
    return f"₹{v:.1f} LPA"

# ---------------- SESSION ----------------
if "page" not in st.session_state: st.session_state.page = "Home"
if "demo_role" not in st.session_state: st.session_state.demo_role = "Student"
if "career" not in st.session_state: st.session_state.career = sorted(jobs.job_title.unique())[0]
if "known" not in st.session_state: st.session_state.known = []
if "course" not in st.session_state: st.session_state.course = courses.course.iloc[0]
if "partner_courses" not in st.session_state: st.session_state.partner_courses = []
if "enrolled" not in st.session_state: st.session_state.enrolled = []
if "exam_started" not in st.session_state: st.session_state.exam_started = False
if "exam_submitted" not in st.session_state: st.session_state.exam_submitted = False
if "overrides" not in st.session_state: st.session_state.overrides = {}

PAGES = ["Home", "Labour Market", "Career Copilot", "Skill Intelligence", "Courses & Exams", "My Skills", "Institute", "Government", "Evidence"]

def go(p):
    st.session_state.page = p
    st.rerun()

# ---------------- STYLE ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--ink:#101828;--muted:#667085;--line:#E4E7EC;--bg:#F7F8FC;--card:#FFFFFF;--purple:#6D4AFF;--pink:#FF4D8D;--cyan:#00B8D9;--lime:#A6E22E;--yellow:#FFC857}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}.stApp{background:var(--bg)}
#MainMenu,header,footer{visibility:hidden}.block-container{max-width:1500px;padding:0 34px 60px}
[data-testid="stSidebar"]{background:#111827;border-right:0}.side-logo{padding:26px 18px 24px;border-bottom:1px solid #293244}.side-logo .mini{font-size:10px;color:#98A2B3;letter-spacing:1.5px}.side-logo .brand{font-family:'Space Grotesk';font-size:27px;font-weight:700;color:#fff;margin-top:5px}.side-logo .dot{color:#A6E22E}
[data-testid="stSidebar"] .stButton>button{width:100%;border:0!important;background:transparent!important;color:#CBD5E1!important;text-align:left;border-radius:10px!important;padding:10px 12px!important;font-size:13px!important;font-weight:600!important}[data-testid="stSidebar"] .stButton>button:hover{background:#1E293B!important;color:#fff!important}
.nav-active button{background:linear-gradient(90deg,#6D4AFF,#8A63FF)!important;color:#fff!important}
.topbar{background:#fff;border:1px solid var(--line);border-radius:16px;padding:13px 18px;display:flex;justify-content:space-between;align-items:center;margin:22px 0 28px;box-shadow:0 8px 25px rgba(16,24,40,.04)}
.pill{border-radius:999px;padding:7px 12px;font-size:11px;font-weight:700}.pill-green{background:#ECFDF3;color:#027A48}.pill-purple{background:#F4F3FF;color:#5925DC}.pill-blue{background:#ECFDFE;color:#0E7490}
.hero{position:relative;overflow:hidden;background:linear-gradient(135deg,#15112B 0%,#2D1D6B 45%,#5634D9 100%);border-radius:26px;padding:42px;color:#fff;box-shadow:0 18px 45px rgba(78,53,190,.22);animation:rise .6s ease-out}.hero:after{content:"";position:absolute;width:320px;height:320px;border-radius:50%;background:rgba(166,226,46,.12);right:-90px;top:-120px}.hero h1{font-family:'Space Grotesk';font-size:44px;line-height:1.03;margin:0 0 13px}.hero p{max-width:780px;color:#E9E7FF;font-size:16px;line-height:1.65}.hero .spark{color:#A6E22E}.hero-actions{display:flex;gap:10px;margin-top:22px}
.section-title{font-family:'Space Grotesk';font-size:21px;font-weight:700;color:var(--ink);margin:32px 0 12px}.section-sub{color:var(--muted);font-size:13px;margin-top:-7px;margin-bottom:16px}
.stat{background:#fff;border:1px solid var(--line);border-radius:18px;padding:20px;box-shadow:0 8px 24px rgba(16,24,40,.035);min-height:122px;transition:.2s}.stat:hover{transform:translateY(-3px);box-shadow:0 15px 30px rgba(16,24,40,.08)}.stat-label{font-size:11px;color:var(--muted);font-weight:700;text-transform:uppercase;letter-spacing:.6px}.stat-value{font-family:'Space Grotesk';font-size:29px;font-weight:700;color:var(--ink);margin-top:8px}.stat-note{font-size:11px;color:var(--muted);margin-top:6px}
.card{background:#fff;border:1px solid var(--line);border-radius:18px;padding:20px;box-shadow:0 8px 24px rgba(16,24,40,.035)}.card h3{font-family:'Space Grotesk';margin:0 0 6px;color:var(--ink)}
.flow{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}.flow-item{padding:11px 14px;background:#fff;border:1px solid var(--line);border-radius:12px;font-weight:700;font-size:12px}.flow-arrow{color:var(--purple);font-weight:800;align-self:center}
.course-card{background:#fff;border:1px solid var(--line);border-radius:20px;padding:20px;height:100%;position:relative;overflow:hidden;transition:.25s}.course-card:hover{transform:translateY(-4px);box-shadow:0 18px 35px rgba(16,24,40,.09)}.course-accent{height:5px;position:absolute;top:0;left:0;right:0;background:linear-gradient(90deg,#6D4AFF,#FF4D8D,#00B8D9)}.company{font-size:11px;color:#6D4AFF;font-weight:800;text-transform:uppercase;letter-spacing:.7px}.course-name{font-family:'Space Grotesk';font-size:20px;font-weight:700;margin:8px 0}.skill-chip{display:inline-block;background:#F2F4F7;border-radius:999px;padding:5px 9px;margin:3px;font-size:10px;color:#344054}.rating{color:#F79009;font-weight:700}.exam-box{background:linear-gradient(135deg,#F9F5FF,#FFF7FB);border:1px solid #E9D7FE;border-radius:18px;padding:20px}
.notice{padding:13px 16px;border-radius:13px;background:#F4F3FF;border:1px solid #DDD6FE;color:#4C1D95;font-size:12px}.successbox{padding:16px;border-radius:15px;background:#ECFDF3;border:1px solid #ABEFC6;color:#05603A}
@keyframes rise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
.stButton>button{border-radius:12px!important;font-weight:700!important}.stSelectbox>div>div,.stMultiSelect>div>div{border-radius:12px!important}.stTabs [data-baseweb="tab-list"]{gap:8px}.stTabs [data-baseweb="tab"]{border-radius:10px;padding:9px 15px}.stTabs [aria-selected="true"]{background:#F4F3FF}
</style>
""", unsafe_allow_html=True)

# ---------------- NAV ----------------
with st.sidebar:
    st.markdown('<div class="side-logo"><div class="mini">AI · SKILLS · CAREERS</div><div class="brand">skillyntra<span class="dot">.</span></div></div>', unsafe_allow_html=True)
    st.selectbox("Continue as", ["Student", "Partner Company", "Training Institute", "Government"], key="demo_role")
    st.caption("Demo mode · no real authentication")
    for i, p in enumerate(PAGES):
        active = 'nav-active' if p == st.session_state.page else ''
        st.markdown(f'<div class="{active}">', unsafe_allow_html=True)
        if st.button(f"{'✦' if p=='Home' else '◈'}  {p}", key="nav_"+p): go(p)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div style="height:20px"></div><div class="notice" style="background:#1E293B;border-color:#334155;color:#CBD5E1">Prototype mode<br><b style="color:#fff">1,200 synthetic job signals</b><br>Partner course + exam workflow enabled.</div>', unsafe_allow_html=True)

st.markdown('<div class="topbar"><div><b>Government of Maharashtra</b><span style="color:#98A2B3"> · Skills, Employment, Entrepreneurship & Innovation</span></div><div><span class="pill pill-green">● SYSTEM ONLINE</span>&nbsp; <span class="pill pill-purple">PS 26134</span></div></div>', unsafe_allow_html=True)

# ---------------- HELPERS ----------------
def page_header(title, subtitle, kicker="SKILLYNTRA INTELLIGENCE"):
    st.markdown(f'<div style="margin-bottom:20px"><div style="font-size:10px;font-weight:800;letter-spacing:1.5px;color:#6D4AFF">{kicker}</div><div style="font-family:Space Grotesk;font-size:32px;font-weight:700;color:#101828;margin-top:5px">{title}</div><div style="color:#667085;font-size:14px;margin-top:5px;max-width:900px">{subtitle}</div></div>', unsafe_allow_html=True)

def card_stat(label, value, note=""):
    return f'<div class="stat"><div class="stat-label">{label}</div><div class="stat-value">{value}</div><div class="stat-note">{note}</div></div>'

def styled_fig(fig, h=350):
    fig.update_layout(template="plotly_white", height=h, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=20,r=20,t=20,b=20), font=dict(family="DM Sans",color="#101828"), legend=dict(orientation="h",y=1.08))
    fig.update_xaxes(showgrid=True, gridcolor="#EAECF0", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#EAECF0", zeroline=False)
    return fig

# ---------------- HOME ----------------
if st.session_state.page == "Home":
    st.markdown('<div class="hero"><div style="font-size:11px;font-weight:800;letter-spacing:2px;color:#C4B5FD">LABOUR MARKET → LEARNING → OPPORTUNITY</div><h1>Skills that move<br><span class="spark">careers forward.</span></h1><p>Skillyntra connects live-style job-market signals, skill gaps, industry-aligned courses, company assessments and training capacity into one intelligent career ecosystem.</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">The Skillyntra loop</div><div class="section-sub">From discovering demand to proving a skill.</div>', unsafe_allow_html=True)
    st.markdown('<div class="flow"><div class="flow-item">Industry Demand</div><div class="flow-arrow">→</div><div class="flow-item">Skill Intelligence</div><div class="flow-arrow">→</div><div class="flow-item">Skill Gap</div><div class="flow-arrow">→</div><div class="flow-item">Partner Course</div><div class="flow-arrow">→</div><div class="flow-item">Company Exam</div><div class="flow-arrow">→</div><div class="flow-item">Placement Signal</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Market at a glance</div>', unsafe_allow_html=True)
    c = st.columns(4)
    metrics = [("Job signals", f"{len(jobs):,}", "Synthetic prototype records"),("Career paths", jobs.job_title.nunique(), "Across multiple domains"),("Skills tracked", skill_rows(jobs).skill.nunique(), "Extracted from postings"),("Cities", jobs.location.nunique(), "Indian job locations")]
    for col,(a,b,n) in zip(c,metrics): col.markdown(card_stat(a,b,n),unsafe_allow_html=True)
    l,r=st.columns([1.15,.85])
    with l:
        st.markdown('<div class="section-title">Top demanded skills</div>',unsafe_allow_html=True)
        dd=demand_of(jobs).head(10).sort_values("job_signals")
        fig=px.bar(dd,x="job_signals",y="skill",orientation="h",labels={"job_signals":"Job signals","skill":""})
        fig.update_traces(marker_color="#6D4AFF",marker_line_width=0)
        st.plotly_chart(styled_fig(fig,360),use_container_width=True,config={"displayModeBar":False})
    with r:
        st.markdown('<div class="section-title">What users get</div>',unsafe_allow_html=True)
        for t,d in [("Students","Career-specific skill gap + roadmap"),("Companies","Courses + assessments + validation"),("Institutes","Curriculum alignment + course health"),("Government","District demand + capacity planning")]:
            st.markdown(f'<div class="card" style="margin-bottom:9px"><b>{t}</b><div style="font-size:12px;color:#667085;margin-top:4px">{d}</div></div>',unsafe_allow_html=True)

# ---------------- MARKET ----------------
elif st.session_state.page == "Labour Market":
    page_header("Market Pulse","Explore the job signals powering Skillyntra — roles, domains, skills, salaries, experience and locations.")
    search, dom, loc, state, role, sen = st.columns(6)
    with search: query = st.text_input("Search", placeholder="Role, company or skill")
    with dom: domain = st.selectbox("Domain", ["All"] + sorted(jobs.domain.unique()))
    with loc: city = st.selectbox("City", ["All"] + sorted(jobs.location.unique()))
    with state: state_name = st.selectbox("State", ["All"] + sorted(jobs.state.unique()))
    with role: career = st.selectbox("Career", ["All"] + sorted(jobs.job_title.unique()))
    with sen: seniority = st.selectbox("Seniority", ["All"] + sorted(jobs.seniority.unique()))
    salary, experience = st.columns(2)
    with salary: min_salary = st.slider("Minimum salary ceiling (LPA)", 0.0, float(jobs.salary_max_lpa.max()), 0.0, 0.5)
    with experience: max_experience = st.slider("Maximum entry experience (years)", 0, int(jobs.experience_max_years.max()), int(jobs.experience_max_years.max()))
    f = filter_jobs(jobs, query, career, domain, city, state_name, seniority, min_salary or None, max_experience if max_experience < jobs.experience_max_years.max() else None)
    sm=demand_of(f)
    c=st.columns(4)
    vals=[("Matching jobs",len(f),"After filters"),("Roles",f.job_title.nunique(),"Career options"),("Skills",skill_rows(f).skill.nunique() if len(f) else 0,"Observed requirements"),("Avg salary",money(((f.salary_min_lpa+f.salary_max_lpa)/2).mean()) if len(f) else "—","Midpoint estimate")]
    for col,(t,v,n) in zip(c,vals): col.markdown(card_stat(t,v,n),unsafe_allow_html=True)
    l,r=st.columns([1.1,.9])
    with l:
        st.markdown('<div class="section-title">Skill demand</div>',unsafe_allow_html=True)
        if not sm.empty:
            fig=px.bar(sm.head(12).sort_values("job_signals"),x="job_signals",y="skill",orientation="h",labels={"job_signals":"Job postings","skill":""});fig.update_traces(marker_color="#FF4D8D")
            st.plotly_chart(styled_fig(fig,390),use_container_width=True,config={"displayModeBar":False})
    with r:
        st.markdown('<div class="section-title">Domain mix</div>',unsafe_allow_html=True)
        x=f.domain.value_counts().reset_index();x.columns=["domain","jobs"]
        fig=px.pie(x,names="domain",values="jobs",hole=.62);fig.update_traces(textinfo="none")
        st.plotly_chart(styled_fig(fig,390),use_container_width=True,config={"displayModeBar":False})
    st.markdown('<div class="section-title">Job intelligence table</div>',unsafe_allow_html=True)
    show=f[["job_title","domain","company","location","state","salary_min_lpa","salary_max_lpa","experience_min_years","experience_max_years","skills"]].head(250).copy()
    show.columns=["Role","Domain","Company","Location","State","Min Salary (LPA)","Max Salary (LPA)","Min Exp","Max Exp","Required Skills"]
    st.dataframe(show,use_container_width=True,hide_index=True,height=430)

# ---------------- SKILL INTELLIGENCE ----------------
elif st.session_state.page == "Skill Intelligence":
    page_header("Skill Intelligence", "Read the skills behind the job market by domain, location, career and salary. Every metric is calculated from the synthetic labour-market dataset.")
    demand = service_skill_demand(jobs)
    a, b, c = st.columns(3)
    a.markdown(card_stat("Skills tracked", demand.skill.nunique(), "Observed in job records"), unsafe_allow_html=True)
    b.markdown(card_stat("Highest demand", demand.iloc[0].skill if not demand.empty else "-", "Most frequent requirement"), unsafe_allow_html=True)
    c.markdown(card_stat("Job signals", f"{len(jobs):,}", "Synthetic prototype records"), unsafe_allow_html=True)
    l, r = st.columns(2)
    with l:
        st.markdown('<div class="section-title">Top demanded skills</div><div class="section-sub">Frequency across all job signals.</div>', unsafe_allow_html=True)
        fig = px.bar(demand.head(12).sort_values("job_signals"), x="job_signals", y="skill", orientation="h", labels={"job_signals":"Job signals", "skill":""})
        fig.update_traces(marker_color="#6D4AFF")
        st.plotly_chart(styled_fig(fig, 420), use_container_width=True, config={"displayModeBar": False})
    with r:
        st.markdown('<div class="section-title">Demand by domain</div><div class="section-sub">The breadth of each domain in the current dataset.</div>', unsafe_allow_html=True)
        domain_mix = jobs.domain.value_counts().reset_index(); domain_mix.columns = ["domain", "jobs"]
        fig = px.pie(domain_mix, names="domain", values="jobs", hole=.58, color_discrete_sequence=["#6D4AFF", "#FF4D8D", "#00B8D9", "#A6E22E", "#FFC857"])
        st.plotly_chart(styled_fig(fig, 420), use_container_width=True, config={"displayModeBar": False})
    selected_domain = st.selectbox("Compare domain skill demand", ["All"] + sorted(jobs.domain.unique()))
    domain_jobs = jobs if selected_domain == "All" else jobs[jobs.domain.eq(selected_domain)]
    by_domain = service_skill_demand(domain_jobs).head(15)
    st.dataframe(by_domain.rename(columns={"skill":"Skill", "job_signals":"Job signals"}), use_container_width=True, hide_index=True)

# ---------------- CAREER ----------------
elif st.session_state.page == "Career Copilot":
    page_header("Career Copilot","Choose a target role. Skillyntra derives the most frequent requirements from matching job signals and turns them into a personal plan.")
    a,b=st.columns([1,1])
    with a: career=st.selectbox("What do you want to become?",sorted(jobs.job_title.unique()),index=sorted(jobs.job_title.unique()).index(st.session_state.career));st.session_state.career=career
    with b: target_loc=st.selectbox("Target location",["All"]+sorted(jobs.location.unique()))
    req=service_role_skills(jobs, career, target_loc)
    st.markdown(f'<div class="notice">✨ <b>{len(req)} priority skills</b> inferred from job postings for <b>{career}</b>. This is the market signal behind your roadmap.</div>',unsafe_allow_html=True)
    known=st.multiselect("Which skills do you already know?",req,default=[x for x in st.session_state.known if x in req]);st.session_state.known=known
    if st.button("Analyze my readiness →",type="primary",use_container_width=True): st.session_state.ready=True
    if st.session_state.get("ready"):
        matched,missing,ready=gap(req,known)
        c=st.columns(3)
        for col,(t,v,n) in zip(c,[("Career readiness",f"{ready}%","Based on priority skills"),("Matched skills",len(matched),"Already known"),("Skills to build",len(missing),"Market requirements")]):col.markdown(card_stat(t,v,n),unsafe_allow_html=True)
        l,r=st.columns(2)
        with l:
            st.markdown('<div class="section-title">✓ What I know</div>',unsafe_allow_html=True)
            for s in matched: st.markdown(f'<div class="card" style="padding:12px 15px;margin:6px 0">✓ <b>{s}</b></div>',unsafe_allow_html=True)
        with r:
            st.markdown('<div class="section-title">→ What I am missing</div>',unsafe_allow_html=True)
            for s in missing: st.markdown(f'<div class="card" style="padding:12px 15px;margin:6px 0;border-left:4px solid #FF4D8D">• <b>{s}</b></div>',unsafe_allow_html=True)
        st.markdown('<div class="section-title">Your next-step plan</div>',unsafe_allow_html=True)
        for i,s in enumerate(missing,1):
            st.markdown(f'<div class="course-card" style="margin:8px 0"><div class="course-accent"></div><div class="company">STEP {i:02d}</div><div class="course-name">Build {s}</div><div style="font-size:12px;color:#667085">High-frequency requirement for {career}. Explore a partner course below and prove the skill through an assessment.</div></div>',unsafe_allow_html=True)
        if missing and st.button("Explore partner courses for my skill gap →",type="primary"):
            go("Courses & Exams")

# ---------------- MY SKILLS ----------------
elif st.session_state.page == "My Skills":
    page_header("My Skills", "Your learning evidence in one place. Complete a partner course and assessment to turn a market requirement into an industry-validated skill.")
    validated = st.session_state.get("validated_skills", [])
    completed = st.session_state.get("completed_skills", [])
    if not validated and not completed:
        st.markdown('<div class="card"><h3>No validated skills yet</h3><div style="color:#667085;font-size:13px">Start a career assessment from Courses & Exams. Your result will appear here as an Industry Validated badge.</div></div>', unsafe_allow_html=True)
    for skill in validated:
        st.markdown(f'<div class="card" style="margin:10px 0;border-left:5px solid #A6E22E"><b>{skill}</b><span class="pill pill-green" style="float:right">Industry Validated</span><div style="font-size:12px;color:#667085;margin-top:5px">Company assessment passed</div></div>', unsafe_allow_html=True)
    for skill in completed:
        if skill not in validated:
            st.markdown(f'<div class="card" style="margin:10px 0"><b>{skill}</b><span class="pill pill-purple" style="float:right">Course Completed</span></div>', unsafe_allow_html=True)

# ---------------- COURSES + EXAMS ----------------
elif st.session_state.page == "Courses & Exams":
    page_header("Courses & Exams","A new learning layer for Skillyntra: partnered companies publish industry courses, learners enroll, and companies can run skill assessments.","PARTNER ECOSYSTEM")
    tab1,tab2,tab3=st.tabs(["🎓 Partner Courses","📝 Company Exams","🏢 Partner Console"])
    with tab1:
        st.markdown('<div class="notice">Partner courses are mapped to market-demand skills. Learners can discover a course, see its skill coverage, enroll, and move to a company assessment.</div>',unsafe_allow_html=True)
        all_courses=[]
        for _,r in courses.iterrows(): all_courses.append({"course":r.course,"company":r.institute,"skills":r.skills,"placement":r.placement_rate,"validation":r.employer_validation})
        all_courses += st.session_state.partner_courses
        query=st.text_input("Search courses or skills",placeholder="e.g. Python, Power BI, PLC, AI...")
        filtered=all_courses
        if query:
            q=query.lower();filtered=[r for r in all_courses if q in (str(r['course'])+' '+str(r['company'])+' '+str(r['skills'])).lower()]
        cols=st.columns(3)
        for i,r in enumerate(filtered):
            with cols[i%3]:
                chips=''.join([f'<span class="skill-chip">{s}</span>' for s in split_skills(r['skills'])[:7]])
                st.markdown(f'<div class="course-card"><div class="course-accent"></div><div class="company">{r["company"]}</div><div class="course-name">{r["course"]}</div><div>{chips}</div><div style="display:flex;justify-content:space-between;margin-top:15px;font-size:11px"><span>Placement <b>{r["placement"]:.0f}%</b></span><span>Industry validation <b>{r["validation"]:.0f}/100</b></span></div></div>',unsafe_allow_html=True)
                if st.button("Enroll / View course",key=f"enroll_{i}",use_container_width=True):
                    if r["course"] not in st.session_state.enrolled: st.session_state.enrolled.append(r["course"])
                    st.success(f"Enrolled in {r['course']}")
        st.markdown(f'<div style="margin-top:15px;color:#667085;font-size:12px">{len(st.session_state.enrolled)} course(s) in your learning list.</div>',unsafe_allow_html=True)
    with tab2:
        st.markdown('<div class="exam-box"><div style="font-size:11px;font-weight:800;color:#6D4AFF">INDUSTRY ASSESSMENT</div><h3 style="font-family:Space Grotesk">Python for Data Analysis — Partner Skill Check</h3><p style="font-size:13px;color:#667085">A prototype assessment flow. Partner companies can publish assessments linked to their courses and use results as a skill-validation signal.</p></div>',unsafe_allow_html=True)
        if not st.session_state.exam_started:
            st.write("")
            c=st.columns(3)
            for col,(t,v) in zip(c,[("Questions","5 MCQs"),("Time","5 minutes"),("Result","Instant")]): col.markdown(card_stat(t,v,"Prototype assessment"),unsafe_allow_html=True)
            if st.button("Start assessment →",type="primary",use_container_width=True): st.session_state.exam_started=True;st.session_state.exam_submitted=False;st.rerun()
        elif not st.session_state.exam_submitted:
            with st.form("exam"):
                answers=[]
                for i, question in enumerate(DEFAULT_QUESTIONS, 1): answers.append(st.radio(f"{i}. {question['question']}", question["options"], key=f"q{i}"))
                if st.form_submit_button("Submit assessment",type="primary"):
                    st.session_state.exam_submitted=True
                    st.session_state.exam_answers=answers
                    st.rerun()
        else:
            result = grade_answers(DEFAULT_QUESTIONS, st.session_state.exam_answers)
            pct = result["score"]
            if result["passed"]:
                st.session_state.validated_skills = sorted(set(st.session_state.get("validated_skills", []) + result["demonstrated"]))
                st.markdown(f'<div class="successbox"><b>Assessment passed · Industry Validated</b><br>Your score: <b>{pct}%</b><br>Skills demonstrated: {", ".join(result["demonstrated"])}</div>',unsafe_allow_html=True)
            else: st.warning(f"Assessment score: {pct}%. Review the course and retry.")
            if result["improvement"]:
                st.markdown(f'<div class="notice">Needs improvement: {", ".join(result["improvement"])}</div>', unsafe_allow_html=True)
            if st.button("Retake assessment"): st.session_state.exam_submitted=False;st.rerun()
    with tab3:
        st.markdown('<div class="notice">🏢 <b>Partner console:</b> In production, verified companies receive an authenticated workspace to publish courses, define skills, create assessments, review results and send employer-validation signals back to Skillyntra.</div>',unsafe_allow_html=True)
        with st.form("partner_course"):
            c1,c2=st.columns(2)
            with c1: pc=st.text_input("Course name",placeholder="e.g. Applied AI for Manufacturing")
            with c2: company=st.text_input("Partner company",placeholder="e.g. Industry Partner Pvt. Ltd.")
            skills_in=st.text_input("Skills taught",placeholder="Python, Machine Learning, SQL")
            c3,c4=st.columns(2)
            with c3: pr=st.slider("Expected placement relevance",0,100,80)
            with c4: evv=st.slider("Industry validation",0,100,85)
            if st.form_submit_button("Publish partner course",type="primary"):
                if pc and company:
                    st.session_state.partner_courses.append({"course":pc,"company":company,"skills":skills_in,"placement":pr,"validation":evv});st.success(f"{pc} published by {company}")
                else: st.error("Add both course name and company.")

# ---------------- INSTITUTE ----------------
elif st.session_state.page == "Institute":
    page_header("Curriculum Alignment","See whether a course covers the skills the market is asking for, then turn the gap into curriculum actions.")
    cl=sorted(courses.course.tolist()); course=st.selectbox("Training program",cl);st.session_state.course=course
    taught,placement,align,health,missing=course_result(course)
    c=st.columns(4)
    for col,(t,v,n) in zip(c,[("Industry alignment",f"{align}%","Against top market skills"),("Placement rate",f"{placement:.0f}%","Prototype outcome"),("Course health",f"{health}/100","Composite signal"),("Skills taught",len(taught),"Current curriculum")]):col.markdown(card_stat(t,v,n),unsafe_allow_html=True)
    l,r=st.columns(2)
    with l:
        st.markdown('<div class="section-title">Skills currently taught</div>',unsafe_allow_html=True)
        for s in taught:st.markdown(f'<span class="skill-chip">✓ {s}</span>',unsafe_allow_html=True)
    with r:
        st.markdown('<div class="section-title">Missing / under-covered</div>',unsafe_allow_html=True)
        for s in missing[:8]:st.markdown(f'<span class="skill-chip" style="background:#FFF1F3;color:#C01048">+ {s}</span>',unsafe_allow_html=True)
    status="Relevant" if align>=70 else ("Needs Update" if align>=40 else "At Risk / Review")
    st.markdown(f'<div class="notice" style="margin-top:18px">Course status: <b>{status}</b> · Skillyntra recommends curriculum changes based on observed market demand.</div>',unsafe_allow_html=True)
    st.markdown('<div class="section-title">Recommended updates</div>',unsafe_allow_html=True)
    for s in missing[:6]:st.markdown(f'<div class="card" style="margin:8px 0"><b>Add / strengthen {s}</b><div style="font-size:12px;color:#667085;margin-top:4px">Observed in current job-market signals; consider adding it to the learning outcomes and assessment.</div></div>',unsafe_allow_html=True)

# ---------------- GOVERNMENT ----------------
elif st.session_state.page == "Government":
    page_header("District Training Planner","Use demand versus training capacity to prioritize where new or expanded training should happen.")
    dist=st.selectbox("District",sorted(capacity.district.unique()));x=cap_metrics(capacity[capacity.district.eq(dist)])
    if not x.empty:
        p=x.iloc[0];c=st.columns(4)
        for col,(t,v,n) in zip(c,[("Priority skill",p.skill,"Largest capacity gap"),("Largest gap",int(p.gap),"Learners"),("Skills reviewed",len(x),"District signals"),("Status",p.status,"Planning signal")]):col.markdown(card_stat(t,v,n),unsafe_allow_html=True)
        fig=px.bar(x,x="skill",y=["estimated_demand","annual_capacity"],barmode="group",labels={"skill":"","value":"Learners","variable":""},color_discrete_sequence=["#6D4AFF","#A6E22E"])
        st.plotly_chart(styled_fig(fig,390),use_container_width=True,config={"displayModeBar":False})
        show=x.rename(columns={"district":"District","skill":"Skill","estimated_demand":"Industry Demand","annual_capacity":"Training Capacity","gap":"Gap","status":"Status"})
        st.dataframe(show,use_container_width=True,hide_index=True)
        for _,r in x.head(4).iterrows():st.markdown(f'<div class="card" style="margin:8px 0"><b>{r.skill}</b> — {"Increase / prioritize training capacity" if r.gap>0 else ("Review for potential oversupply" if r.gap<0 else "Capacity balanced")}.</div>',unsafe_allow_html=True)

# ---------------- EVIDENCE ----------------
else:
    demand = service_skill_demand(jobs)
    emap = dict(zip(employer.skill, employer.employer_validation))
    emap.update(st.session_state.overrides)
    ev = demand.copy()
    ev["employer_validation"] = ev.skill.map(emap).fillna(50)
    conf = dict(zip(employer.skill, employer.confidence))
    ev["confidence"] = ev.skill.map(conf).fillna("Medium")
    # Use normalized evidence scoring (consistent with analytics.py)
    job_signals = ev["job_signals"]
    if job_signals.max() > job_signals.min():
        job_signals_norm = (job_signals - job_signals.min()) / (job_signals.max() - job_signals.min()) * 100
    else:
        job_signals_norm = pd.Series(50, index=job_signals.index)
    confidence_map = {"High": 100, "Medium": 60, "Low": 35}
    confidence_norm = ev["confidence"].map(confidence_map).fillna(60)
    ev["evidence_score"] = (job_signals_norm * 0.45 + ev["employer_validation"] * 0.35 + confidence_norm * 0.20).round(1)
    ev = ev.sort_values("evidence_score", ascending=False)
    page_header("Evidence & Validation", "Skillyntra keeps the signals behind recommendations visible and gives employers a future-ready way to validate skill relevance.")
    st.dataframe(ev.rename(columns={"skill": "Skill", "job_signals": "Job Signals", "employer_validation": "Employer Validation", "confidence": "Confidence", "evidence_score": "Evidence Score"}).head(30), use_container_width=True, hide_index=True, height=500)
    st.markdown('<div class="section-title">Employer validation simulator</div>',unsafe_allow_html=True)
    with st.form("validation"):
        s=st.selectbox("Skill",sorted(demand.skill.tolist()));score=st.slider("Current industry relevance",0,100,int(emap.get(s,50)))
        if st.form_submit_button("Submit validation",type="primary"):
            st.session_state.overrides[s]=score;st.success(f"Validation recorded for {s}: {score}/100");st.rerun()
    st.markdown('<div class="notice" style="margin-top:18px">Production path: verified partner companies → authenticated course/assessment workspace → assessment results → employer validation → refreshed SKILLYNTRA intelligence.</div>',unsafe_allow_html=True)

st.markdown('<div style="margin-top:45px;padding-top:16px;border-top:1px solid #E4E7EC;color:#98A2B3;font-size:10px">Skillyntra · SIH 2026 · PS 26134 · Prototype uses synthetic labour-market demo data.</div>',unsafe_allow_html=True)
