"use client";
import { useState } from "react";
import Link from "next/link";

type GH = { name: string; crop: string; moisture: number; temp: number; humidity: number; anomaly: number; detail: string };
const greenhouses: GH[] = [
  {name:"North greenhouse",crop:"Tomato",moisture:34,temp:24,humidity:68,anomaly:12,detail:"Reference crop with stable moisture."},
  {name:"Coastal greenhouse",crop:"Lettuce",moisture:57,temp:19,humidity:78,anomaly:7,detail:"Cooler, humid growing conditions."},
  {name:"Drylands greenhouse",crop:"Pepper",moisture:22,temp:29,humidity:43,anomaly:31,detail:"Dryer substrate; review irrigation context."},
  {name:"Highland greenhouse",crop:"Strawberry",moisture:46,temp:17,humidity:73,anomaly:15,detail:"Cool growing conditions with moderate moisture."},
  {name:"Research greenhouse",crop:"Basil",moisture:64,temp:26,humidity:82,anomaly:24,detail:"Higher humidity; inspect leaf surfaces."},
  {name:"South greenhouse",crop:"Cucumber",moisture:39,temp:27,humidity:61,anomaly:19,detail:"Warm growing conditions."},
];
type Field = "moisture" | "temp" | "humidity" | "anomaly";
const fields: { key: Field; label:string;unit:string }[] = [
 {key:"moisture",label:"Soil moisture",unit:"%"},
 {key:"temp",label:"Temperature",unit:"°C"},
 {key:"humidity",label:"Relative humidity",unit:"%"},
 {key:"anomaly",label:"Visible anomaly index",unit:"/100"},
];
export default function GreenhousesPage() {
 const [chosen,setChosen]=useState(0);
 const [metric,setMetric]=useState<Field>("moisture");
 const [userValue,setUserValue]=useState("");
 const active=greenhouses[chosen];
 const values=greenhouses.map(g=>g[metric]);
 const avg=values.reduce((a,b)=>a+b,0)/values.length;
 const numeric=userValue.trim()===""?null:Number(userValue);
 const valid=numeric!==null&&Number.isFinite(numeric)&&numeric>=0&&(metric==="temp"?numeric<=60:numeric<=100);
 return <main className="container route-page">
 <p className="eyebrow">Six greenhouse research scenarios</p>
 <h1>Compare conditions.<br/><span>Not private farms.</span></h1>
 <p className="hero-copy">All six greenhouses are intentionally fabricated illustrations, not real farms, live sensor readings, validated forecasts, or the three-client federated training run. Use them to understand how a future opt-in comparison could work.</p>
 <div className="greenhouse-cards" style={{gridTemplateColumns:"repeat(auto-fit,minmax(220px,1fr))"}}>
 {greenhouses.map((g,i)=><button key={g.name} className={chosen===i?"greenhouse-card selected":"greenhouse-card"} style={{textAlign:"left",display:"block",background:chosen===i?"#082216":"#071410",color:"#edf8f2"}} onClick={()=>setChosen(i)} aria-pressed={chosen===i}><strong>{g.name}</strong><small>{g.crop} · Synthetic scenario</small><small>{g.detail}</small></button>)}
 </div>
 <div className="grid"><section className="panel">
 <p className="eyebrow">Selected example</p><h2>{active.name}</h2>
 <div className="metric-cards">{fields.map(f=><article key={f.key}><span>{f.label}</span><strong>{active[f.key]}{f.unit==="%"?"%":""}</strong><small>{f.unit==="%"?"Synthetic sample":f.unit+" · synthetic sample"}</small></article>)}</div>
 <p className="muted">These values are fictional learning examples. No user data is connected to this page.</p>
 </section><section className="panel"><p className="eyebrow">Private comparison calculator</p><h2>Compare your own reading</h2>
 <label className="field">Metric<select value={metric} onChange={e=>{setMetric(e.target.value as Field);setUserValue("");}}>{fields.map(f=><option key={f.key} value={f.key}>{f.label}</option>)}</select></label>
 <label className="field">Your measurement ({fields.find(f=>f.key===metric)?.unit})<input type="number" inputMode="decimal" min="0" max={metric==="temp"?"60":"100"} value={userValue} onChange={e=>setUserValue(e.target.value)} placeholder="Optional: enter a value"/></label>
 <p className="muted">The number you enter stays in your browser's page state. It is not uploaded or saved, and it does not train any model.</p>
 <p role="status">{valid&&numeric!==null?<>Your entry is <strong>{Math.abs(numeric-avg).toFixed(1)} {fields.find(f=>f.key===metric)?.unit}</strong> {numeric>=avg?"above":"below"} the six-scenario average ({avg.toFixed(1)}). This difference is descriptive, not a health assessment.</>:"Select a metric and enter a valid number to compare with fabricated benchmarks."}</p>
 </section></div>
 <section className="panel support"><p className="eyebrow">How this connects to VigiloForge</p><h2>From demonstration to a real observation</h2><p>Use the <Link href="/#vision">camera workspace</Link> to observe your own leaf image. With your explicit permission, the platform can separately request public reference research and agent processing. This scenario calculator does not transmit your measurements, does not invoke agents, and cannot diagnose a crop.</p><p>To compare live greenhouse telemetry, use the dashboard's Tiger Cloud panel. Its current hosted records are explicitly synthetic demo records. The <Link href="/federated">federated learning page</Link> is a different demonstration with three simulated clients.</p></section>
 </main>;
}
