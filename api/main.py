"""
api/main.py  —  Phase 5 of the IDBI ML pipeline.

FastAPI scoring service exposing ML predictions, health cards, prospect lists,
early-warning accounts, and per-customer SHAP explanations.

Endpoints (from feature-engineering-README.md):
  GET  /api/customers                    → list all customers with scores
  GET  /api/customers/{id}               → full profile + all scores
  GET  /api/customers/{id}/propensity    → propensity score + SHAP top factors
  GET  /api/customers/{id}/health        → 6-dimension health card
  GET  /api/customers/{id}/default       → PD score + SHAP top factors
  GET  /api/prospects                    → ranked prospect list (score > threshold)
  GET  /api/early-warning               → accounts with elevated PD
  POST /api/agent/analyze/{id}           → trigger agent-style reasoning summary

Run:  uvicorn api.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
MODEL_DIR = ROOT / "data" / "models"

# --------------------------------------------------------------------------- #
# Load data at startup
# --------------------------------------------------------------------------- #
app = FastAPI(
    title="IDBI Unified Agentic Platform — ML Scoring API",
    version="1.0.0",
    description="Serves propensity, health score, and default predictions with SHAP explanations.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load() -> dict[str, Any]:
    """Load all models, features, SHAP values into memory at startup."""
    data: dict[str, Any] = {}

    # Feature matrix (+ labels)
    feat = pd.read_csv(PROC / "feature_matrix.csv")
    data["feat"] = feat
    data["account_ids"] = feat["account_id"].tolist()

    # Metadata
    meta = json.loads((MODEL_DIR / "model_metadata.json").read_text(encoding="utf-8"))
    data["meta"] = meta
    feature_cols = meta["feature_columns"]
    data["feature_cols"] = feature_cols

    # Models
    data["propensity_model"] = joblib.load(MODEL_DIR / "propensity_model.pkl")
    data["health_models"] = joblib.load(MODEL_DIR / "health_model.pkl")
    data["default_model"] = joblib.load(MODEL_DIR / "default_model.pkl")

    # Precompute predictions for fast serving
    X = feat[feature_cols].fillna(0).replace([np.inf, -np.inf], 0).to_numpy()
    data["X"] = X

    data["propensity_scores"] = data["propensity_model"].predict_proba(X)[:, 1]

    health_preds = {}
    for dim, model in data["health_models"].items():
        health_preds[dim] = model.predict(X).clip(0, 100).round(1)
    data["health_preds"] = health_preds

    data["default_scores"] = data["default_model"].predict_proba(X)[:, 1]

    # SHAP values (pre-loaded for top-factor lookup)
    shap_prop = pd.read_csv(MODEL_DIR / "shap_propensity.csv")
    shap_def = pd.read_csv(MODEL_DIR / "shap_default.csv")
    data["shap_propensity"] = shap_prop
    data["shap_default"] = shap_def

    # Health SHAP
    health_shap = {}
    for dim in data["health_models"].keys():
        fp = MODEL_DIR / f"shap_health_{dim}.csv"
        if fp.exists():
            health_shap[dim] = pd.read_csv(fp)
    data["health_shap"] = health_shap

    # Global importance
    data["global_importance"] = json.loads(
        (MODEL_DIR / "shap_global_importance.json").read_text(encoding="utf-8"))

    # Build account_id -> row index map
    data["id_to_idx"] = {aid: i for i, aid in enumerate(data["account_ids"])}

    return data


_DATA: dict[str, Any] = {}


@app.on_event("startup")
def startup():
    global _DATA
    _DATA = _load()


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _get_idx(customer_id: int) -> int:
    idx = _DATA["id_to_idx"].get(customer_id)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    return idx


def _top_shap_factors(shap_df: pd.DataFrame, idx: int, n: int = 5) -> list[dict]:
    """Return top-N SHAP factors for a given row."""
    row = shap_df.iloc[idx]
    shap_cols = [c for c in shap_df.columns if c.startswith("shap_")]
    vals = row[shap_cols].to_dict()
    sorted_factors = sorted(vals.items(), key=lambda x: abs(x[1]), reverse=True)[:n]
    return [{"feature": k.replace("shap_", ""), "shap_value": round(float(v), 4)}
            for k, v in sorted_factors]


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #
@app.get("/api/customers")
def list_customers(
    limit: int = Query(50, ge=1, le=4500),
    offset: int = Query(0, ge=0),
):
    """List customers with summary scores."""
    feat = _DATA["feat"]
    end = min(offset + limit, len(feat))
    rows = []
    for i in range(offset, end):
        acc = int(feat.iloc[i]["account_id"])
        rows.append({
            "account_id": acc,
            "propensity_score": round(float(_DATA["propensity_scores"][i]) * 100, 1),
            "default_probability": round(float(_DATA["default_scores"][i]) * 100, 1),
            "has_loan": int(feat.iloc[i].get("has_loan", 0)),
            "msme_flag": int(feat.iloc[i].get("msme_flag", 0)),
        })
    return {"total": len(feat), "offset": offset, "limit": limit, "customers": rows}


@app.get("/api/customers/{customer_id}")
def get_customer(customer_id: int):
    """Full profile + all scores for a single customer."""
    idx = _get_idx(customer_id)
    feat = _DATA["feat"]
    row = feat.iloc[idx]

    # health scores
    health = {dim: float(preds[idx])
              for dim, preds in _DATA["health_preds"].items()}
    health["composite"] = round(np.mean(list(health.values())), 1)

    profile = {
        "account_id": customer_id,
        "district_id": int(row.get("district_id", 0)),
        "has_loan": int(row.get("has_loan", 0)),
        "loan_status": str(row.get("loan_status", "")),
        "propensity_score": round(float(_DATA["propensity_scores"][idx]) * 100, 1),
        "default_probability": round(float(_DATA["default_scores"][idx]) * 100, 1),
        "health_scores": health,
        "msme_flag": int(row.get("msme_flag", 0)),
        "health_quality": str(row.get("health_quality", "")),
        "monthly_income_avg": round(float(row.get("monthly_income_avg", 0)), 0),
        "monthly_surplus_avg": round(float(row.get("monthly_surplus_avg", 0)), 0),
        "balance_latest": round(float(row.get("balance_latest", 0)), 0),
    }
    return profile


@app.get("/api/customers/{customer_id}/propensity")
def get_propensity(customer_id: int):
    """Propensity score + SHAP explanation."""
    idx = _get_idx(customer_id)
    score = round(float(_DATA["propensity_scores"][idx]) * 100, 1)
    factors = _top_shap_factors(_DATA["shap_propensity"], idx)

    # predicted product
    row = _DATA["feat"].iloc[idx]
    intent = str(row.get("intent_product", ""))
    product = intent if intent else ("Personal Loan" if score > 50 else "None")

    return {
        "account_id": customer_id,
        "propensity_score": score,
        "predicted_product": product,
        "confidence": "High" if score >= 70 else ("Medium" if score >= 40 else "Low"),
        "top_factors": factors,
    }


@app.get("/api/customers/{customer_id}/health")
def get_health(customer_id: int):
    """6-dimension health card + SHAP per dimension."""
    idx = _get_idx(customer_id)
    dimensions = {}
    for dim, preds in _DATA["health_preds"].items():
        dim_score = float(preds[idx])
        factors = []
        if dim in _DATA["health_shap"]:
            factors = _top_shap_factors(_DATA["health_shap"][dim], idx, n=3)
        dimensions[dim] = {"score": round(dim_score, 1), "top_factors": factors}

    composite = round(np.mean([d["score"] for d in dimensions.values()]), 1)
    return {
        "account_id": customer_id,
        "composite_health_score": composite,
        "dimensions": dimensions,
        "recommendation": (
            "Approve" if composite >= 60 else
            "Review" if composite >= 40 else "Decline"
        ),
    }


@app.get("/api/customers/{customer_id}/default")
def get_default(customer_id: int):
    """Default probability + SHAP explanation."""
    idx = _get_idx(customer_id)
    pd_score = round(float(_DATA["default_scores"][idx]) * 100, 1)
    factors = _top_shap_factors(_DATA["shap_default"], idx)

    # stress level
    if pd_score >= 30:
        level = "Level 3 — Action Required"
    elif pd_score >= 15:
        level = "Level 2 — Alert"
    elif pd_score >= 10:
        level = "Level 1 — Watch"
    else:
        level = "Healthy"

    return {
        "account_id": customer_id,
        "default_probability_pct": pd_score,
        "stress_level": level,
        "top_factors": factors,
    }


@app.get("/api/prospects")
def get_prospects(
    threshold: float = Query(70.0, ge=0, le=100),
    limit: int = Query(50, ge=1, le=500),
):
    """Ranked prospect list — accounts with propensity > threshold and low default risk."""
    scores = _DATA["propensity_scores"] * 100
    default_scores = _DATA["default_scores"] * 100
    feat = _DATA["feat"]

    # filter: propensity above threshold AND default < 15%
    mask = (scores >= threshold) & (default_scores < 15)
    indices = np.where(mask)[0]
    # sort by propensity descending
    sorted_idx = indices[np.argsort(scores[indices])[::-1]][:limit]

    prospects = []
    for i in sorted_idx:
        row = feat.iloc[i]
        prospects.append({
            "account_id": int(row["account_id"]),
            "propensity_score": round(float(scores[i]), 1),
            "default_probability": round(float(default_scores[i]), 1),
            "predicted_product": str(row.get("intent_product", "")) or "Personal Loan",
            "monthly_surplus": round(float(row.get("monthly_surplus_avg", 0)), 0),
        })
    return {"threshold": threshold, "count": len(prospects), "prospects": prospects}


@app.get("/api/early-warning")
def get_early_warning(
    threshold: float = Query(15.0, ge=0, le=100),
    limit: int = Query(50, ge=1, le=500),
):
    """Accounts with elevated default probability (PD spike / early warning)."""
    default_scores = _DATA["default_scores"] * 100
    feat = _DATA["feat"]

    # only accounts with loans
    loan_mask = feat["has_loan"].eq(1).to_numpy()
    indices = np.where((default_scores >= threshold) & loan_mask)[0]
    sorted_idx = indices[np.argsort(default_scores[indices])[::-1]][:limit]

    warnings = []
    for i in sorted_idx:
        row = feat.iloc[i]
        factors = _top_shap_factors(_DATA["shap_default"], i, n=3)
        warnings.append({
            "account_id": int(row["account_id"]),
            "default_probability_pct": round(float(default_scores[i]), 1),
            "loan_status": str(row.get("loan_status", "")),
            "top_stress_factors": factors,
        })
    return {"threshold": threshold, "count": len(warnings), "accounts": warnings}


@app.post("/api/agent/analyze/{customer_id}")
def agent_analyze(customer_id: int):
    """Simulate agent reasoning: summarize the customer's ML signals and recommend action."""
    idx = _get_idx(customer_id)
    feat = _DATA["feat"]
    row = feat.iloc[idx]

    prop_score = round(float(_DATA["propensity_scores"][idx]) * 100, 1)
    pd_score = round(float(_DATA["default_scores"][idx]) * 100, 1)
    health_scores = {dim: round(float(preds[idx]), 1)
                     for dim, preds in _DATA["health_preds"].items()}
    composite_health = round(np.mean(list(health_scores.values())), 1)

    # Agent-style reasoning
    signals = []
    recommended_action = "monitor"
    urgency = "low"

    if prop_score >= 70 and pd_score < 15:
        signals.append(f"High propensity ({prop_score}) with low default risk ({pd_score}%)")
        recommended_action = "route_to_prospect_agent"
        urgency = "high"
    if pd_score >= 30:
        signals.append(f"Default probability spiked to {pd_score}% — intervention needed")
        recommended_action = "route_to_risk_agent"
        urgency = "critical"
    elif pd_score >= 15:
        signals.append(f"Elevated default risk ({pd_score}%) — monitor closely")
        recommended_action = "alert_rm"
        urgency = "medium"
    if composite_health < 40:
        signals.append(f"Low health score ({composite_health}) — financial stress detected")
    if int(row.get("msme_flag", 0)) == 1:
        signals.append(f"MSME account — health quality: {row.get('health_quality', 'unknown')}")

    if not signals:
        signals.append("No significant signals detected. Customer appears healthy.")

    return {
        "account_id": customer_id,
        "propensity_score": prop_score,
        "default_probability_pct": pd_score,
        "composite_health_score": composite_health,
        "health_dimensions": health_scores,
        "signals": signals,
        "recommended_action": recommended_action,
        "urgency": urgency,
    }
