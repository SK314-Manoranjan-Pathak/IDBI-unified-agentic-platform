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

  const recColor = health?.recommendation === "Approve" ? "text-green-600 bg-green-50 border-green-200"
    : health?.recommendation === "Review" ? "text-amber-600 bg-amber-50 border-amber-200"
    : "text-red-600 bg-red-50 border-red-200";

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">💳 Financial Health Card (PS3)</h2>
      <p className="text-gray-500 text-sm mb-6">Multi-dimensional health assessment for NTC/NTB customers.</p>

      <div className="flex gap-3 mb-6">
        <input
          type="number"
          placeholder="Account ID (e.g. 2926 for MSME)"
          value={accountId}
          onChange={(e) => setAccountId(e.target.value)}
          className="border rounded px-4 py-2 w-72"
          onKeyDown={(e) => e.key === "Enter" && lookup()}
        />
        <button onClick={lookup} className="bg-emerald-600 text-white px-6 py-2 rounded hover:bg-emerald-700">
          Generate Health Card
        </button>
      </div>

      {health && (
        <>
          {/* Header badges */}
          <div className="flex gap-4 mb-6">
            <div className="card flex-1 text-center">
              <p className="text-xs text-gray-500">Composite Score</p>
              <p className="text-4xl font-bold text-emerald-600">{health.composite_health_score}</p>
              <p className="text-xs text-gray-400">out of 100</p>
            </div>
            <div className={`card flex-1 text-center border ${recColor}`}>
              <p className="text-xs">Recommendation</p>
              <p className="text-2xl font-bold">{health.recommendation === "Approve" ? "✅" : health.recommendation === "Review" ? "⚠️" : "❌"} {health.recommendation}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            {/* Radar */}
            <div className="card">
              <h3 className="font-semibold mb-3">6-Dimension Radar</h3>
              <ResponsiveContainer width="100%" height={350}>
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="dim" fontSize={10} />
                  <PolarRadiusAxis domain={[0, 100]} />
                  <Radar dataKey="score" stroke="#059669" fill="#059669" fillOpacity={0.3} />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            {/* Dimension bars + drivers */}
            <div className="card overflow-auto max-h-[450px]">
              <h3 className="font-semibold mb-3">Dimension Breakdown</h3>
              {Object.entries(health.dimensions).map(([dim, data]) => {
                const label = dim.replace("_score", "").replace(/_/g, " ");
                const barColor = data.score >= 60 ? "#16a34a" : data.score >= 40 ? "#d97706" : "#dc2626";
                return (
                  <div key={dim} className="mb-4">
                    <div className="flex justify-between text-sm">
                      <span className="capitalize font-medium">{label}</span>
                      <span className="font-bold" style={{ color: barColor }}>{data.score}</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded h-2 mt-1">
                      <div className="h-2 rounded" style={{ width: `${data.score}%`, background: barColor }} />
                    </div>
                    {data.top_factors.length > 0 && (
                      <p className="text-xs text-gray-400 mt-1">
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
