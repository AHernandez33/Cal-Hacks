import type { MetadataRoute } from "next";
export default function manifest(): MetadataRoute.Manifest {
  return { name: "VigiloForge Secured Crop Detective", short_name: "VigiloForge", description: "Offline-first crop observation prototype", start_url: "/", display: "standalone", background_color: "#f4f7f5", theme_color: "#123b2c", icons: [{src:"/icon.svg",sizes:"any",type:"image/svg+xml",purpose:"any"}] };
}
