import FederatedPanel from "../../components/federated_panel";
export default function FederatedPage() {
  return (
    <main className="container route-page">
      <p className="eyebrow">Federated learning models</p>
      <h1>
        One shared model.
        <br />
        <span>Three simulated clients.</span>
      </h1>
      <p className="hero-copy">
        Explore the actual training run, see how its error changes, and compare
        the shared model with a local-only baseline. All results use fabricated
        data.
      </p>
      <FederatedPanel />
    </main>
  );
}
