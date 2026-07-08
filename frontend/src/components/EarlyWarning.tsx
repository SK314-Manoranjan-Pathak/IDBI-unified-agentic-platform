"use client";

import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { fetchJSON, EarlyWarningAccount, DefaultResult } from "@/lib/api";

export default function EarlyWarning() {
  const [threshold, setThreshold] = useState(30);
  const [accounts, setAccounts] = useState<EarlyWarningAccount[]>([]);
  const [selected, setSelected] = useState<DefaultResult | null>(null);

  useEffect(() => {
    fetchJSON<{ accounts: EarlyWarningAccount[] }>(`/early-warning?threshold=${threshold}&limit=30`).then(
      (d) => setAccounts(d.accounts)
    );
  }, [threshold]);

  const drillDown = async (id: number) => {
    const d = await fetchJSON<DefaultResult>(`/customers/${id}/default`);
    setSelected(d);
  };

  const shapData = selected
    ? selected.top_factors.map((f) => ({ name: f.feature.replace(/_/g, " "), value: f.shap_value }))
    : [];

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">⚠️ Early Warning System (PS4)</h2>
      <p className="text-gray-500 text-sm mb-6">Loan portfolio monitoring — detect behavioral deterioration 12 months before default.</p>

      <div className="flex items-center gap-4 mb-6">
        <label className="text-sm">PD Alert Threshold:</label>
        <input type="range" min={10} max={80} value={threshold}
          onChange={(e) => setThreshold(Number(e.target.value))} className="w-48" />
        <span className="font-semibold">{threshold}%</span>
        <span className="ml-4 text-sm text-red-500 font-semibold">{accounts.length} accounts flagged</span>
      </div>

      <div className="grid grid-cols-5 gap-6">
        {/* Table */}
        <div className="col-span-3 card overflow-auto max-h-[550px]">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="text-left p-2">Account</th>
                <th className="text-left p-2">PD %</th>
                <th className="text-left p-2">Status</th>
                <th className="text-left p-2">Top Stress Factor</th>
                <th className="p-2"></th>
              </tr>
            </thead>
            <tbody>
              {accounts.map((a) => (
                <tr key={a.account_id} className="border-t hover:bg-red-50 cursor-pointer"
                  onClick={() => drillDown(a.account_id)}>
                  <td className="p-2 font-mono">{a.account_id}</td>
                  <td className="p-2 text-red-600 font-bold">{a.default_probability_pct}%</td>
                  <td className="p-2">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      a.loan_status === "B" ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"
                    }`}>{a.loan_status}</span>
                  </td>
                  <td className="p-2 text-xs">{a.top_stress_factors[0]?.feature.replace(/_/g, " ")}</td>
                  <td className="p-2"><button className="text-blue-500 text-xs hover:underline">Detail</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* SHAP drill-down */}
        <div className="col-span-2 card">
          <h3 className="font-semibold mb-3">SHAP Drill-Down</h3>
          {selected ? (
            <>
              <div className="mb-4">
                <p className="text-sm text-gray-500">Account <span className="font-mono font-bold">{selected.account_id}</span></p>
                <p className="text-2xl font-bold text-red-600">{selected.default_probability_pct}% PD</p>
                <p className="text-sm">{selected.stress_level}</p>
              </div>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={shapData} layout="vertical">
                  <XAxis type="number" />
                  <YAxis type="category" dataKey="name" width={130} fontSize={11} />
                  <Tooltip />
                  <Bar dataKey="value" name="SHAP">
                    {shapData.map((d, i) => (
                      <Cell key={i} fill={d.value > 0 ? "#dc2626" : "#16a34a"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </>
          ) : (
            <p className="text-sm text-gray-400">Click an account row to see SHAP explanation</p>
          )}

          {/* Intervention guide */}
          <div className="mt-6 p-4 bg-gray-50 rounded text-xs">
            <p className="font-semibold mb-2">Intervention Matrix</p>
            <p>🟡 Level 1 (Watch): Add to monitoring</p>
            <p>🟠 Level 2 (Alert): RM notification + courtesy msg</p>
            <p>🔴 Level 3 (Action): Urgent call + offer moratorium</p>
          </div>
        </div>
      </div>
    </div>
  );
}
