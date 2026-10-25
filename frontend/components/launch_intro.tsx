"use client";
import { useEffect, useState } from "react";
import Image from "next/image";
export default function LaunchIntro(){
 const [visible,setVisible]=useState(false);
 useEffect(()=>{if(!window.matchMedia("(prefers-reduced-motion: reduce)").matches && !sessionStorage.getItem("vigilo_intro_seen")){setVisible(true);sessionStorage.setItem("vigilo_intro_seen","1");}},[]);
 if(!visible)return null;
 return <div className="launch-intro" role="presentation" onAnimationEnd={()=>setVisible(false)}>
 <div className="launch-door launch-door-left" aria-hidden="true"/>
 <div className="launch-door launch-door-right" aria-hidden="true"/>
 <div className="launch-emblem"><Image src="/vigiloforge-logo.png" width={720} height={240} alt="" unoptimized/><span className="launch-glimmer"/></div>
 </div>;
}
