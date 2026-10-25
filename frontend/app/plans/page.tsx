"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { requestJSON } from "../../lib/api";
const tiers = [
 {name:"Free",price:"$0",daily:"Regular prototype access; no email scan gate",detail:"Standard research assistant",color:"Available prototype"},
 {name:"Gold",price:"$4.99",daily:"Proposed higher usage limits",detail:"Expanded daily usage",color:"Planned"},
 {name:"Platinum",price:"$19.99",daily:"Proposed extended usage under fair-use safeguards",detail:"Proposed expanded investigation tools",color:"Planned"},
];
export default function PlansPage(){
 const [message,setMessage]=useState("");
 useEffect(()=>{requestJSON<{message:string}>("/billing/status").then(v=>setMessage(v.message)).catch(()=>setMessage("Billing status is unavailable."));},[]);
 return <main className="container route-page"><p className="eyebrow">Proposed membership</p>
 <h1>Start with evidence.<br/><span>Grow with confidence.</span></h1>
 <p className="hero-copy">Current prototype features are free to use with regular access. Gold and Platinum are proposed subscription tiers only: no payment checkout, paid entitlements, or daily scan quotas are active. Signing in to a hosted workspace uses its private key, without an email scan gate.</p>
 <div className="integration-grid">{tiers.map(t=><section key={t.name} className="panel">
 <span className="brand-tag">{t.color}</span><h2 style={{marginTop:20}}>{t.name}</h2>
 <p className="plan-price">{t.price}<span style={{fontSize:13,color:"#a6bcb2"}}>{t.price==="$0"?"":"/month"}</span></p>
 <p><strong>{t.daily}</strong></p><p className="muted">{t.detail}</p>
 <Link className="button secondary" href="/login">{t.name==="Free"?"Open a workspace":"View account access"}</Link>
 </section>)}</div>
 <section className="panel support"><h2>Pricing transparency</h2><p>Plans and prices are proposals. No paid subscriptions, automatic emails, unlimited capacity guarantee, or stronger paid model are currently active. Payment cards must be handled by a PCI-compliant hosted checkout provider; VigiloForge must never collect or store raw card numbers.</p><p>Hosted account access uses a private workspace key. Activating a future paid plan would require a configured payment provider and server-verified billing entitlements. These plan cards do not charge a card or change your current access.</p><p className="muted" role="status">{message}</p></section>
 </main>;
}