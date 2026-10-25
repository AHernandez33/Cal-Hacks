import type { Metadata } from "next";
import "@fontsource/inter/400.css";
import "@fontsource/inter/600.css";
import "@fontsource/orbitron/400.css";
import "@fontsource/orbitron/600.css";
import "./globals.css";
import SiteNav from "../components/site_nav";
export const metadata: Metadata = {
  title: "VigiloForge | Secured Crop Detector",
  description: "Smarter Farming. Private by Design.",
  manifest: "/manifest.webmanifest",
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <div className="container">
          <SiteNav />
        </div>
        {children}
      </body>
    </html>
  );
}
