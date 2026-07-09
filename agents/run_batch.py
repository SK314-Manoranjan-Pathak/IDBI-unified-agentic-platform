"""
agents/run_batch.py — Entry point for running the multi-agent batch processing.

This script:
1. Loads ML scores from the latest batch
2. Routes customers to appropriate agents
3. Runs each agent on its flagged customers
4. Logs all actions to agents/actions/actions_latest.json

Usage:
    python -m agents.run_batch [--dry-run] [--limit N]
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from .router import load_scores, route_customers, get_routing_summary
from .prospect_agent import run_prospect_agent
from .risk_agent import run_risk_agent
from .health_agent import run_health_agent
from .engagement_agent import run_engagement_agent

ACTIONS_DIR = Path(__file__).resolve().parent / "actions"
ACTIONS_DIR.mkdir(exist_ok=True)


def run_batch(dry_run: bool = False, limit: int = 5) -> list[dict]:
    """
    Run all agents on the current batch of flagged customers.

    Args:
        dry_run: If True, only route and log — don't invoke LLM agents.
        limit: Max customers to process per agent (for cost control during dev).

    Returns:
        List of action records.
    """
    print("=" * 60)
    print(f"AGENT BATCH RUN — {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # Load and route
    feat = load_scores()
    routes = route_customers(feat)
    summary = get_routing_summary(routes)

    print("\nRouting Summary:")
    for agent, info in summary.items():
        print(f"  {agent}: {info['count']} customers flagged")

    if dry_run:
        print("\n[DRY RUN] Skipping agent invocations.")
        return []

    actions: list[dict] = []
    timestamp = datetime.now(timezone.utc).isoformat()

    # Run Prospect Agent
    print(f"\n--- Prospect Agent ({min(limit, len(routes['prospect_agent']))} customers) ---")
    for customer in routes["prospect_agent"][:limit]:
        cid = customer["customer_id"]
        print(f"  Processing customer {cid}...")
        try:
            result = run_prospect_agent(cid)
            actions.append({
                "timestamp": timestamp,
                "agent": "prospect_agent",
                "customer_id": cid,
                "trigger": customer["trigger"],
                "scores": {"propensity": customer.get("propensity_score"), "default_pd": customer.get("default_pd")},
                "response": result.get("response"),
                "structured_output": result.get("structured_output"),
                "status": "completed",
            })
        except Exception as e:
            print(f"    ERROR: {e}")
            actions.append({
                "timestamp": timestamp,
                "agent": "prospect_agent",
                "customer_id": cid,
                "trigger": customer["trigger"],
                "status": "error",
                "error": str(e),
            })

    # Run Risk Agent
    print(f"\n--- Risk Agent ({min(limit, len(routes['risk_agent']))} customers) ---")
    for customer in routes["risk_agent"][:limit]:
        cid = customer["customer_id"]
        print(f"  Processing customer {cid}...")
        try:
            result = run_risk_agent(cid)
            actions.append({
                "timestamp": timestamp,
                "agent": "risk_agent",
                "customer_id": cid,
                "trigger": customer["trigger"],
                "scores": {"default_pd": customer.get("default_pd")},
                "response": result.get("response"),
                "structured_output": result.get("structured_output"),
                "status": "completed",
            })
        except Exception as e:
            print(f"    ERROR: {e}")
            actions.append({
                "timestamp": timestamp,
                "agent": "risk_agent",
                "customer_id": cid,
                "trigger": customer["trigger"],
                "status": "error",
                "error": str(e),
            })

    # Run Health Agent
    print(f"\n--- Health Agent ({min(limit, len(routes['health_agent']))} customers) ---")
    for customer in routes["health_agent"][:limit]:
        cid = customer["customer_id"]
        print(f"  Processing customer {cid}...")
        try:
            result = run_health_agent(cid)
            actions.append({
                "timestamp": timestamp,
                "agent": "health_agent",
                "customer_id": cid,
                "trigger": customer["trigger"],
                "response": result.get("response"),
                "structured_output": result.get("structured_output"),
                "status": "completed",
            })
        except Exception as e:
            print(f"    ERROR: {e}")
            actions.append({
                "timestamp": timestamp,
                "agent": "health_agent",
                "customer_id": cid,
                "trigger": customer["trigger"],
                "status": "error",
                "error": str(e),
            })

    # Run Engagement Agent
    print(f"\n--- Engagement Agent ({min(limit, len(routes['engagement_agent']))} customers) ---")
    for customer in routes["engagement_agent"][:limit]:
        cid = customer["customer_id"]
        print(f"  Processing customer {cid}...")
        try:
            result = run_engagement_agent(cid, trigger_reason=customer["trigger"])
            actions.append({
                "timestamp": timestamp,
                "agent": "engagement_agent",
                "customer_id": cid,
                "trigger": customer["trigger"],
                "response": result.get("response"),
                "structured_output": result.get("structured_output"),
                "status": "completed",
            })
        except Exception as e:
            print(f"    ERROR: {e}")
            actions.append({
                "timestamp": timestamp,
                "agent": "engagement_agent",
                "customer_id": cid,
                "trigger": customer["trigger"],
                "status": "error",
                "error": str(e),
            })

    # Save actions log
    output_file = ACTIONS_DIR / "actions_latest.json"
    with open(output_file, "w") as f:
        json.dump(actions, f, indent=2, default=str)

    print(f"\n{'=' * 60}")
    print(f"BATCH COMPLETE — {len(actions)} actions logged to {output_file}")
    print(f"{'=' * 60}")

    return actions


def main():
    parser = argparse.ArgumentParser(description="Run multi-agent batch processing")
    parser.add_argument("--dry-run", action="store_true", help="Only route, don't invoke agents")
    parser.add_argument("--limit", type=int, default=3, help="Max customers per agent")
    args = parser.parse_args()

    run_batch(dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    main()
