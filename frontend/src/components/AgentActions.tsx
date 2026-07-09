"use client";

import React, { useEffect, useState } from "react";
import { fetchJSON } from "@/lib/api";

interface AgentAction {
  timestamp: string;
  agent: string;
  customer_id: number;
  trigger: string;
  scores?: Record<string, number>;
  response?: string;
  structured_output?: StructuredOutput;
  status: string;
  error?: string;
}

interface RecommendedAction {
  action_type: string;
  label: string;
  details: string;
  urgency: string;
}

interface StructuredOutput {
  customer_id: number;
  assessment: string;
  recommended_actions: RecommendedAction[];
  autonomy_tier: number;
  // Prospect-specific
  propensity_confidence?: string;
  intent_signals?: string[];
  predicted_product?: string;
  recommended_amount?: number;
  estimated_emi?: number;
  monthly_surplus?: number;
  call_script?: string;
  // Risk-specific
  default_probability?: number;
  stress_level?: string;
  root_cause?: string;
  top_risk_factors?: string[];
  is_temporary?: boolean;
  // Health-specific
  composite_score?: number;
  strengths?: string[];
  concerns?: string[];
  lending_recommendation?: string;
  suggested_amount?: number;
  special_conditions?: string;
  // Engagement-specific
  trigger_reason?: string;
  message_content?: string;
  message_language?: string;
  channel?: string;
  send_timing?: string;
}

interface AgentSummary {
  [agent: string]: { count: number; status: string };
}

const AGENT_META: Record<string, { label: string; color: string; icon: string }> = {
  prospect_agent: {
    label: "Prospect Agent",
    color: "#2563eb",
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="19" x2="19" y1="8" y2="14"/><line x1="22" x2="16" y1="11" y2="11"/></svg>`,
  },
  risk_agent: {
    label: "Risk Agent",
    color: "#ef4444",
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><line x1="12" x2="12" y1="9" y2="13"/><line x1="12" x2="12.01" y1="17" y2="17"/></svg>`,
  },
  health_agent: {
    label: "Health Agent",
    color: "#10b981",
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>`,
  },
  engagement_agent: {
    label: "Engagement Agent",
    color: "#8b5cf6",
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
  },
};

const URGENCY_STYLES: Record<string, string> = {
  critical: "bg-red-50 border-red-200 text-red-700",
  high: "bg-blue-50 border-blue-200 text-blue-700",
  medium: "bg-amber-50 border-amber-200 text-amber-700",
  low: "bg-gray-50 border-gray-200 text-gray-600",
};

/**
 * Parse agent response text (may contain markdown-like formatting)
 * into presentable React elements.
 */
function formatAgentResponse(raw: string): React.ReactNode {
  // Clean up markdown artifacts
  const lines = raw
    .replace(/\*\*/g, "")       // remove bold markers
    .replace(/<br\s*\/?>/g, "\n") // convert <br> to newlines
    .replace(/\|[-]+/g, "")     // remove table separators
    .replace(/\|\s*\|/g, "")    // remove empty table cells
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => l.length > 0 && !l.match(/^\|[\s-]*\|?$/)); // remove empty table rows

  const elements: React.ReactNode[] = [];

  lines.forEach((line, i) => {
    // Section headers (lines ending with : or starting with caps + containing key terms)
    if (
      line.match(/^(Assessment Summary|Action Taken|Top SHAP|Recommendation|Stress Level|Current PD|Intervention|Reasoning)/i) ||
      line.match(/^[A-Z][A-Za-z\s]+:$/)
    ) {
      elements.push(
        <p key={i} className="font-semibold text-[var(--text)] mt-3 mb-1 text-xs uppercase tracking-wide">
          {line.replace(/:$/, "")}
        </p>
      );
    }
    // Numbered items or bullet points
    else if (line.match(/^\d+\.\s/) || line.match(/^[-•]\s/)) {
      elements.push(
        <div key={i} className="flex gap-2 ml-2 mb-1">
          <span className="text-[var(--primary-blue)] flex-shrink-0">•</span>
          <span>{line.replace(/^\d+\.\s*/, "").replace(/^[-•]\s*/, "")}</span>
        </div>
      );
    }
    // Key-value pairs (lines with : separator)
    else if (line.includes(":") && line.indexOf(":") < 30 && !line.startsWith("http")) {
      const [key, ...rest] = line.split(":");
      const value = rest.join(":").trim();
      if (key.length < 30 && value) {
        elements.push(
          <div key={i} className="flex gap-2 mb-1">
            <span className="text-[var(--text-muted)] min-w-[120px]">{key.trim()}:</span>
            <span className="text-[var(--text)] font-medium">{value}</span>
          </div>
        );
      } else {
        elements.push(<p key={i} className="mb-1">{line}</p>);
      }
    }
    // Table-like rows (contain | separators)
    else if (line.includes("|") && line.split("|").length >= 3) {
      const cells = line.split("|").map((c) => c.trim()).filter(Boolean);
      elements.push(
        <div key={i} className="flex gap-4 mb-1 ml-2">
          {cells.map((cell, ci) => (
            <span key={ci} className={ci === 0 ? "text-[var(--text-muted)] min-w-[100px]" : "text-[var(--text)]"}>
              {cell}
            </span>
          ))}
        </div>
      );
    }
    // Regular text
    else {
      elements.push(<p key={i} className="mb-1">{line}</p>);
    }
  });

  return <>{elements}</>;
}

export default function AgentActions() {
  const [actions, setActions] = useState<AgentAction[]>([]);
  const [summary, setSummary] = useState<AgentSummary>({});
  const [activeFilter, setActiveFilter] = useState("all");

  useEffect(() => {
    fetchJSON<{ actions: AgentAction[]; summary: AgentSummary }>(
      `/agent/actions?agent_filter=${activeFilter}`
    ).then((d) => {
      setActions(d.actions);
      setSummary(d.summary);
    });
  }, [activeFilter]);

  // Load full summary on mount
  useEffect(() => {
    fetchJSON<{ actions: AgentAction[]; summary: AgentSummary }>("/agent/actions?agent_filter=all").then((d) => {
      setSummary(d.summary);
    });
  }, []);

  const allAgents = Object.keys(AGENT_META);

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold gradient-text mb-1">Agent Command Center</h2>
        <p className="text-sm text-[var(--text-muted)]">
          Multi-agent autonomous system — real-time actions and communications
        </p>
      </div>

      {/* Agent cards row */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {allAgents.map((agentKey) => {
          const meta = AGENT_META[agentKey];
          const count = summary[agentKey]?.count || 0;
          const isActive = activeFilter === agentKey;

          return (
            <button
              key={agentKey}
              onClick={() => setActiveFilter(isActive ? "all" : agentKey)}
              className={`card text-left transition-all cursor-pointer ${
                isActive ? "ring-2 ring-offset-1" : ""
              }`}
              style={{
                borderColor: isActive ? meta.color : undefined,
                ["--tw-ring-color" as string]: meta.color,
              }}
            >
              <div className="flex items-center gap-3 mb-2">
                <div
                  className="w-9 h-9 rounded-lg flex items-center justify-center"
                  style={{ background: meta.color + "15", color: meta.color }}
                  dangerouslySetInnerHTML={{ __html: meta.icon }}
                />
                <div>
                  <p className="text-sm font-semibold text-[var(--text)]">{meta.label}</p>
                  <p className="text-xs text-[var(--text-muted)]">
                    {count > 0 ? `${count} actions` : "No actions"}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ background: count > 0 ? meta.color : "#94a3b8" }}
                />
                <span className="text-xs text-[var(--text-muted)]">
                  {count > 0 ? "Active" : "Idle"}
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Filter indicator */}
      <div className="flex items-center gap-3 mb-4">
        <p className="text-sm font-medium text-[var(--text-secondary)]">
          Activity Feed
          {activeFilter !== "all" && (
            <span className="ml-2 text-xs px-2 py-0.5 rounded-full" style={{
              background: AGENT_META[activeFilter]?.color + "15",
              color: AGENT_META[activeFilter]?.color,
            }}>
              {AGENT_META[activeFilter]?.label}
            </span>
          )}
        </p>
        {activeFilter !== "all" && (
          <button
            onClick={() => setActiveFilter("all")}
            className="text-xs text-[var(--text-muted)] hover:text-[var(--text)] underline"
          >
            Show all
          </button>
        )}
      </div>

      {/* Activity feed */}
      <div className="space-y-4 max-h-[520px] overflow-auto">
        {actions.length === 0 && (
          <div className="card text-center py-12">
            <p className="text-[var(--text-muted)]">No agent actions recorded yet.</p>
            <p className="text-xs text-[var(--text-muted)] mt-1">
              Run the batch: <code className="bg-[#f1f5f9] px-2 py-0.5 rounded">python -m agents.run_batch --limit 3</code>
            </p>
          </div>
        )}

        {actions.map((action, idx) => {
          const meta = AGENT_META[action.agent] || { label: action.agent, color: "#666", icon: "" };
          const urgency = action.response?.toLowerCase().includes("critical")
            ? "critical"
            : action.response?.toLowerCase().includes("urgent")
            ? "high"
            : action.agent === "risk_agent"
            ? "high"
            : "medium";

          return (
            <div key={idx} className="card">
              {/* Header */}
              <div className="flex items-center gap-3 mb-3">
                <div
                  className="w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0"
                  style={{ background: meta.color + "15", color: meta.color }}
                  dangerouslySetInnerHTML={{ __html: meta.icon }}
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold" style={{ color: meta.color }}>
                      {meta.label}
                    </span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded border font-medium uppercase ${URGENCY_STYLES[urgency]}`}>
                      {urgency}
                    </span>
                  </div>
                  <p className="text-xs text-[var(--text-muted)]">
                    Customer {action.customer_id} • {action.trigger?.replace(/_/g, " ")}
                  </p>
                </div>
                <span className="text-xs text-[var(--text-muted)]">
                  {new Date(action.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>

              {/* Scores */}
              {action.scores && (
                <div className="flex gap-4 mb-3 text-xs">
                  {Object.entries(action.scores).map(([k, v]) => (
                    v != null && (
                      <span key={k} className="text-[var(--text-muted)]">
                        {k.replace(/_/g, " ")}: <span className="font-medium text-[var(--text)]">{v}%</span>
                      </span>
                    )
                  ))}
                </div>
              )}

              {/* Structured Output */}
              {action.structured_output && (
                <div className="space-y-3">
                  {/* Assessment */}
                  <p className="text-sm text-[var(--text)] leading-relaxed">
                    {action.structured_output.assessment}
                  </p>

                  {/* Key metrics row */}
                  <div className="flex flex-wrap gap-3">
                    {action.structured_output.predicted_product && (
                      <span className="text-xs px-2 py-1 rounded-md bg-blue-50 text-blue-700 border border-blue-200">
                        {action.structured_output.predicted_product}
                      </span>
                    )}
                    {action.structured_output.recommended_amount != null && action.structured_output.recommended_amount > 0 && (
                      <span className="text-xs px-2 py-1 rounded-md bg-green-50 text-green-700 border border-green-200">
                        ₹{action.structured_output.recommended_amount.toLocaleString()}
                      </span>
                    )}
                    {action.structured_output.estimated_emi != null && action.structured_output.estimated_emi > 0 && (
                      <span className="text-xs px-2 py-1 rounded-md bg-gray-50 text-gray-700 border border-gray-200">
                        EMI ₹{action.structured_output.estimated_emi.toLocaleString()}
                      </span>
                    )}
                    {action.structured_output.default_probability != null && (
                      <span className={`text-xs px-2 py-1 rounded-md border ${
                        action.structured_output.default_probability > 30
                          ? "bg-red-50 text-red-700 border-red-200"
                          : "bg-amber-50 text-amber-700 border-amber-200"
                      }`}>
                        PD: {action.structured_output.default_probability}%
                      </span>
                    )}
                    {action.structured_output.composite_score != null && (
                      <span className="text-xs px-2 py-1 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200">
                        Health: {action.structured_output.composite_score}/100
                      </span>
                    )}
                    {action.structured_output.lending_recommendation && (
                      <span className={`text-xs px-2 py-1 rounded-md border ${
                        action.structured_output.lending_recommendation === "approve"
                          ? "bg-green-50 text-green-700 border-green-200"
                          : action.structured_output.lending_recommendation === "review"
                          ? "bg-amber-50 text-amber-700 border-amber-200"
                          : "bg-red-50 text-red-700 border-red-200"
                      }`}>
                        {action.structured_output.lending_recommendation.toUpperCase()}
                      </span>
                    )}
                    {action.structured_output.stress_level && (
                      <span className={`text-xs px-2 py-1 rounded-md border ${
                        action.structured_output.stress_level === "escalate" || action.structured_output.stress_level === "action_required"
                          ? "bg-red-50 text-red-700 border-red-200"
                          : "bg-amber-50 text-amber-700 border-amber-200"
                      }`}>
                        {action.structured_output.stress_level.replace(/_/g, " ")}
                      </span>
                    )}
                    {action.structured_output.is_temporary != null && (
                      <span className={`text-xs px-2 py-1 rounded-md border ${
                        action.structured_output.is_temporary
                          ? "bg-blue-50 text-blue-700 border-blue-200"
                          : "bg-red-50 text-red-700 border-red-200"
                      }`}>
                        {action.structured_output.is_temporary ? "Temporary" : "Structural"}
                      </span>
                    )}
                  </div>

                  {/* Root cause / signals */}
                  {action.structured_output.root_cause && (
                    <div className="bg-[#f8fafc] rounded-lg p-3 border border-[var(--card-border)]">
                      <p className="text-[10px] uppercase tracking-wide text-[var(--text-muted)] mb-1">Root Cause</p>
                      <p className="text-xs text-[var(--text-secondary)]">{action.structured_output.root_cause}</p>
                    </div>
                  )}

                  {/* Message preview for engagement */}
                  {action.structured_output.message_content && (
                    <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="text-[10px] uppercase tracking-wide text-blue-600">Message Preview</p>
                        {action.structured_output.channel && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-600">
                            {action.structured_output.channel}
                          </span>
                        )}
                        {action.structured_output.send_timing && (
                          <span className="text-[10px] text-blue-400">{action.structured_output.send_timing}</span>
                        )}
                      </div>
                      <p className="text-xs text-blue-800 italic">&ldquo;{action.structured_output.message_content}&rdquo;</p>
                    </div>
                  )}

                  {/* Make Call button for Engagement Agent */}
                  {action.agent === "engagement_agent" && (
                    <div className="mt-3">
                      <button
                        onClick={async () => {
                          try {
                            await fetchJSON(`/agent/call/${action.customer_id}`, { method: "POST" });
                            alert(`Call initiated for customer ${action.customer_id}. RM dashboard updated.`);
                          } catch {
                            alert(`Call queued for customer ${action.customer_id}.`);
                          }
                        }}
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm text-white transition-all hover:shadow-md active:scale-95"
                        style={{ background: "linear-gradient(135deg, #8b5cf6, #6d28d9)" }}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                        </svg>
                        Make Call
                      </button>
                    </div>
                  )}

                  {/* Call Script for Prospect Agent */}
                  {action.agent === "prospect_agent" && action.structured_output.call_script && (
                    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200 mt-3">
                      <div className="flex items-center gap-2 mb-2">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                        </svg>
                        <p className="text-xs font-semibold text-blue-700 uppercase tracking-wide">RM Call Script</p>
                      </div>
                      <div className="text-xs text-blue-900 leading-relaxed whitespace-pre-wrap">
                        {action.structured_output.call_script}
                      </div>
                    </div>
                  )}

                  {/* Strengths & Concerns (Health) */}
                  {action.structured_output.strengths && action.structured_output.strengths.length > 0 && (
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <p className="text-[10px] uppercase tracking-wide text-[var(--text-muted)] mb-1">Strengths</p>
                        {action.structured_output.strengths.map((s, i) => (
                          <p key={i} className="text-xs text-green-700 flex items-start gap-1 mb-0.5">
                            <span className="text-green-500 mt-0.5">✓</span> {s}
                          </p>
                        ))}
                      </div>
                      {action.structured_output.concerns && action.structured_output.concerns.length > 0 && (
                        <div>
                          <p className="text-[10px] uppercase tracking-wide text-[var(--text-muted)] mb-1">Concerns</p>
                          {action.structured_output.concerns.map((c, i) => (
                            <p key={i} className="text-xs text-amber-700 flex items-start gap-1 mb-0.5">
                              <span className="text-amber-500 mt-0.5">!</span> {c}
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Action Buttons */}
                  {action.structured_output.recommended_actions && action.structured_output.recommended_actions.length > 0 && (
                    <div className="border-t border-[var(--card-border)] pt-3 mt-3">
                      <p className="text-[10px] uppercase tracking-wide text-[var(--text-muted)] mb-2">Recommended Actions</p>
                      <div className="flex flex-wrap gap-2">
                        {action.structured_output.recommended_actions.map((ra, i) => (
                          <button
                            key={i}
                            className={`text-xs px-3 py-1.5 rounded-md font-medium border transition-all hover:shadow-sm ${
                              ra.urgency === "critical"
                                ? "bg-red-600 text-white border-red-600 hover:bg-red-700"
                                : ra.urgency === "high"
                                ? "bg-[var(--primary-blue)] text-white border-[var(--primary-blue)] hover:opacity-90"
                                : "bg-white text-[var(--text)] border-[var(--card-border)] hover:border-[var(--primary-blue)] hover:text-[var(--primary-blue)]"
                            }`}
                            title={ra.details}
                          >
                            {ra.label}
                          </button>
                        ))}
                      </div>
                      {/* Show details of first action */}
                      <p className="text-[10px] text-[var(--text-muted)] mt-2 italic">
                        {action.structured_output.recommended_actions[0]?.details}
                      </p>
                    </div>
                  )}

                  {/* Autonomy tier */}
                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-[10px] text-[var(--text-muted)]">
                      Tier {action.structured_output.autonomy_tier}:
                      {action.structured_output.autonomy_tier === 1 && " Autonomous"}
                      {action.structured_output.autonomy_tier === 2 && " Act + Notify"}
                      {action.structured_output.autonomy_tier === 3 && " Human Decides"}
                    </span>
                  </div>
                </div>
              )}

              {/* Fallback: raw response (for old format) */}
              {!action.structured_output && action.response && (
                <div className="bg-[#f8fafc] rounded-lg p-4 border border-[var(--card-border)]">
                  <div className="text-xs text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap agent-response">
                    {formatAgentResponse(action.response)}
                  </div>
                </div>
              )}

              {/* Error */}
              {action.error && (
                <div className="bg-red-50 rounded-lg p-3 border border-red-200">
                  <p className="text-xs text-red-600">{action.error}</p>
                </div>
              )}

              {/* Status badge */}
              <div className="mt-3 flex items-center gap-2">
                <span className={`w-1.5 h-1.5 rounded-full ${action.status === "completed" ? "bg-green-500" : "bg-red-500"}`} />
                <span className="text-[10px] text-[var(--text-muted)] uppercase">{action.status}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
