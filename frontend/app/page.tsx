"use client";
import { useState } from "react";
import IntegrationStatus from "../components/integration_status";
import Link from "next/link";
import BrandHero from "../components/brand_hero";
import VisionPanel from "../components/vision_panel";
import AgentPanel from "../components/agent_panel";
import PrivacyPanel from "../components/privacy_panel";
import FederatedPanel from "../components/federated_panel";
import TelemetryPanel from "../components/telemetry_panel";
import OfflinePanel from "../components/offline_panel";
import CustomerChat from "../components/customer_chat";
import PWARegister from "../components/pwa_register";
import type { VisionResponse } from "../lib/api";
export default function HomePage() {
  const [vision, setVision] = useState<VisionResponse | null>(null);
  return (
    <main className="container">
      <PWARegister />
      <BrandHero />
      <section className="overview" aria-label="Platform overview">
        <article>
          <p className="eyebrow">01 / Observe</p>
          <h2>Look closer.</h2>
          <p>
            Capture leaf images and measure visible discoloration locally on
            your configured backend.
          </p>
        </article>
        <article>
          <p className="eyebrow">02 / Investigate</p>
          <h2>Follow evidence.</h2>
          <p>
            Coordinator → Investigator → Researcher → Planner. Rule-based local
            steps are labeled separately from remote agents.
          </p>
        </article>
        <article>
          <p className="eyebrow">03 / Collaborate</p>
          <h2>Learn together.</h2>
          <p>
            Explore federated averaging across three simulated greenhouses
            without claiming field-validated performance.
          </p>
        </article>
      </section>
      <div id="dashboard" className="section-heading">
        <p className="eyebrow">Observation workspace</p>
        <h2>Crop intelligence dashboard</h2>
      </div>
      <div className="grid">
        <div className="stack">
          <div id="vision">
            <VisionPanel onAnalyzed={setVision} />
          </div>
          <AgentPanel vision={vision} />
          <div id="field">
            <OfflinePanel onAnalyzed={setVision} />
          </div>
        </div>
        <div className="stack">
          <div id="privacy">
            <PrivacyPanel />
          </div>
          <p>
            <Link href="/federated">Open the learning models page →</Link>
          </p>
          <FederatedPanel />
          <TelemetryPanel />
        </div>
      </div>
      <IntegrationStatus />
      <CustomerChat />
      <footer>
        VigiloForge SCD · Cal Hacks 13.0 · Heuristic observations, transparent
        uncertainty.
      </footer>
    </main>
  );
}
