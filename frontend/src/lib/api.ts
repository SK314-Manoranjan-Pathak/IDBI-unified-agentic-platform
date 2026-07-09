const BASE = "/api";

export async function fetchJSON<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<T>;
}

export interface CustomerSummary {
  account_id: number;
  propensity_score: number;
  default_probability: number;
  has_loan: number;
  msme_flag: number;
}

export interface CustomerDetail {
  account_id: number;
  district_id: number;
  has_loan: number;
  loan_status: string;
  propensity_score: number;
  default_probability: number;
  health_scores: Record<string, number>;
  msme_flag: number;
  health_quality: string;
  monthly_income_avg: number;
  monthly_surplus_avg: number;
  balance_latest: number;
}

export interface PropensityResult {
  account_id: number;
  propensity_score: number;
  predicted_product: string;
  confidence: string;
  top_factors: { feature: string; shap_value: number }[];
}

export interface HealthResult {
  account_id: number;
  composite_health_score: number;
  dimensions: Record<string, { score: number; top_factors: { feature: string; shap_value: number }[] }>;
  recommendation: string;
}

export interface DefaultResult {
  account_id: number;
  default_probability_pct: number;
  stress_level: string;
  top_factors: { feature: string; shap_value: number }[];
}

export interface Prospect {
  account_id: number;
  propensity_score: number;
  default_probability: number;
  predicted_product: string;
  monthly_surplus: number;
}

export interface EarlyWarningAccount {
  account_id: number;
  default_probability_pct: number;
  loan_status: string;
  top_stress_factors: { feature: string; shap_value: number }[];
}
