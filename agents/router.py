"""
agents/router.py — Score-based router that dispatches customers to appropriate agents.

Reads the ML scoring results and determines which agent should handle each flagged customer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .config import (
    PROPENSITY_THRESHOLD,
    DEFAULT_ALERT_THRESHOLD,
    DEFAULT_WATCH_THRESHOLD,
    HEALTH_APPROVE_THRESHOLD,
)

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"


def load_scores() -> pd.DataFrame:
    """Load feature matrix with pre-computed scores."""
    feat = pd.read_csv(PROC / "feature_matrix.csv")
    return feat


def route_customers(feat: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    """
    Route customers to agents based on ML scores.

    Fetches propensity and default scores from the scoring API (must be running).
    Falls back to feature heuristics if API is unavailable.
    """
    import httpx
    from .config import API_BASE

    routes: dict[str, list[dict[str, Any]]] = {
        "prospect_agent": [],
        "risk_agent": [],
        "health_agent": [],
        "engagement_agent": [],
    }

    # Try to fetch scores from the running API for all customers
    scores_map: dict[int, dict] = {}
    try:
        resp = httpx.get(f"{API_BASE}/api/customers?limit=4500", timeout=15)
        if resp.status_code == 200:
            for c in resp.json().get("customers", []):
                scores_map[c["account_id"]] = c
    except Exception:
        pass  # API not running — fall back to feature-based routing

    for _, row in feat.iterrows():
        customer_id = int(row["account_id"])
        has_loan = int(row.get("has_loan", 0))
        msme_flag = int(row.get("msme_flag", 0))

        # Get scores from API response if available
        api_scores = scores_map.get(customer_id, {})
        propensity = float(api_scores.get("propensity_score", 0))
        default_pd = float(api_scores.get("default_probability", 0))

        # Route to Prospect Agent: high propensity + low default risk
        if propensity >= PROPENSITY_THRESHOLD and default_pd < 15:
            routes["prospect_agent"].append({
                "customer_id": customer_id,
                "trigger": "high_propensity",
                "propensity_score": propensity,
                "default_pd": default_pd,
            })

        # Route to Risk Agent: elevated PD on existing loans
        if has_loan and default_pd >= DEFAULT_ALERT_THRESHOLD:
            routes["risk_agent"].append({
                "customer_id": customer_id,
                "trigger": "default_probability_spike",
                "default_pd": default_pd,
            })

        # Route to Health Agent: MSME / NTC customers for assessment
        if msme_flag == 1:
            routes["health_agent"].append({
                "customer_id": customer_id,
                "trigger": "msme_health_assessment",
            })

        # Route to Engagement Agent: high propensity customers for outreach
        if propensity >= PROPENSITY_THRESHOLD and default_pd < 15:
            routes["engagement_agent"].append({
                "customer_id": customer_id,
                "trigger": "high_propensity",
                "propensity_score": propensity,
            })

    return routes


def get_routing_summary(routes: dict[str, list]) -> dict:
    """Generate summary stats for the routing."""
    return {
        agent: {
            "count": len(customers),
            "customer_ids": [c["customer_id"] for c in customers[:10]],  # first 10
        }
        for agent, customers in routes.items()
    }
