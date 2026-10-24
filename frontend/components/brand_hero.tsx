"use client";
import Image from "next/image";
import { useState } from "react";
export default function BrandHero() {
  const [missingLogo, setMissingLogo] = useState(false);
  return (
    <header className="hero" id="home">
      <p className="eyebrow">Cal Hacks 13.0 · Agricultural intelligence</p>
      {!missingLogo ? (
        <Image
          className="brand-banner"
          src="/vigiloforge-logo.png"
          alt="Original VigiloForge banner"
          width={1400}
          height={420}
          preload
          unoptimized
          onError={() => setMissingLogo(true)}
        />
      ) : (
        <p className="logo-notice">
          Original banner pending. Add your artwork at
          frontend/public/vigiloforge-logo.png.
        </p>
      )}
      <h1>
        Smarter Farming.
        <br />
        <span>Private by Design.</span>
      </h1>
      <p className="hero-copy">
        Investigate crop-health uncertainty with visible leaf observations,
        public scientific evidence, and permission-controlled agent workflows.
      </p>
      <div className="actions">
        <a className="button" href="#vision">
          Start crop analysis <span aria-hidden="true">↗</span>
        </a>
        <a className="button secondary" href="#dashboard">
          Open dashboard
        </a>
      </div>
      <div className="hero-notes">
        <p>
          <strong>Your observations.</strong> Your sharing choices.
        </p>
        <p>
          <strong>Forged by Multiple Agents.</strong> Local stages and optional
          hosted integrations.
        </p>
      </div>
      <p className="muted">
        Research prototype. Image observations are not a validated disease
        diagnosis.
      </p>
    </header>
  );
}
