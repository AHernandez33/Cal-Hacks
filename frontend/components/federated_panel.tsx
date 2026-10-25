"use client";
import { useState } from "react";
import { requestJSON } from "../lib/api";
import MetricChart from "./metric_chart";
type Metrics = {
  validation_loss: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
};
type Round = Metrics & { round: number; training_loss: number };
type DemoResult = {
  dataset: string;
  simulation: string;
  participating_clients: string[];
  excluded_clients: string[];
  history: Round[];
  federated_final: Round;
  local_only_baseline: Metrics;
  privacy: string;
  holdout_samples: number;
};
const CLIENTS = [
  {
    id: "greenhouse_a",
    label: "Simulated Greenhouse A",
    description: "Generated dataset with the lowest discoloration shift.",
  },
  {
    id: "greenhouse_b",
    label: "Simulated Greenhouse B",
    description: "Generated dataset with a moderate discoloration shift.",
  },
  {
    id: "greenhouse_c",
    label: "Simulated Greenhouse C",
    description: "Generated dataset with the highest discoloration shift.",
  },
];
const label = (id: string) => CLIENTS.find((c) => c.id === id)?.label || id;
const percent = (value: number) => `${(value * 100).toFixed(1)}%`;
export default function FederatedPanel() {
  const [consent, setConsent] = useState<Record<string, boolean>>({});
  const [result, setResult] = useState<DemoResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function run() {
    setBusy(true);
    setError("");
    setResult(null);
    try {
      setResult(
        await requestJSON<DemoResult>("/federated/demo", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            consent,
            rounds: 10,
            local_epochs: 2,
            samples_per_client: 120,
          }),
        }),
      );
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel">
      <p className="eyebrow">Learning laboratory · synthetic demonstration</p>
      <h2>How models learn together</h2>
      <p>
        These greenhouses are three{" "}
        <strong>simulated datasets on this computer</strong>, not connected
        buildings. Each selected client trains a small model locally; FedAvg
        averages its model parameters into a shared model.
      </p>
      <p className="muted">
        Each has 120 fabricated observations. Nothing here measures real farm
        accuracy. Selecting a client authorizes only this synthetic run,
        independently of your real-data training preference.
      </p>
      <div className="greenhouse-cards">
        {CLIENTS.map((client) => (
          <label
            className={`greenhouse-card ${consent[client.id] ? "selected" : ""}`}
            key={client.id}
          >
            <input
              type="checkbox"
              disabled={busy}
              checked={consent[client.id] === true}
              onChange={(e) =>
                setConsent((previous) => ({
                  ...previous,
                  [client.id]: e.target.checked,
                }))
              }
            />
            <span>
              <strong>{client.label}</strong>
              <small>{client.description}</small>
              <small>
                {consent[client.id]
                  ? "Opted in for this run"
                  : "Excluded until you opt in"}
              </small>
            </span>
          </label>
        ))}
      </div>
      <button
        disabled={busy || !CLIENTS.some((c) => consent[c.id])}
        onClick={() => void run()}
      >
        {busy ? "Training ten rounds…" : "Run 10 federated rounds"}
      </button>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {result && (
        <div aria-live="polite">
          <h3>Results from your completed run</h3>
          <p>
            Trained: {result.participating_clients.map(label).join(", ")}.
            Excluded: {result.excluded_clients.map(label).join(", ") || "None"}.
          </p>
          <div className="metric-cards">
            {[
              {
                name: "Accuracy",
                value: result.federated_final.accuracy,
                meaning: "Fraction of correct synthetic holdout predictions.",
              },
              {
                name: "Precision",
                value: result.federated_final.precision,
                meaning:
                  "Of predicted positive labels, how many were positive.",
              },
              {
                name: "Recall",
                value: result.federated_final.recall,
                meaning: "Of actual positive labels, how many the model found.",
              },
              {
                name: "F1",
                value: result.federated_final.f1,
                meaning: "Balance between precision and recall.",
              },
            ].map((m) => (
              <article key={m.name}>
                <span>{m.name}</span>
                <strong>{percent(m.value)}</strong>
                <small>{m.meaning}</small>
              </article>
            ))}
          </div>
          <MetricChart
            title="Learning over ten rounds"
            description="Loss measures prediction error on fabricated labels. Lower is better; validation loss uses separate holdout examples."
            rounds={result.history.map((r) => r.round)}
            series={[
              {
                label: "Training loss",
                color: "#00ed64",
                values: result.history.map((r) => r.training_loss),
              },
              {
                label: "Validation loss",
                color: "#00f5ff",
                values: result.history.map((r) => r.validation_loss),
              },
            ]}
          />
          <MetricChart
            title="Shared model versus local-only baseline"
            description="F1 balances precision and recall. A shared model is not guaranteed to beat the local-only model."
            percentage
            rounds={result.history.map((r) => r.round)}
            series={[
              {
                label: "Federated F1",
                color: "#00ed64",
                values: result.history.map((r) => r.f1),
              },
              {
                label: "Local-only final F1",
                color: "#e2c46c",
                values: result.history.map(() => result.local_only_baseline.f1),
              },
            ]}
          />
          <p>
            The shared model’s final F1 is{" "}
            {(
              (result.federated_final.f1 - result.local_only_baseline.f1) *
              100
            ).toFixed(1)}{" "}
            percentage points relative to the local-only baseline, on{" "}
            {result.holdout_samples} held-out synthetic examples.
          </p>
          <div className="table-scroll">
            <table>
              <caption>Final model comparison</caption>
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Accuracy</th>
                  <th>Precision</th>
                  <th>Recall</th>
                  <th>F1</th>
                  <th>Loss</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { name: "Federated", m: result.federated_final },
                  { name: "Local only", m: result.local_only_baseline },
                ].map(({ name, m }) => (
                  <tr key={name}>
                    <th scope="row">{name}</th>
                    <td>{percent(m.accuracy)}</td>
                    <td>{percent(m.precision)}</td>
                    <td>{percent(m.recall)}</td>
                    <td>{percent(m.f1)}</td>
                    <td>{m.validation_loss.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <details>
            <summary>Exact training history</summary>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Round</th>
                    <th>Training loss</th>
                    <th>Validation loss</th>
                    <th>F1</th>
                  </tr>
                </thead>
                <tbody>
                  {result.history.map((row) => (
                    <tr key={row.round}>
                      <td>{row.round}</td>
                      <td>{row.training_loss.toFixed(4)}</td>
                      <td>{row.validation_loss.toFixed(4)}</td>
                      <td>{percent(row.f1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
          <p className="muted">{result.privacy}</p>
        </div>
      )}
      <details className="model-details">
        <summary>What model is actually running?</summary>
        <p>
          LeafRiskMLP: five numerical inputs → 64 → 32 → 16 → one output. It
          learns fabricated binary labels with PyTorch. Mean hue is normalized
          in this demonstration.
        </p>
        <p>
          Clients train for two local epochs per round. Sample-weighted FedAvg
          combines parameters. The baseline trains only on one selected client,
          evaluated on the same holdout.
        </p>
        <p className="muted">
          No physical greenhouse connections, secure aggregation, or
          differential privacy are implemented. This compute-intensive demo runs
          only through a loopback backend connection.
        </p>
      </details>
    </section>
  );
}
