"""
agents/config.py — Bedrock model configuration and shared constants.
"""

import os

# Bedrock model
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "openai.gpt-oss-120b-1:0")
AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")

# API base URL (our own scoring service)
API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")

# Autonomy tiers
TIER_AUTONOMOUS = 1       # Agent acts alone
TIER_ACT_NOTIFY = 2       # Agent acts + notifies human
TIER_HUMAN_DECIDES = 3    # Agent recommends, human approves

# Thresholds (matching API logic)
PROPENSITY_THRESHOLD = 70.0
DEFAULT_ALERT_THRESHOLD = 30.0
DEFAULT_WATCH_THRESHOLD = 15.0
HEALTH_APPROVE_THRESHOLD = 60.0
HEALTH_REVIEW_THRESHOLD = 40.0
