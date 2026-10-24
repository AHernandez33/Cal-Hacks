"use client";
import { useEffect } from "react";
export default function PWARegister() {
 useEffect(()=>{if("serviceWorker" in navigator && window.isSecureContext) {navigator.serviceWorker.register("/sw.js").catch(console.warn);}},[]);
 return null;
}
