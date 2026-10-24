"use client";
import { useState } from "react";
import { requestJSON } from "../lib/api";
export default function CustomerChat() {
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  async function ask(topic: string) {
    setBusy(true);
    try {
      const result = await requestJSON<{ answer: string }>("/support/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic }),
      });
      setAnswer(result.answer);
    } catch (e) {
      setAnswer(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel support" id="pilot">
      <p className="eyebrow">Get started</p>
      <h2>Grow with VigiloForge</h2>
      <p>
        Explore the prototype or learn how its privacy controls work. Pilot
        enrollment is coming soon.
      </p>
      <div className="actions">
        {["analysis", "privacy", "offline", "pilot"].map((topic) => (
          <button
            className="secondary"
            key={topic}
            disabled={busy}
            onClick={() => void ask(topic)}
          >
            {topic}
          </button>
        ))}
      </div>
      <p role="status">{answer}</p>
      <p className="muted">
        Local FAQ responses. No hosted AI assistant is invoked.
      </p>
    </section>
  );
}
