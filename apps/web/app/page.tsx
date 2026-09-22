import Link from "next/link";

const roles = [
  ["student", "Student", "Find your next skill and opportunity."],
  ["company", "Partner Company", "Publish courses and validate talent."],
  ["institute", "Training Institute", "Align curriculum with demand."],
  ["government", "Government", "Plan training where shortages emerge."],
];

export default function LandingPage() {
  return (
    <main className="page">
      <section className="landing">
        <div>
          <div className="brand-mark">Industry intelligence · learning · opportunity</div>
          <h1>From skills<br /><span>to opportunities.</span></h1>
          <p className="lede">Skillyntra connects labour-market demand, skill gaps, industry-aligned learning, company assessments and employment outcomes in one intelligent ecosystem.</p>
        </div>
        <div className="role-panel">
          <h2>Enter demo mode</h2>
          <p>Choose a workspace to explore the product story from a different point of view.</p>
          <div className="role-grid">
            {roles.map(([slug, name, description]) => (
              <Link className="role-link" href={`/${slug}`} key={slug}>
                <span><strong>{name}</strong><small>{description}</small></span><span aria-hidden="true">-&gt;</span>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
