"use client";
import { useState } from "react";
import AgentPanel from "../components/agent_panel";
import FederatedPanel from "../components/federated_panel";
import PrivacyPanel from "../components/privacy_panel";
import VisionPanel from "../components/vision_panel";
import type { VisionResponse } from "../lib/api";
export default function HomePage() {
 const [vision, setVision] = useState<VisionResponse | null>(null);
 return <main className="container"><header className="header"><span className="eyebrow">VigiloForge · Secured Crop Detective</span>
   <h1>Smarter Farming. Private by Design.</h1><p>Privacy-first agricultural intelligence • Cal Hacks 13.0 prototype</p></header>
   <div className="grid"><div className="stack"><VisionPanel onAnalyzed={setVision}/><AgentPanel vision={vision}/></div>
   <div className="stack"><PrivacyPanel/><FederatedPanel/></div></div>
   <footer>Prototype: anomaly measurements and synthetic federated learning are not validated crop disease diagnosis or certified data security.</footer>
 </main>;
}
