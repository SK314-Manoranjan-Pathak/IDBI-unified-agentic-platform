"use client";

import { useState } from "react";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import { fetchJSON, CustomerDetail, PropensityResult, DefaultResult } from "@/lib/api";

export default function CustomerLookup() {
  const [accountId, setAccountId] = useState("");
  const [customer, setCustomer] = useState<CustomerDetail | null>(null);
  const [propensity, setPropensity] = useState<PropensityResult | null>(null);
  const [defaultRisk, setDefaultRisk] = useState<DefaultResult | null>(null);

  const lookup = async () => {
    if (!accountId) return;
    const [c, p, d] = await Promise.all([
      fetchJSON<CustomerDetail>(`/customers/${accountId}`),
      fetchJSON<PropensityResult>(`/customers/${accountId}/propensity`),
      fetchJSON<DefaultResult>(`/customers/${accountId}/default`),
    ]);
    setCustomer(c);
    setPropensity(p);
    setDefaultRisk(d);
  };

  const healthRadar = customer
    ? Object.entries(customer.health_scores)
        .filter(([k]) => k !== "composite")
        .map(([k, v]) => ({ dim: k.replace("_score", "").replace(/_/g, " "), score: v }))
    : [];

  const shapData = (factors: { feature: string; shap_value: number }[]) =>
    factors.map((f) => ({ name: f.feature.replace(/_/g, " "), value: f.shap_value }));

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">🔍 Customer Lookup</h2>

      <div className="flex gap-3 mb-6">
        <input
          type="number"
          placeholder="Enter Account ID (e.g. 2048)"
          value={accountId}
          onChange={(e) => setAccountId(e.target.value)}
          className="border rounded px-4 py-2 w-64"
          onKeyDown={(e) => e.key === "Enter" && lookup()}
        />
        <button onClick={lookup} className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700">
          Search
        </button>
      </div>

      {customer && (
        <>
          {/* Profile metrics */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="card"><p className="text-xs text-gray-500">Income/mo</p><p className="text-xl font-bold">₹{customer.monthly_income_avg?.toLocaleString()}</p></div>
            <div className="card"><p className="text-xs text-gray-500">Surplus/mo</p><p className="text-xl font-bold">₹{customer.monthly_surplus_avg?.toLocaleString()}</p></div>
            <div className="card"><p className="text-xs text-gray-500">Balance</p><p className="text-xl font-bold">₹{customer.balance_latest?.toLocaleString()}</p></div>
            <div className="card"><p className="text-xs text-gray-500">Has Loan</p><p className="text-xl font-bold">{customer.has_loan ? "Yes" : "No"}</p></div>
          </div>

          {/* Score gauges (simple colored cards) */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="card border-l-4 border-blue-500">
              <p className="text-xs text-gray-500">Propensity Score</p>
              <p className="text-3xl font-bold text-blue-600">{customer.propensity_score}</p>
              <p className="text-xs">{propensity?.predicted_product} · {propensity?.confidence}</p>
            </div>
            <div className={`card border-l-4 ${customer.default_probability > 30 ? "border-red-500" : customer.default_probability > 10 ? "border-amber-500" : "border-green-500"}`}>
              <p className="text-xs text-gray-500">Default Risk</p>
              <p className={`text-3xl font-bold ${customer.default_probability > 30 ? "text-red-600" : "text-green-600"}`}>{customer.default_probability}%</p>
              <p className="text-xs">{defaultRisk?.stress_level}</p>
            </div>
            <div className="card border-l-4 border-emerald-500">
              <p className="text-xs text-gray-500">Health Score</p>
              <p className="text-3xl font-bold text-emerald-600">{customer.health_scores.composite}</p>
              <p className="text-xs">Composite / 100</p>
            </div>
          </div>

          {/* Radar + SHAP side by side */}
          <div className="grid grid-cols-2 gap-6">
            <div className="card">
              <h3 className="font-semibold mb-3">Health Card (6 Dimensions)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={healthRadar}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="dim" fontSize={10} />
                  <PolarRadiusAxis domain={[0, 100]} />
                  <Radar dataKey="score" stroke="#2563eb" fill="#2563eb" fillOpacity={0.3} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
            <div className="card">
              <h3 className="font-semibold mb-3">SHAP — Default Risk Factors</h3>
              {defaultRisk && (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={shapData(defaultRisk.top_factors)} layout="vertical">
                    <XAxis type="number" />
                    <YAxis type="category" dataKey="name" width={140} fontSize={11} />
                    <Tooltip />
                    <Bar dataKey="value" name="SHAP">
                      {shapData(defaultRisk.top_factors).map((d, i) => (
                        <Cell key={i} fill={d.value > 0 ? "#dc2626" : "#16a34a"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
