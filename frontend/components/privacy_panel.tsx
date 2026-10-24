"use client";
import { useState } from "react";
export default function PrivacyPanel() {
 const [external, setExternal] = useState(false);
 return <section className="panel"><h2>Privacy transparency</h2>
  <p>Collaborative training is OFF by default in the federated demo. Opt-in occurs separately for each simulated greenhouse.</p>
  <label className="checklist"><input type="checkbox" checked={external} onChange={e=>setExternal(e.target.checked)}/> Acknowledge external AI service use (visual demo only)</label>
  <p className="muted">This checkbox is informational UI state only. It does not change your server-side privacy controls or authorize any request. Fetch.ai submissions are controlled in the agent panel and must be subject to server-side authorization before public deployment.</p>
  <p className="muted">Do not enter farm coordinates, personal data or private images into agent requests.</p>
 </section>;
}
