"""
agents/tools.py — Shared tools that agents use to fetch data from the ML scoring API.

Decorated with @tool from Strands for agent integration.
"""

import httpx
from strands import tool

from .config import API_BASE


@tool
def get_customer_profile(customer_id: int) -> dict:
    """Fetch full customer profile including all ML scores, income, surplus, loan status.

    Args:
        customer_id: The account ID of the customer to look up.
    """
    resp = httpx.get(f"{API_BASE}/api/customers/{customer_id}", timeout=10)
    resp.raise_for_status()
    return resp.json()


@tool
def get_propensity_details(customer_id: int) -> dict:
    """Fetch propensity score with SHAP explanation and predicted loan product.

    Args:
        customer_id: The account ID of the customer.
    """
    resp = httpx.get(f"{API_BASE}/api/customers/{customer_id}/propensity", timeout=10)
    resp.raise_for_status()
    return resp.json()


@tool
def get_health_card(customer_id: int) -> dict:
    """Fetch 6-dimension financial health card with scores and SHAP factors per dimension.

    Args:
        customer_id: The account ID of the customer.
    """
    resp = httpx.get(f"{API_BASE}/api/customers/{customer_id}/health", timeout=10)
    resp.raise_for_status()
    return resp.json()


@tool
def get_default_risk(customer_id: int) -> dict:
    """Fetch default probability percentage, stress level, and top SHAP risk factors.

    Args:
        customer_id: The account ID of the customer.
    """
    resp = httpx.get(f"{API_BASE}/api/customers/{customer_id}/default", timeout=10)
    resp.raise_for_status()
    return resp.json()


@tool
def send_rm_alert(customer_id: int, rm_name: str, urgency: str, message: str) -> dict:
    """Send an alert notification to a Relationship Manager about a customer requiring attention.

    Args:
        customer_id: The account ID of the customer.
        rm_name: Name of the assigned Relationship Manager.
        urgency: Urgency level — one of 'low', 'medium', 'high', 'critical'.
        message: The alert message content for the RM.
    """
    return {
        "status": "sent",
        "channel": "rm_dashboard",
        "to": rm_name,
        "customer_id": customer_id,
        "urgency": urgency,
        "message": message,
    }


@tool
def send_customer_notification(customer_id: int, channel: str, language: str, message: str) -> dict:
    """Send a notification message to a customer via their preferred communication channel.

    Args:
        customer_id: The account ID of the customer.
        channel: Delivery channel — 'push', 'sms', 'whatsapp', 'email', or 'in_app'.
        language: Message language code — 'en', 'hi', 'ta', 'te', 'bn', etc.
        message: The notification content to send.
    """
    return {
        "status": "sent",
        "channel": channel,
        "language": language,
        "customer_id": customer_id,
        "message": message,
    }


@tool
def generate_loan_offer(customer_id: int, product: str, amount: int, rate: float, tenure_months: int) -> dict:
    """Generate a pre-approved loan offer document for a qualified customer.

    Args:
        customer_id: The account ID of the customer.
        product: Loan product type — 'Auto Loan', 'Home Loan', or 'Personal Loan'.
        amount: Loan amount in INR.
        rate: Annual interest rate as a percentage (e.g. 8.5).
        tenure_months: Loan repayment tenure in months.
    """
    monthly_rate = rate / 1200
    emi = round(amount * monthly_rate * ((1 + monthly_rate) ** tenure_months) /
                (((1 + monthly_rate) ** tenure_months) - 1))
    return {
        "status": "generated",
        "customer_id": customer_id,
        "product": product,
        "amount": amount,
        "rate": rate,
        "tenure_months": tenure_months,
        "estimated_emi": emi,
    }


@tool
def escalate_to_risk_committee(customer_id: int, pd_score: float, assessment: str) -> dict:
    """Escalate a high-risk loan account to the risk committee for urgent review and decision.

    Args:
        customer_id: The account ID of the customer.
        pd_score: Current default probability as a percentage (0-100).
        assessment: The agent's complete assessment summary explaining why escalation is needed.
    """
    return {
        "status": "escalated",
        "to": "risk_committee",
        "customer_id": customer_id,
        "pd_score": pd_score,
        "assessment": assessment,
    }


@tool
def flag_for_underwriter(customer_id: int, health_score: float, recommendation: str, concerns: str) -> dict:
    """Send a health card assessment to the underwriter queue for a lending decision on NTC/NTB customers.

    Args:
        customer_id: The account ID of the customer.
        health_score: Composite financial health score (0-100).
        recommendation: Lending recommendation — 'Approve', 'Review', or 'Decline'.
        concerns: Specific concerns, flags, or conditions to highlight for the underwriter.
    """
    return {
        "status": "flagged",
        "to": "underwriter_queue",
        "customer_id": customer_id,
        "health_score": health_score,
        "recommendation": recommendation,
        "concerns": concerns,
    }


@tool
def make_call(customer_id: int, rm_name: str, call_purpose: str, call_script: str) -> dict:
    """Initiate a phone call to a customer via the RM's dialer system.

    This logs the call intent and provides the RM with the call script.
    The RM will see the script on their dashboard when the call connects.

    Args:
        customer_id: The account ID of the customer to call.
        rm_name: Name of the Relationship Manager making the call.
        call_purpose: Brief purpose — e.g. 'Pre-approved Auto Loan offer', 'Follow-up on home loan inquiry'.
        call_script: The personalized call script for the RM to use during the conversation.
    """
    return {
        "status": "call_initiated",
        "channel": "phone",
        "customer_id": customer_id,
        "rm_name": rm_name,
        "call_purpose": call_purpose,
        "call_script_loaded": True,
        "message": f"Call queued for customer {customer_id}. Script loaded on RM dashboard for {rm_name}.",
    }
