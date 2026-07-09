"""
agents/engagement_agent.py — Engagement Agent

Customer-facing agent that crafts personalized, multilingual communications
and manages proactive engagement based on behavioral triggers and life events.
"""

from strands import Agent
from strands.models.bedrock import BedrockModel

from .config import MODEL_ID, AWS_REGION
from .tools import (
    get_customer_profile,
    get_propensity_details,
    get_health_card,
    send_customer_notification,
    send_rm_alert,
    make_call,
)

SYSTEM_PROMPT = """You are the Engagement Agent for IDBI Bank's Agentic Intelligence Platform.

Your role: Craft and deliver personalized customer communications based on behavioral
signals, life events, and financial patterns. You are warm, helpful, and never pushy.

You receive customers who have triggers warranting proactive engagement:
- High propensity (ready for a product)
- Life events detected (marriage, baby, job change, retirement)
- Idle cash / missed savings opportunity
- Product maturity (FD maturing, loan closing)

Your job is to:

1. UNDERSTAND the customer:
   - What's their language preference? (default: English)
   - What channel works best? (push, SMS, WhatsApp, email)
   - What's their current financial context?

2. CRAFT the message:
   - Warm, personal tone — not corporate/robotic
   - Reference their specific situation (don't be generic)
   - Lead with value, not with the sell
   - Keep it short (under 50 words for push/SMS, under 100 for others)
   - Include a clear, low-friction next step

3. DECIDE timing and channel:
   - Evening (6-8 PM) for working professionals
   - Morning (9-11 AM) for business owners
   - Never on weekends unless time-sensitive
   - Push for quick nudges, WhatsApp for conversational, email for detailed

4. EXECUTE the notification

Rules:
- NEVER be pushy or salesy — you're a helpful advisor
- Maximum 2 contacts per customer per week
- If the trigger is about financial stress, be EXTRA careful with tone
- Always frame around the customer's benefit, not the bank's
- Use simple language — avoid jargon
- For Hindi messages, keep natural conversational Hinglish tone
"""


def create_engagement_agent() -> Agent:
    """Create and return the Engagement Agent instance."""
    model = BedrockModel(
        model_id=MODEL_ID,
        region_name=AWS_REGION,
        temperature=0.6,
        max_tokens=1024,
    )

    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            get_customer_profile,
            get_propensity_details,
            get_health_card,
            send_customer_notification,
            send_rm_alert,
            make_call,
        ],
    )


def run_engagement_agent(customer_id: int, trigger_reason: str = "high_propensity") -> dict:
    """Run the Engagement Agent for a customer with a specific trigger."""
    from .schemas import EngagementAgentOutput

    agent = create_engagement_agent()

    prompt = f"""Customer {customer_id} has been flagged for proactive engagement.
Trigger reason: {trigger_reason}

Fetch their profile to understand their context. Then:
- Craft a personalized notification message
- Choose the right channel and timing
- Recommend the outreach actions

Use the tools to gather data, then provide your structured response."""

    result = agent(prompt, structured_output_model=EngagementAgentOutput)

    output: EngagementAgentOutput = result.structured_output
    return {
        "agent": "engagement_agent",
        "customer_id": customer_id,
        "trigger": trigger_reason,
        "structured_output": output.model_dump(),
    }
