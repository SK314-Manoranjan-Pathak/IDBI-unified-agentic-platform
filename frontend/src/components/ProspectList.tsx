"use client";

import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { fetchJSON, Prospect } from "@/lib/api";

const PRODUCT_COLORS: Record<string, string> = {
  "Auto Loan": "#3b82f6",
  "Home Loan": "#10b981",
  "Personal Loan": "#a855f7",
};

export default function ProspectList() {
  const [threshold, setThreshold] = useState(70);
  const [prospects, setProspects] = useState<Prospect[]>([]);

  useEffect(() => {
    fetchJSON<{ prospects: Prospect[] }>(`/prospects?threshold=${threshold}&limit=50`).then((d) =>
      setProspects(d.prospects)
    );
  }, [threshold]);

  const productMix = prospects.reduce((acc, p) => {
    const prod = p.predicted_product || "Other";
    acc[prod] = (acc[prod] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  const mixData = Object.entries(productMix).map(([name, count]) => ({ name, count }));

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold gradient-text mb-1">Prospect Assist — PS2</h2>
        <p className="text-sm text-[var(--text-muted)]">High-propensity customers with low default risk — ready for outreach</p>
      </div>

      <div className="flex items-center gap-4 mb-6 card py-4">
        <label className="text-sm text-[var(--text-secondary)]">Propensity Threshold:</label>
        <input
          type="range" min={50} max={99} value={threshold}
          onChange={(e) => setThreshold(Number(e.target.value))}
          className="w-48"
        />
        <span className="font-semibold text-[var(--primary-light)]">{threshold}%</span>
        <span className="ml-4 text-sm text-[var(--text-muted)]">({prospects.length} qualified)</span>
      </div>

      <div className="grid grid-cols-3 gap-6 mb-6">
        <div className="col-span-2 card overflow-auto max-h-[500px]">
          <table className="w-full text-sm">
            <thead className="sticky top-0">
              <tr>
                <th className="text-left p-2">Account</th>
                <th className="text-left p-2">Score</th>
                <th className="text-left p-2">Product</th>
                <th className="text-left p-2">Default %</th>
                <th className="text-left p-2">Surplus ₹</th>
              </tr>
            </thead>
            <tbody>
              {prospects.map((p) => (
                <tr key={p.account_id} className="border-t border-[var(--card-border)]">
                  <td className="p-2 font-mono text-[var(--text-secondary)]">{p.account_id}</td>
                  <td className="p-2 font-semibold text-[var(--primary-light)]">{p.propensity_score}</td>
                  <td className="p-2">
                    <span className="px-2 py-0.5 rounded text-xs font-medium"
                      style={{ background: (PRODUCT_COLORS[p.predicted_product] || "#666") + "20",
                               color: PRODUCT_COLORS[p.predicted_product] || "#94a3b8" }}>
                      {p.predicted_product}
                    </span>
                  </td>
                  <td className="p-2 text-[var(--green)]">{p.default_probability}%</td>
                  <td className="p-2 text-[var(--text-secondary)]">₹{p.monthly_surplus.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <h3 className="font-semibold text-[var(--text)] mb-4">Product Mix</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={mixData}>
              <XAxis dataKey="name" fontSize={11} stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip contentStyle={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "8px", color: "#1e293b" }} />
              <Bar dataKey="count" name="Count" radius={[4, 4, 0, 0]}>
                {mixData.map((d, i) => (
                  <Cell key={i} fill={PRODUCT_COLORS[d.name] || "#64748b"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
