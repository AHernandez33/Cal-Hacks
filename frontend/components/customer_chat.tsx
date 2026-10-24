"use client";
import {useState} from "react";
import {requestJSON} from "../lib/api";
export default function CustomerChat(){const [question,setQuestion]=useState('');const [reply,setReply]=useState('');const [busy,setBusy]=useState(false);
 const routes=[{label:'Start free analysis',href:'#vision'},{label:'Join pilot (coming soon)',href:'#pilot'},{label:'Learn about privacy',href:'#privacy'}];
 async function send(){setBusy(true);setReply('');try{const value=await requestJSON<Record<string,unknown>>('/agents/creao',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:question})});setReply(JSON.stringify(value,null,2));}catch(e){setReply(String(e));}finally{setBusy(false);}}
 return <section className="panel" id="pilot"><h2>Ask VigiloForge — Customer assistant</h2><p className="muted">CREAO integration requires a verified hosted agent, credentials, and explicit consent in Privacy controls. No message is sent automatically.</p><label className="field">Question<input value={question} maxLength={2000} onChange={e=>setQuestion(e.target.value)}/></label><button disabled={busy||question.trim().length<3} onClick={()=>void send()}>{busy?'Sending…':'Send to configured CREAO agent'}</button><div className="actions">{routes.map(r=><a key={r.href} href={r.href}>{r.label}</a>)}</div>{reply&&<pre className="code-result">{reply}</pre>}</section>;
}
