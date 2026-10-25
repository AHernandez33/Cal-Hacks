"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { requestJSON } from "../../lib/api";
const tiers = [
 {name:"Free",price:"$0",daily:"10 photos/day after email invitation; 1 introductory photo",detail:"Standard research assistant",color:"Available prototype"},
 {name:"Gold",price:"$4.99",daily:"100 photos/day",detail:"Expanded daily usage",color:"Planned"},
 {name:"Platinum",price:"$19.99",daily:"Unlimited photos under fair-use safeguards",detail:"Proposed advanced LLM",color:"Planned"},
];
export default function PlansPage(){
 const [message,setMessage]=useState("");
 useEffect(()=>{requestJSON<{message:string}>("/billing/status").then(v=>setMessage(v.message)).catch(()=>setMessage("Billing status is unavailable."));},[]);
 return <main className="container route-page"><p className="eyebrow">Proposed membership</p>
 <h1>Start with one scan.<br/><span>Grow with confidence.</span></h1>
 <p className="hero-copy">Planned launch: one introductory scan, then an email invitation to receive your results and unlock up to ten free scans daily. Gold and Platinum would unlock higher limits. These entitlements and email delivery are not yet enabled; this prototype currently has no card checkout.</p>
 <div className="integration-grid">{tiers.map(t=><section key={t.name} className="panel">
 <span className="brand-tag">{t.color}</span><h2 style={{marginTop:20}}>{t.name}</h2>
 <p className="plan-price">{t.price}<span style={{fontSize:13,color:"#a6bcb2"}}>{t.price==="$0"?"":"/month"}</span></p>
 <p><strong>{t.daily}</strong></p><p className="muted">{t.detail}</p>
 <Link className="button secondary" href="/login">{t.name==="Free"?"Open a workspace":"View account access"}</Link>
 </section>)}</div>
 <section className="panel support"><h2>Pricing transparency</h2><p>Plans and prices are proposals. No subscriptions, automatic emails, unlimited capacity guarantee, or stronger paid model are currently active. Payment cards must be handled by a PCI-compliant hosted checkout provider; VigiloForge must never collect or store raw card numbers.</p><p>Current access is via a private workspace key, not yet email and password. A production launch requires verified email authentication, secure account recovery, server-enforced quotas, consented email delivery, and webhook-verified billing entitlements.</p><p className="muted" role="status">{message}</p></section>
 </main>;
}