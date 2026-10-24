"use client";

import { useState } from "react";
import VisionPanel from "../components/vision_panel";
import AgentPanel from "../components/agent_panel";
import PrivacyPanel from "../components/privacy_panel";
import FederatedPanel from "../components/federated_panel";
import TelemetryPanel from "../components/telemetry_panel";
import type { VisionResponse } from "../lib/api";

export default function HomePage() {
  const [vision, setVision] = useState<VisionResponse | null>(null);

  return (
    <main className="container">
      <header className="header">
        <p className="eyebrow">
          VigiloForge Secured Crop Detective
        </p>

        <h1>Smarter Farming - Private by Design - Forged by Multiple Agents</h1>

        <p>
          Privacy-first agricultural intelligence powered by
          computer vision, scientific research, and AI agents.
        </p>
      </header>

      <div className="grid">
        <div className="stack">
          <section className="panel">
            <VisionPanel onAnalyzed={setVision} />
          </section>

          <section className="panel">
            <AgentPanel vision={vision} />
          </section>

          <section className="panel">
            <PrivacyPanel />
          </section>
        </div>

        <div className="stack">
          <section className="panel">
            <FederatedPanel />
          </section>

          <section className="panel">
            <TelemetryPanel />
          </section>
        </div>
      </div>

      <footer>
        VigiloForge SCD — Cal Hacks 13.0
      </footer>
    </main>
  );
}