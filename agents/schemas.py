"""
agents/schemas.py — Pydantic models for structured agent output.

These define the exact shape of each agent's response,
enabling clean UI rendering and actionable buttons.
"""

from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class RecommendedAction(BaseModel):
    """A single recommended action the human can approve/execute."""
    action_type: Literal[
        "generate_loan_offer",
        "initiate_call_outreach",
        "initiate_text_outreach",
        "initiate_phone_call",
        "send_push_notification",
        "alert_rm",
        "escalate_to_risk_committee",
        "recommend_moratorium",
        "recommend_restructure",
        "flag_for_underwriter",
        "schedule_followup",
        "no_action",
    ] = Field(description="Type of action to take")
    label: str = Field(description="Human-readable button label for this action")
    details: str = Field(description="Specifics — e.g. loan amount, message content, RM name")
    urgency: Literal["low", "medium", "high", "critical"] = Field(description="How urgent is this action")


class ProspectAgentOutput(BaseModel):
    """Structured output from the Prospect Agent."""
    customer_id: int = Field(description="The customer account ID analyzed")
    assessment: str = Field(description="2-3 sentence summary of why this is a good/bad prospect")
    propensity_confidence: Literal["high", "medium", "low"] = Field(description="Confidence in the propensity signal")
    intent_signals: list[str] = Field(description="Key intent signals detected from SHAP factors")
    predicted_product: str = Field(description="Best matching loan product")
    recommended_amount: int = Field(description="Suggested loan amount in INR")
    estimated_emi: int = Field(description="Estimated monthly EMI in INR")
    monthly_surplus: int = Field(description="Customer's monthly surplus in INR")
    call_script: str = Field(description="Personalized RM call script tailored to this customer's profile, intent signals, and financial context. Include: opening line, value proposition, key talking points, objection handling, and closing with next steps.")
    recommended_actions: list[RecommendedAction] = Field(description="Actions for human to approve")
    autonomy_tier: Literal[1, 2, 3] = Field(description="1=autonomous, 2=act+notify, 3=human decides")


class RiskAgentOutput(BaseModel):
    """Structured output from the Risk Agent."""
    customer_id: int = Field(description="The customer account ID analyzed")
    assessment: str = Field(description="2-3 sentence summary of the risk situation")
    default_probability: float = Field(description="Current PD percentage")
    stress_level: Literal["watch", "alert", "action_required", "escalate"] = Field(description="Severity classification")
    root_cause: str = Field(description="Likely root cause — e.g. 'job transition', 'income loss', 'over-leverage'")
    top_risk_factors: list[str] = Field(description="Top 3 SHAP factors driving the risk")
    is_temporary: bool = Field(description="Whether the stress appears temporary or structural")
    recommended_actions: list[RecommendedAction] = Field(description="Actions for human to approve")
    autonomy_tier: Literal[1, 2, 3] = Field(description="1=autonomous, 2=act+notify, 3=human decides")


class HealthAgentOutput(BaseModel):
    """Structured output from the Health Agent."""
    customer_id: int = Field(description="The customer account ID analyzed")
    assessment: str = Field(description="2-3 sentence summary of financial health")
    composite_score: float = Field(description="Overall health score 0-100")
    strengths: list[str] = Field(description="Key financial strengths identified")
    concerns: list[str] = Field(description="Key concerns or risks identified")
    lending_recommendation: Literal["approve", "review", "decline"] = Field(description="Credit decision recommendation")
    suggested_amount: int = Field(description="Recommended loan amount in INR (0 if decline)")
    special_conditions: str = Field(description="Any special structuring — e.g. 'lower EMI in June-July'")
    recommended_actions: list[RecommendedAction] = Field(description="Actions for human to approve")
    autonomy_tier: Literal[1, 2, 3] = Field(description="1=autonomous, 2=act+notify, 3=human decides")


class EngagementAgentOutput(BaseModel):
    """Structured output from the Engagement Agent."""
    customer_id: int = Field(description="The customer account ID")
    assessment: str = Field(description="2-3 sentence summary of why we're engaging this customer")
    trigger_reason: str = Field(description="What triggered this engagement — e.g. 'high propensity', 'life event'")
    message_content: str = Field(description="The actual message to send to the customer")
    message_language: Literal["en", "hi", "ta", "te", "bn", "mr", "gu"] = Field(description="Language for the message")
    channel: Literal["push", "sms", "whatsapp", "email", "in_app"] = Field(description="Delivery channel")
    send_timing: str = Field(description="When to send — e.g. '7 PM today', 'tomorrow morning'")
    recommended_actions: list[RecommendedAction] = Field(description="Actions for human to approve")
    autonomy_tier: Literal[1, 2, 3] = Field(description="1=autonomous, 2=act+notify, 3=human decides")
