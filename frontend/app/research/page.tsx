import ResearchPanel from "../../components/research_panel";
export default function ResearchPage() {
  return (
    <main className="container route-page">
      <p className="eyebrow">Evidence library</p>
      <h1>Trace the evidence.</h1>
      <p className="hero-copy">
        Explore the passages actually indexed by the backend. Every returned
        passage links to its recorded source; retrieval does not establish
        scientific correctness.
      </p>
      <ResearchPanel />
      <section className="panel support">
        <h2>Build a credible source library</h2>
        <p>
          Start with university extension and government guidance. The following
          are suggested source organizations, not evidence retrieved or verified
          by this application:
        </p>
        <ul>
          <li>
            <a href="https://ipm.ucanr.edu/" target="_blank" rel="noreferrer">
              UC Integrated Pest Management
            </a>
          </li>
          <li>
            <a
              href="https://extension.umn.edu/"
              target="_blank"
              rel="noreferrer"
            >
              University of Minnesota Extension
            </a>
          </li>
          <li>
            <a href="https://www.usda.gov/" target="_blank" rel="noreferrer">
              USDA
            </a>
          </li>
        </ul>
        <p className="muted">No LLM integration was added in this update.</p>
      </section>
    </main>
  );
}
