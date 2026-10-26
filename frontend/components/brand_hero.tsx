"use client";

import Image from "next/image";
import { useState } from "react";

export default function BrandHero() {
  const [missingLogo, setMissingLogo] = useState(false);

  return (
    <header className="hero" id="home">
      <div className="hero-topline">
        <p className="eyebrow">VigiloForge · Secured Crop Detector</p>
        <span className="brand-tag">Cal Hacks 13.0</span>
      </div>
      <div className={`logo-stage${missingLogo ? " logo-stage-pending" : ""}`}>
        {!missingLogo ? (
          <>
            <Image
              className="brand-banner"
              src="/vigiloforge-logo.png"
              alt="VigiloForge — Secured Crop Detector. Secured Farming. Private by Design. Forged by Multiple Agents."
              width={2172}
              height={724}
              sizes="(max-width: 1320px) 100vw, 1260px"
              preload
              unoptimized
              onError={() => setMissingLogo(true)}
            />
            <span className="logo-sheen" aria-hidden="true" />
            <span className="logo-flare" aria-hidden="true" />
          </>
        ) : (
          <p className="logo-notice">Logo asset missing: add vigiloforge-logo.png to frontend/public.</p>
        )}
        <span className="logo-stage-line" aria-hidden="true" />
      </div>
      <div className="hero-content">
        <div>
          <p className="eyebrow">Observe. Investigate. Stay in control.</p>
          <h1>
            Smarter Farming.
            <br />
            <span>Private by Design.</span>
          </h1>
          <p className="hero-copy">
            A closer look at your crops. A clearer view of the evidence.
            Investigate visible leaf changes while choosing how your
            observations are shared.
          </p>
          <div className="actions">
            <a className="button" href="#vision">
              Start crop analysis <span aria-hidden="true">↗</span>
            </a>
            <a className="button secondary" href="#dashboard">
              Open dashboard
            </a>
          </div>
        </div>
        <aside className="hero-principles" aria-label="Platform principles">
          <p className="eyebrow">Forged by Multiple Agents</p>
          <p>
            <span aria-hidden="true">01</span> Observe with computer vision
          </p>
          <p>
            <span aria-hidden="true">02</span> Investigate public evidence
          </p>
          <p>
            <span aria-hidden="true">03</span> Share by explicit permission
          </p>
          <a href="#privacy">Explore your privacy controls →</a>
        </aside>
      </div>
      <p className="muted hero-disclaimer">
        Research prototype. Image observations are not a validated disease
        diagnosis. Local stages and external AI integrations are labeled
        separately.
      </p>
    </header>
  );
}
