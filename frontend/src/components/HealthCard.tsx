"use client";

import { useState } from "react";
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts";
import { fetchJSON, HealthResult } from "@/lib/api";

export default function HealthCard() {
  const [accountId, setAccountId] = useState("");
  const [health, setHealth] = useState<HealthResult | null>(null);

  const lookup = async () => {
    if (!accountId) return;
    const h = await fetchJSON<HealthResult>(`/customers/${accountId}/health`);
    setHealth(h);
  };

  const radarData = health
    ? Object.entries(health.dimensions).map(([k, v]) => ({
        dim: k.replace("_score", "").replace(/_/g, " "),
        score: v.score,
      }))
    : [];

  const recStyle = health?.recommendation === "Approve"
    ? "text-[var(--green)] bg-[var(--green)]/10 border-[var(--green)]/30"
    : health?.recommendation === "Review"
    ? "text-[var(--amber)] bg-[var(--amber)]/10 border-[var(--amber)]/30"
    : "text-[var(--red)] bg-[var(--red)]/10 border-[var(--red)]/30";

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold gradient-text mb-1">Financial Health Card — PS3</h2>
        <p className="text-sm text-[var(--text-muted)]">Multi-dimensional health assessment for NTC/NTB customers using alternate data</p>
      </div>

      <div className="flex gap-3 mb-6">
        <input
          type="number"
          placeholder="Account ID (e.g. 2926 for MSME)"
          value={accountId}
          onChange={(e) => setAccountId(e.target.value)}
          className="w-72"
          onKeyDown={(e) => e.key === "Enter" && lookup()}
        />
        <button onClick={lookup} className="bg-gradient-to-r from-[var(--green)] to-emerald-400 text-[var(--text)] px-6 py-2 rounded-lg font-medium hover:opacity-90 hover:shadow-lg hover:shadow-emerald-500/20">
          Generate Health Card
        </button>
      </div>

      {health && (
        <>
          {/* Header badges */}
          <div className="flex gap-4 mb-6">
            <div className="card flex-1 text-center">
              <p className="text-xs text-[var(--text-muted)]">Composite Score</p>
              <p className="text-4xl font-bold text-[var(--green)]">{health.composite_health_score}</p>
              <p className="text-xs text-[var(--text-muted)]">out of 100</p>
            </div>
            <div className={`card flex-1 text-center border ${recStyle}`}>
              <p className="text-xs text-[var(--text-muted)]">Recommendation</p>
              <p className="text-2xl font-bold mt-1">
                {health.recommendation === "Approve" ? "✅" : health.recommendation === "Review" ? "⚠️" : "❌"}{" "}
                {health.recommendation}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            {/* Radar */}
            <div className="card">
              <h3 className="font-semibold text-[var(--text)] mb-3">6-Dimension Radar</h3>
              <ResponsiveContainer width="100%" height={350}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#e2e8f0" />
                  <PolarAngleAxis dataKey="dim" fontSize={10} stroke="#94a3b8" />
                  <PolarRadiusAxis domain={[0, 100]} stroke="#cbd5e1" />
                  <Radar dataKey="score" stroke="#10b981" fill="#10b981" fillOpacity={0.2} />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            {/* Dimension bars + drivers */}
            <div className="card overflow-auto max-h-[450px]">
              <h3 className="font-semibold text-[var(--text)] mb-3">Dimension Breakdown</h3>
              {Object.entries(health.dimensions).map(([dim, data]) => {
                const label = dim.replace("_score", "").replace(/_/g, " ");
                const barColor = data.score >= 60 ? "var(--green)" : data.score >= 40 ? "var(--amber)" : "var(--red)";
                return (
                  <div key={dim} className="mb-4">
                    <div className="flex justify-between text-sm">
                      <span className="capitalize font-medium text-[var(--text-secondary)]">{label}</span>
                      <span className="font-bold" style={{ color: barColor }}>{data.score}</span>
                    </div>
                    <div className="w-full bg-[#f1f5f9] rounded h-2 mt-1">
                      <div className="h-2 rounded transition-all" style={{ width: `${data.score}%`, background: barColor }} />
                    </div>
                    {data.top_factors.length > 0 && (
                      <p className="text-xs text-[var(--text-muted)] mt-1">
                        Drivers: {data.top_factors.map((f) => f.feature.replace(/_/g, " ")).join(", ")}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
