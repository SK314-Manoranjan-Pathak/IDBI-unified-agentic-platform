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
      <div className="mb-8">
        <h2 className="text-2xl font-bold gradient-text mb-1">Early Warning System — PS4</h2>
        <p className="text-sm text-[var(--text-muted)]">Detect behavioral deterioration 12 months before default — AI-powered stress monitoring</p>
      </div>

      <div className="flex items-center gap-4 mb-6 card py-4">
        <label className="text-sm text-[var(--text-secondary)]">PD Alert Threshold:</label>
        <input type="range" min={10} max={80} value={threshold}
          onChange={(e) => setThreshold(Number(e.target.value))} className="w-48" />
        <span className="font-semibold text-[var(--red)]">{threshold}%</span>
        <span className="ml-4 text-sm text-[var(--text-muted)]">{accounts.length} accounts flagged</span>
      </div>

      <div className="grid grid-cols-5 gap-6">
        {/* Table */}
        <div className="col-span-3 card overflow-auto max-h-[550px]">
          <table className="w-full text-sm">
            <thead className="sticky top-0">
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
                <tr key={a.account_id} className="border-t border-[var(--card-border)] cursor-pointer"
                  onClick={() => drillDown(a.account_id)}>
                  <td className="p-2 font-mono text-[var(--text-secondary)]">{a.account_id}</td>
                  <td className="p-2 text-[var(--red)] font-bold">{a.default_probability_pct}%</td>
                  <td className="p-2">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      a.loan_status === "B" ? "bg-[var(--red)]/10 text-[var(--red)]" : "bg-[var(--amber)]/10 text-[var(--amber)]"
                    }`}>{a.loan_status}</span>
                  </td>
                  <td className="p-2 text-xs text-[var(--text-muted)]">{a.top_stress_factors[0]?.feature.replace(/_/g, " ")}</td>
                  <td className="p-2">
                    <button className="text-[var(--primary-light)] text-xs hover:underline">Detail →</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* SHAP drill-down */}
        <div className="col-span-2 card">
          <h3 className="font-semibold text-[var(--text)] mb-3">SHAP Drill-Down</h3>
          {selected ? (
            <>
              <div className="mb-4 p-3 bg-[#f8fafc] rounded-lg border border-[var(--card-border)]">
                <p className="text-sm text-[var(--text-muted)]">Account <span className="font-mono font-bold text-[var(--text)]">{selected.account_id}</span></p>
                <p className="text-2xl font-bold text-[var(--red)] mt-1">{selected.default_probability_pct}% PD</p>
                <p className="text-xs text-[var(--amber)]">{selected.stress_level}</p>
              </div>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={shapData} layout="vertical">
                  <XAxis type="number" stroke="#94a3b8" fontSize={11} />
                  <YAxis type="category" dataKey="name" width={130} fontSize={10} stroke="#94a3b8" />
                  <Tooltip contentStyle={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "8px", color: "#1e293b" }} />
                  <Bar dataKey="value" name="SHAP" radius={[0, 4, 4, 0]}>
                    {shapData.map((d, i) => (
                      <Cell key={i} fill={d.value > 0 ? "#f43f5e" : "#10b981"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </>
          ) : (
            <div className="flex items-center justify-center h-48 text-[var(--text-muted)] text-sm">
              Click an account to see SHAP explanation
            </div>
          )}

          {/* Intervention guide */}
          <div className="mt-6 p-4 bg-[#f8fafc] rounded-lg border border-[var(--card-border)]">
            <p className="font-semibold text-[var(--text)] text-xs mb-2">Intervention Matrix</p>
            <div className="space-y-1.5 text-xs text-[var(--text-secondary)]">
              <p><span className="text-[var(--amber)]">●</span> Level 1 (Watch): Add to monitoring</p>
              <p><span className="text-orange-400">●</span> Level 2 (Alert): RM notification + courtesy msg</p>
              <p><span className="text-[var(--red)]">●</span> Level 3 (Action): Urgent call + offer moratorium</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
