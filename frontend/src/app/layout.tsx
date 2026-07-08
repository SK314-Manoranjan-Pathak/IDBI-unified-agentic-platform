import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "IDBI Agentic Platform — ML Dashboard",
  description: "Propensity, Health Score, Default Prediction with SHAP Explanations",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
