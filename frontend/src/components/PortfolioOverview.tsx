"use client";

import { useEffect, useState } from "react";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { fetchJSON, CustomerSummary, Prospect, EarlyWarningAccount } from "@/lib/api";

const COLORS = { green: "#16a34a", amber: "#d97706", red: "#dc2626" };

export default function PortfolioOverview() {
  const [customers, setCustomers] = useState<CustomerSummary[]>([]);
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [warnings, setWarnings] = useState<EarlyWarningAccount[]>([]);

  useEffect(() => {
    fetchJSON<{ customers: CustomerSummary[] }>("/customers?limit=4500").then((d) =>
      setCustomers(d.customers)
    );
    fetchJSON<{ prospects: Prospect[] }>("/prospects?threshold=70&limit=15").then((d) =>
      setProspects(d.prospects)
    );
    fetchJSON<{ accounts: EarlyWarningAccount[] }>("/early-warning?threshold=30&limit=10").then((d) =>
      setWarnings(d.accounts)
    );
  }, []);

  const green = customers.filter((c) => c.default_probability < 10).length;
  const amber = customers.filter((c) => c.default_probability >= 10 && c.default_probability < 30).length;
  const red = customers.filter((c) => c.default_probability >= 30).length;
  const hotProspects = customers.filter((c) => c.propensity_score >= 70).length;

  const pieData = [
    { name: "Green (<10%)", value: green, color: COLORS.green },
    { name: "Amber (10-30%)", value: amber, color: COLORS.amber },
    { name: "Red (>30%)", value: red, color: COLORS.red },
  ];

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">📊 Portfolio Overview</h2>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="card text-center">
          <p className="text-3xl font-bold">{customers.length.toLocaleString()}</p>
          <p className="text-sm text-gray-500">Total Customers</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-green-600">{green.toLocaleString()}</p>
          <p className="text-sm text-gray-500">🟢 Low Risk</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-red-600">{red.toLocaleString()}</p>
          <p className="text-sm text-gray-500">🔴 High Risk</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-blue-600">{hotProspects}</p>
          <p className="text-sm text-gray-500">🎯 Hot Prospects</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6 mb-8">
        {/* Pie chart */}
        <div className="card">
          <h3 className="font-semibold mb-4">Risk Distribution</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
                {pieData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Top prospects bar */}
        <div className="card">
          <h3 className="font-semibold mb-4">Top 15 Prospects</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={prospects} layout="vertical">
              <XAxis type="number" domain={[0, 100]} />
              <YAxis type="category" dataKey="account_id" width={60} fontSize={11} />
              <Tooltip />
              <Bar dataKey="propensity_score" fill="#2563eb" name="Propensity" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Early warning table */}
      <div className="card">
        <h3 className="font-semibold mb-4">⚠️ Early Warning (PD &gt; 30%)</h3>
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left p-2">Account</th>
              <th className="text-left p-2">PD %</th>
              <th className="text-left p-2">Status</th>
              <th className="text-left p-2">Top Stress Factor</th>
            </tr>
          </thead>
          <tbody>
            {warnings.map((w) => (
              <tr key={w.account_id} className="border-t">
                <td className="p-2 font-mono">{w.account_id}</td>
                <td className="p-2 text-red-600 font-semibold">{w.default_probability_pct}%</td>
                <td className="p-2">{w.loan_status}</td>
                <td className="p-2">{w.top_stress_factors[0]?.feature}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
