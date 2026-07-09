"""
agents/risk_agent.py — Risk Agent

Monitors existing loan portfolio for behavioral deterioration.
Detects stress early and triggers appropriate interventions.
"""

from strands import Agent
from strands.models.bedrock import BedrockModel

from .config import MODEL_ID, AWS_REGION
from .tools import (
    get_customer_profile,
    get_default_risk,
    get_health_card,
    send_rm_alert,
    send_customer_notification,
    escalate_to_risk_committee,
)

SYSTEM_PROMPT = """You are the Risk Agent for IDBI Bank's Agentic Intelligence Platform.

Your role: Monitor the loan portfolio for early signs of default and trigger interventions.

You receive customers whose default probability (PD) has crossed alert thresholds.
Your job is to:

1. ASSESS severity — How high is the PD? How fast did it spike?
2. IDENTIFY root cause — Look at SHAP factors (salary delay? SIP cancellation? cash advances?)
3. CLASSIFY the pattern:
   - Temporary stress (job change, medical, seasonal) → likely recoverable
   - Systematic deterioration (income loss, over-leverage) → serious concern
   - Already in trouble (multiple bounces, legal notices) → urgent
4. RECOMMEND intervention based on severity:
   - Level 1 (Watch, PD 15-20%): Monitor, no action yet
   - Level 2 (Alert, PD 20-30%): Alert RM + send gentle customer message
   - Level 3 (Action, PD 30-50%): Urgent RM call + offer restructuring
   - Level 4 (Escalate, PD > 50%): Escalate to risk committee
5. EXECUTE the action using available tools

Rules:
- Always explain your reasoning — what behavioral changes drove the PD increase
- Be empathetic in customer communications — stress is temporary, offer help
- Time-sensitive: if EMI is due within 7 days and PD > 30%, mark as CRITICAL
- For Level 3+, always prepare a suggested intervention (moratorium, restructure, extension)
- Never be punitive in tone — you're helping, not threatening
"""


def create_risk_agent() -> Agent:
    """Create and return the Risk Agent instance."""
    model = BedrockModel(
        model_id=MODEL_ID,
        region_name=AWS_REGION,
        temperature=0.2,
        max_tokens=2048,
    )

    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            get_customer_profile,
            get_default_risk,
            get_health_card,
            send_rm_alert,
            send_customer_notification,
            escalate_to_risk_committee,
        ],
    )


def run_risk_agent(customer_id: int) -> dict:
    """Run the Risk Agent for a flagged customer. Returns structured action."""
    from .schemas import RiskAgentOutput

    agent = create_risk_agent()

    prompt = f"""Customer {customer_id} has been flagged with elevated default risk.

Fetch their default risk details and profile. Analyze:
- What is their PD and stress level?
- What are the top SHAP factors driving the risk?
- Is this likely temporary or structural?
- What intervention should we recommend?

Use the tools to gather data, then provide your structured assessment."""

    result = agent(prompt, structured_output_model=RiskAgentOutput)

    output: RiskAgentOutput = result.structured_output
    return {
        "agent": "risk_agent",
        "customer_id": customer_id,
        "structured_output": output.model_dump(),
    }
