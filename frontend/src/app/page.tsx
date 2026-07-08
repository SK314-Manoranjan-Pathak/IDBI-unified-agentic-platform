"use client";

import { useState } from "react";
import PortfolioOverview from "@/components/PortfolioOverview";
import CustomerLookup from "@/components/CustomerLookup";
import ProspectList from "@/components/ProspectList";
import HealthCard from "@/components/HealthCard";
import EarlyWarning from "@/components/EarlyWarning";

const TABS = [
  { id: "portfolio", label: "📊 Portfolio Overview" },
  { id: "lookup", label: "🔍 Customer Lookup" },
  { id: "prospects", label: "🎯 Prospects (PS2)" },
  { id: "health", label: "💳 Health Card (PS3)" },
  { id: "warning", label: "⚠️ Early Warning (PS4)" },
];

export default function Home() {
  const [activeTab, setActiveTab] = useState("portfolio");

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-[#1e3a5f] text-white p-6 flex flex-col gap-2">
        <h1 className="text-lg font-bold mb-2">🏦 IDBI Agentic</h1>
        <p className="text-xs text-blue-200 mb-6">Unified ML Dashboard</p>
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`text-left px-3 py-2 rounded text-sm transition ${
              activeTab === tab.id
                ? "bg-white/20 font-semibold"
                : "hover:bg-white/10"
            }`}
          >
            {tab.label}
          </button>
        ))}
        <div className="mt-auto text-xs text-blue-300 pt-6 border-t border-blue-400/30">
          <p>Models: 3 (XGBoost)</p>
          <p>Features: 51</p>
          <p>Customers: 4,500</p>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 p-8 overflow-auto">
        {activeTab === "portfolio" && <PortfolioOverview />}
        {activeTab === "lookup" && <CustomerLookup />}
        {activeTab === "prospects" && <ProspectList />}
        {activeTab === "health" && <HealthCard />}
        {activeTab === "warning" && <EarlyWarning />}
      </main>
    </div>
  );
}
