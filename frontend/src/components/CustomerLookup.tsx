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
      <div className="mb-8">
        <h2 className="text-2xl font-bold gradient-text mb-1">Customer Intelligence</h2>
        <p className="text-sm text-[var(--text-muted)]">360° view — propensity, health, and risk for any customer</p>
      </div>

      <div className="flex gap-3 mb-6">
        <input
          type="number"
          placeholder="Enter Account ID (e.g. 2048)"
          value={accountId}
          onChange={(e) => setAccountId(e.target.value)}
          className="w-64"
          onKeyDown={(e) => e.key === "Enter" && lookup()}
        />
        <button onClick={lookup} className="bg-gradient-to-r from-[var(--primary)] to-[var(--accent)] text-[var(--text)] px-6 py-2 rounded-lg font-medium hover:opacity-90 hover:shadow-lg hover:shadow-blue-500/20">
          Search
        </button>
      </div>

      {customer && (
        <>
          {/* Profile metrics */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="card">
              <p className="text-xs text-[var(--text-muted)]">Income/mo</p>
              <p className="text-xl font-bold text-[var(--text)]">₹{customer.monthly_income_avg?.toLocaleString()}</p>
            </div>
            <div className="card">
              <p className="text-xs text-[var(--text-muted)]">Surplus/mo</p>
              <p className="text-xl font-bold text-[var(--text)]">₹{customer.monthly_surplus_avg?.toLocaleString()}</p>
            </div>
            <div className="card">
              <p className="text-xs text-[var(--text-muted)]">Balance</p>
              <p className="text-xl font-bold text-[var(--text)]">₹{customer.balance_latest?.toLocaleString()}</p>
            </div>
            <div className="card">
              <p className="text-xs text-[var(--text-muted)]">Has Loan</p>
              <p className="text-xl font-bold text-[var(--text)]">{customer.has_loan ? "Yes" : "No"}</p>
            </div>
          </div>

          {/* Score cards */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="card border-l-4 border-[var(--primary)]">
              <p className="text-xs text-[var(--text-muted)]">Propensity Score</p>
              <p className="text-3xl font-bold text-[var(--primary-light)]">{customer.propensity_score}</p>
              <p className="text-xs text-[var(--text-muted)] mt-1">{propensity?.predicted_product} · {propensity?.confidence}</p>
            </div>
            <div className={`card border-l-4 ${customer.default_probability > 30 ? "border-[var(--red)]" : customer.default_probability > 10 ? "border-[var(--amber)]" : "border-[var(--green)]"}`}>
              <p className="text-xs text-[var(--text-muted)]">Default Risk</p>
              <p className={`text-3xl font-bold ${customer.default_probability > 30 ? "text-[var(--red)]" : "text-[var(--green)]"}`}>{customer.default_probability}%</p>
              <p className="text-xs text-[var(--text-muted)] mt-1">{defaultRisk?.stress_level}</p>
            </div>
            <div className="card border-l-4 border-[var(--green)]">
              <p className="text-xs text-[var(--text-muted)]">Health Score</p>
              <p className="text-3xl font-bold text-[var(--green)]">{customer.health_scores.composite}</p>
              <p className="text-xs text-[var(--text-muted)] mt-1">Composite / 100</p>
            </div>
          </div>

          {/* Radar + SHAP */}
          <div className="grid grid-cols-2 gap-6">
            <div className="card">
              <h3 className="font-semibold text-[var(--text)] mb-3">Health Card (6 Dimensions)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={healthRadar}>
                  <PolarGrid stroke="#e2e8f0" />
                  <PolarAngleAxis dataKey="dim" fontSize={10} stroke="#94a3b8" />
                  <PolarRadiusAxis domain={[0, 100]} stroke="#cbd5e1" />
                  <Radar dataKey="score" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
            <div className="card">
              <h3 className="font-semibold text-[var(--text)] mb-3">SHAP — Default Risk Factors</h3>
              {defaultRisk && (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={shapData(defaultRisk.top_factors)} layout="vertical">
                    <XAxis type="number" stroke="#94a3b8" fontSize={11} />
                    <YAxis type="category" dataKey="name" width={140} fontSize={10} stroke="#94a3b8" />
                    <Tooltip contentStyle={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "8px", color: "#1e293b" }} />
                    <Bar dataKey="value" name="SHAP" radius={[0, 4, 4, 0]}>
                      {shapData(defaultRisk.top_factors).map((d, i) => (
                        <Cell key={i} fill={d.value > 0 ? "#f43f5e" : "#10b981"} />
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
