"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { requestJSON } from "../../lib/api";
export default function PlansPage() {
  const [status, setStatus] = useState("");
  useEffect(() => {
    let active = true;
    requestJSON<{ message: string }>("/billing/status")
      .then((value) => {
        if (active) setStatus(value.message);
      })
      .catch((e) => {
        if (active) setStatus(String(e));
      });
    return () => {
      active = false;
    };
  }, []);
  return (
    <main className="container route-page">
      <p className="eyebrow">Plans & access</p>
      <h1>
        Start with evidence.
        <br />
        <span>Keep control.</span>
      </h1>
      <p className="hero-copy">
        All current hackathon features are available on the free prototype.
        There is no payment checkout and no active paid subscription.
      </p>
      <div className="grid">
        <section className="panel">
          <span className="brand-tag">Available now</span>
          <h2>Research prototype</h2>
          <p className="plan-price">Free</p>
          <ul>
            <li>Leaf observations and heatmap</li>
            <li>Public-reference keyword retrieval</li>
            <li>Consent-controlled agent requests when configured</li>
            <li>Synthetic federated learning demonstration</li>
            <li>Mobile photo history and explicit sync</li>
            <li>Pseudonymous private workspace</li>
          </ul>
          <Link className="button" href="/login">
            Create or open a workspace
          </Link>
        </section>
        <section className="panel">
          <span className="brand-tag">Planned · not for sale</span>
          <h2>Grower pilot</h2>
          <p>
            Potential future services include managed telemetry, supported
            deployments, and larger research libraries.
          </p>
          <p className="muted">
            Pricing, billing, service limits, and support terms have not been
            configured. No purchase or paid entitlement can be created here. A
            payment provider would handle payment information if billing is
            added.
          </p>
        </section>
      </div>
      <p className="muted" role="status">
        {status}
      </p>
    </main>
  );
}
