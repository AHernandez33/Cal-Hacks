import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VigiloForge | Secured Crop Detective",
  description:
    "Smarter Farming. Private by Design.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}