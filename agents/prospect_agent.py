"""
agents/prospect_agent.py — Prospect Agent

Qualifies high-propensity leads, matches them to loan products,
generates personalized offers, and routes to RM for follow-up.
"""

from strands import Agent
from strands.models.bedrock import BedrockModel

from .config import MODEL_ID, AWS_REGION
from .tools import (
    get_customer_profile,
    get_propensity_details,
    get_default_risk,
    generate_loan_offer,
    send_rm_alert,
    send_customer_notification,
)

SYSTEM_PROMPT = """You are the Prospect Agent for IDBI Bank's Agentic Intelligence Platform.

Your role: Qualify high-propensity loan prospects and take action to convert them.

You receive customers who have been flagged by the ML pipeline with high propensity scores
(>70) and low default risk (<15%). Your job is to:

1. VALIDATE the intent signal — check the SHAP factors to confirm genuine intent
2. ASSESS capacity — look at monthly surplus, income stability
3. MATCH product — determine the best loan product (Auto/Home/Personal)
4. SIZE the offer — calculate appropriate loan amount based on surplus (EMI should be < 40% of surplus)
5. DECIDE action:
   - If high confidence (score > 80, clear intent signals): Generate pre-approved offer + notify RM
   - If medium confidence (score 70-80): Add to RM call list with talking points
   - Always log your reasoning

Rules:
- Never approve if default risk > 15%
- EMI should not exceed 40% of monthly surplus
- Always explain WHY this customer is a good prospect
- Be specific about timing and channel for outreach
- Output your final action as a clear structured decision
"""


def create_prospect_agent() -> Agent:
    """Create and return the Prospect Agent instance."""
    model = BedrockModel(
        model_id=MODEL_ID,
        region_name=AWS_REGION,
        temperature=0.3,
        max_tokens=2048,
    )

    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            get_customer_profile,
            get_propensity_details,
            get_default_risk,
            generate_loan_offer,
            send_rm_alert,
            send_customer_notification,
        ],
    )


def run_prospect_agent(customer_id: int) -> dict:
    """Run the Prospect Agent for a single customer. Returns structured action."""
    from .schemas import ProspectAgentOutput

    agent = create_prospect_agent()

    prompt = f"""Analyze customer {customer_id} as a potential loan prospect.

Fetch their profile, propensity details, and default risk. Then decide:
- Is this a genuine high-quality lead?
- What loan product and amount should we offer?
- What actions should be taken?

Use the tools to gather data, then provide your structured assessment."""

    result = agent(prompt, structured_output_model=ProspectAgentOutput)

    output: ProspectAgentOutput = result.structured_output
    return {
        "agent": "prospect_agent",
        "customer_id": customer_id,
        "structured_output": output.model_dump(),
    }
