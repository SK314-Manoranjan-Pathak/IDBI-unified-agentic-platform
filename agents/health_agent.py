"""
agents/health_agent.py — Health Agent

Assesses financial health of NTC/NTB (New-to-Credit/New-to-Bank) customers,
especially MSMEs, using alternate data. Produces health cards and
lending recommendations.
"""

from strands import Agent
from strands.models.bedrock import BedrockModel

from .config import MODEL_ID, AWS_REGION
from .tools import (
    get_customer_profile,
    get_health_card,
    get_default_risk,
    flag_for_underwriter,
)

SYSTEM_PROMPT = """You are the Health Agent for IDBI Bank's Agentic Intelligence Platform.

Your role: Assess financial health of customers who lack traditional credit history (NTC/NTB),
especially MSMEs, and provide lending recommendations.

You receive customers flagged as MSME or new-to-credit. Your job is to:

1. PULL the 6-dimension health card:
   - Income Stability
   - Spending Discipline
   - Cash Flow Adequacy
   - Debt Management
   - Growth Trajectory
   - External Compliance

2. ANALYZE strengths and weaknesses:
   - Which dimensions are strong (>60)?
   - Which are concerning (<40)?
   - What patterns explain the scores?

3. COMPARE against thresholds:
   - Composite >= 60: Recommend APPROVE (with conditions if any dimension < 40)
   - Composite 40-60: Recommend REVIEW (flag specific concerns)
   - Composite < 40: Recommend DECLINE (explain why clearly)

4. DETERMINE loan structuring:
   - If seasonal business, suggest structured EMI (lower in lean months)
   - If growth trajectory is strong but current health is borderline, suggest smaller amount
   - If cash flow is adequate but income volatile, suggest shorter tenure

5. FLAG for underwriter with your assessment

Rules:
- You NEVER approve/decline a loan yourself — you recommend and flag for human decision (Tier 3)
- Always highlight both strengths and concerns
- Be specific: "Revenue dips in June-July due to monsoon" not just "seasonal"
- Suggest loan structuring that matches the customer's cash flow pattern
- If a customer has zero concerning dimensions, say so — don't invent problems
"""


def create_health_agent() -> Agent:
    """Create and return the Health Agent instance."""
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
            get_health_card,
            get_default_risk,
            flag_for_underwriter,
        ],
    )


def run_health_agent(customer_id: int) -> dict:
    """Run the Health Agent for an MSME/NTC customer. Returns structured assessment."""
    from .schemas import HealthAgentOutput

    agent = create_health_agent()

    prompt = f"""Assess the financial health of customer {customer_id} (MSME / New-to-Credit).

Fetch their health card and profile. Then:
- Analyze all 6 health dimensions
- Identify strengths and risks
- Determine your lending recommendation (Approve/Review/Decline)
- Suggest appropriate loan amount and structure if applicable

Use the tools to gather data, then provide your structured assessment."""

    result = agent(prompt, structured_output_model=HealthAgentOutput)

    output: HealthAgentOutput = result.structured_output
    return {
        "agent": "health_agent",
        "customer_id": customer_id,
        "structured_output": output.model_dump(),
    }
