"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

export default function LaunchIntro() {
  const [visible, setVisible] = useState(false);

  // Replays on every full reload; respects the user's reduced-motion setting.
  useEffect(() => {
    if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      const frame = requestAnimationFrame(() => setVisible(true));
      return () => cancelAnimationFrame(frame);
    }
  }, []);

  if (!visible) return null;

  return (
    <div
      className="launch-intro"
      aria-hidden="true"
      onAnimationEnd={(event) => {
        if (event.target === event.currentTarget) setVisible(false);
      }}
    >
      <div className="launch-door launch-door-left" />
      <div className="launch-door launch-door-right" />
      <div className="launch-seam" />
      <div className="launch-emblem">
        <Image
          src="/vigiloforge-logo.png"
          alt=""
          width={720}
          height={240}
          priority
          unoptimized
        />
        <span className="launch-glimmer" />
        <span className="launch-star" />
      </div>
    </div>
  );
}
