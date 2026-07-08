import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FinPulse — Agentic Intelligence Platform | ShellKode",
  description: "Unified Behavioral Intelligence Platform — Propensity, Health Score, Default Prediction powered by Agentic AI",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#0a0e1a]">{children}</body>
    </html>
  );
}
