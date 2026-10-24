"use client";
import {useEffect,useState} from "react";
import {saveObservation,listObservations,deleteObservation,type Observation} from "../lib/offline_storage";
import {analyzeImage} from "../lib/api";
export default function OfflinePanel(){
 const [items,setItems]=useState<Observation[]>([]);const [message,setMessage]=useState('');const [online,setOnline]=useState(true);
 async function refresh(){try{setItems(await listObservations());}catch(e){setMessage(String(e));}}
 useEffect(()=>{setOnline(navigator.onLine);const fn=()=>setOnline(navigator.onLine);window.addEventListener('online',fn);window.addEventListener('offline',fn);void refresh();return()=>{window.removeEventListener('online',fn);window.removeEventListener('offline',fn);};},[]);
 async function save(file:File){try{await saveObservation(file,file.name);setMessage('Saved locally. Nothing uploaded.');await refresh();}catch(e){setMessage(String(e));}}
 async function send(ob:Observation){if(!online){setMessage('Offline: reconnect before analysis.');return;}if(!window.confirm('Send this saved image to your configured backend for analysis?'))return;try{const result=await analyzeImage(ob.photo);setMessage('Analysis returned: '+JSON.stringify(result).slice(0,280));}catch(e){setMessage(String(e));}}
 return <section className="panel"><h2>Field Mode — offline observations</h2><p className="muted">{online?'Network appears available':'Offline'} · Photos are stored only in this browser until you choose to send or delete them.</p>
 <label className="file-label">Save a photo locally <input type="file" accept="image/*" capture="environment" onChange={e=>{const f=e.target.files?.[0];if(f)void save(f);e.currentTarget.value='';}} /></label>
 <div className="history">{items.map(ob=><p key={ob.id}><strong>{ob.name}</strong> ({new Date(ob.createdAt).toLocaleString()}) <button type="button" onClick={()=>void send(ob)}>Analyze with consent</button> <button type="button" onClick={()=>void deleteObservation(ob.id).then(refresh)}>Delete</button></p>)}</div>
 {message&&<p role="status" className="muted">{message}</p>}</section>;
}
