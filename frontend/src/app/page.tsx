"use client";

import { useState } from "react";
import PortfolioOverview from "@/components/PortfolioOverview";
import CustomerLookup from "@/components/CustomerLookup";
import ProspectList from "@/components/ProspectList";
import HealthCard from "@/components/HealthCard";
import EarlyWarning from "@/components/EarlyWarning";
import AgentActions from "@/components/AgentActions";

const TABS = [
  { id: "portfolio", label: "Portfolio Overview", icon: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/></svg>` },
  { id: "lookup", label: "Customer Lookup", icon: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>` },
  { id: "prospects", label: "Prospect Assist", icon: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="19" x2="19" y1="8" y2="14"/><line x1="22" x2="16" y1="11" y2="11"/></svg>` },
  { id: "health", label: "Health Card", icon: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>` },
  { id: "warning", label: "Early Warning", icon: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><line x1="12" x2="12" y1="9" y2="13"/><line x1="12" x2="12.01" y1="17" y2="17"/></svg>` },
  { id: "agents", label: "Agent Actions", icon: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a4 4 0 0 0-4 4c0 2 2 3 2 6H8a2 2 0 0 0-2 2v2h12v-2a2 2 0 0 0-2-2h-2c0-3 2-4 2-6a4 4 0 0 0-4-4Z"/><path d="M9 18v1a3 3 0 0 0 6 0v-1"/></svg>` },
];

export default function Home() {
  const [activeTab, setActiveTab] = useState("portfolio");

  return (
    <div className="flex min-h-screen">
      {/* Sidebar — dark top fading to lighter */}
      <aside className="w-72 bg-gradient-to-b from-[#0a0e1a] to-[#1e3a5f] flex flex-col">
        {/* Logo / Brand */}
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center">
              <span className="text-white font-bold text-sm">S</span>
            </div>
            <div>
              <h1 className="text-base font-bold text-white tracking-tight">FinPulse</h1>
              <p className="text-[10px] text-blue-300/70 uppercase tracking-widest">by ShellKode</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 flex flex-col gap-1">
          <p className="text-[10px] uppercase tracking-widest text-blue-300/50 mb-3 px-3">Modules</p>
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`text-left px-4 py-2.5 rounded-lg text-sm flex items-center gap-3 transition-all ${
                activeTab === tab.id
                  ? "bg-white/12 text-white font-medium"
                  : "text-blue-200/70 hover:bg-white/6 hover:text-white"
              }`}
            >
              <span dangerouslySetInnerHTML={{ __html: tab.icon }} className="flex-shrink-0 opacity-80" />
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Stats footer */}
        <div className="p-4 border-t border-white/10">
          <div className="bg-white/5 rounded-lg p-3 space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-blue-300/60">Models</span>
              <span className="text-green-400 font-medium">3 active</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-blue-300/60">Features</span>
              <span className="text-white/80 font-medium">51</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-blue-300/60">Customers</span>
              <span className="text-white/80 font-medium">4,500</span>
            </div>
          </div>
          <p className="text-[10px] text-blue-300/40 text-center mt-3">
            Strands Agents + Bedrock AgentCore
          </p>
        </div>
      </aside>

      {/* Main content — light background */}
      <main className="flex-1 p-8 overflow-auto bg-[#f0f4f8]">
        {activeTab === "portfolio" && <PortfolioOverview />}
        {activeTab === "lookup" && <CustomerLookup />}
        {activeTab === "prospects" && <ProspectList />}
        {activeTab === "health" && <HealthCard />}
        {activeTab === "warning" && <EarlyWarning />}
        {activeTab === "agents" && <AgentActions />}
      </main>
    </div>
  );
}
