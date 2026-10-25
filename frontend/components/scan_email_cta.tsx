"use client";
import { useState } from "react";
import Link from "next/link";
import { getAccessToken, requestJSON, type VisionResponse } from "../lib/api";

export default function ScanEmailCTA({ result }: { result: VisionResponse }) {
 const [email,setEmail]=useState("");
 const [consent,setConsent]=useState(false);
 const [busy,setBusy]=useState(false);
 const [message,setMessage]=useState("");
 const [sent,setSent]=useState(false);
 const signedIn=Boolean(getAccessToken());
 async function send(e: React.FormEvent<HTMLFormElement>) {
   e.preventDefault();
   if(!consent || !signedIn) return;
   setBusy(true);setMessage("");
   try {
     const reply=await requestJSON<{sent:boolean;message:string}>("/reports/email",{
       method:"POST",headers:{"Content-Type":"application/json"},
       body:JSON.stringify({
         email,consent_to_email:consent,
         yellow_fraction:result.features.yellow_fraction,
         brown_fraction:result.features.brown_fraction,
         anomaly_score:result.anomaly_score,
         leaf_coverage_fraction:result.leaf_coverage_fraction
       })
     });
     setSent(reply.sent);setMessage(reply.message);
   } catch(err) {setMessage(err instanceof Error?err.message:"Could not send report");}
   finally {setBusy(false);}
 }
 return <section className="scan-cta" aria-label="Email your crop results">
   <p className="eyebrow">Your crop scan is complete</p>
   <h3>Your crop insights shouldn't stop here.</h3>
   <p>See your observations above. Receive a numerical summary in your inbox, and explore the planned Free tier with up to 10 daily scans when account quotas launch.</p>
   {!signedIn && <p className="warning">To prevent unwanted email, sign in with your private workspace first. Email/password registration and automatic free-tier unlock are not enabled yet. <Link href="/login">Open workspace sign in</Link></p>}
   <form onSubmit={e=>void send(e)}>
     <label className="field">Email address
       <input type="email" autoComplete="email" value={email} maxLength={254} onChange={e=>setEmail(e.target.value)} required placeholder="you@example.com"/>
     </label>
     <label className="consent">
       <input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/>
       I agree to receive this one crop observation report by email. No photograph will be emailed.
     </label>
     <div className="actions">
       <button type="submit" disabled={busy || sent || !consent || !signedIn}>{busy?"Sending…":sent?"Report submitted":"Email my crop results"}</button>
       <Link href="/plans" className="button secondary">Explore Free, Gold & Platinum</Link>
     </div>
     <p role="status" className={sent?"muted":"warning"}>{message}</p>
   </form>
   <p className="muted">No marketing signup is created. SMTP delivery requires server setup. Results remain visible without providing an email.</p>
 </section>;
}
