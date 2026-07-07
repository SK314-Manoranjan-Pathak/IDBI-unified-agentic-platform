# Unified Agentic Intelligence Platform for Banking

## Executive Summary

A multi-agent AI platform built on **Strands Agents SDK** and deployed via **AWS Bedrock AgentCore** that continuously monitors customer transaction behavior and autonomously takes action — identifying loan prospects, scoring financial health, predicting defaults, and proactively engaging customers. One platform solves IDBI Problem Statements 2, 3, 4 and SBI Themes 1, 2, 3 simultaneously.

**Core Thesis:** Every decision in retail/MSME banking — who to lend to, how healthy they are, whether they'll default, when to engage them — is answered by the same underlying signal: **how people actually move money.** We built one platform that reads transaction behavior and acts on it autonomously.

---

## Problem Statements Addressed

### IDBI Innovate 2026
| PS | Problem | Our Solution |
|----|---------|-------------|
| 2 | Low loan conversion due to traditional metrics | Propensity Agent identifies intent + capacity from transactions |
| 3 | NTC/NTB MSMEs lack documents for credit assessment | Health Agent builds multi-dimensional score from alternate data |
| 4 | Default prediction accuracy only 16-22% | Risk Agent monitors behavioral deterioration, 12-month early warning |

### SBI Hackathon (Agentic AI & Emerging Tech)
| Theme | Problem | Our Solution |
|-------|---------|-------------|
| 1 | Identify, qualify, convert via personalized engagement | Prospect + Engagement Agents qualify and convert conversationally |
| 2 | Contextual AI for digital service adoption | Engagement Agent nudges based on behavior + life events |
| 3 | Proactive interaction based on behaviors & life events | Full agent loop: detect → reason → act → learn |


---

## Why One Platform Solves All

The research is unambiguous — the same transaction behavioral data and feature engineering powers all three predictions:

| Model | Question Asked | Same Data? | Same Features? |
|-------|--------------|-----------|---------------|
| Propensity (PS2) | "Will they WANT a loan?" | ✅ | ✅ + intent signals |
| Health Score (PS3) | "Are they financially HEALTHY?" | ✅ | ✅ + external data |
| Default (PS4) | "Will they FAIL to repay?" | ✅ | ✅ + stress signals |
| Engagement (SBI) | "WHEN and HOW to talk to them?" | ✅ | ✅ + life events |

A customer's Health Score is their Default Probability inverted. A healthy customer with intent signals is a high-propensity prospect. A declining health score triggers early warning. **These aren't separate problems — they're different views of the same signal.**

---

## Architecture Overview

### Layer 1: Data Ingestion
Transaction and behavioral data flows in from multiple sources:
- **Core Banking System (CBS)** — salary credits, EMI debits, account balances
- **Account Aggregator (Sahamati)** — cross-bank financial data with consent
- **UPI Transaction History** — merchant payments, P2P transfers, patterns
- **GST Portal** — filing regularity, revenue trends (MSMEs)
- **EPFO** — employee provident fund contributions, employment stability
- **Bureau Data** — existing credit history (where available)
- **Utility Payments** — electricity, gas, telecom consistency

### Layer 2: Feature Engineering (ML Pipeline)
Raw data is transformed into predictive features:
- **Cash Flow Features** — monthly surplus, min balance trend, income volatility
- **Behavioral Features** — spending categories, merchant diversity, payment timing
- **Temporal Patterns** — transaction embeddings via Transformer, sequence anomalies
- **Intent Signals** — specific merchant payments (car dealers, property portals)
- **Stress Indicators** — SIP cancellations, FD pre-closures, cash advance spikes
- **External Signals** — GST filing gaps, EPFO contribution drops, utility defaults

### Layer 3: ML Scoring Service
Three model heads trained on the shared feature set:
- **Propensity Model** (XGBoost + LightGBM) — predicts loan intent + matches product
- **Health Score Model** (Multi-output XGBoost) — 6-dimension financial health
- **Default Prediction Model** (Transformer + XGBoost ensemble) — 12-month PD forecast

### Layer 4: Agentic Layer (Strands + AgentCore)
AI agents that reason about ML signals and take autonomous action:
- **Supervisor Agent** — routes signals, manages priorities, enforces guardrails
- **Prospect Agent** — qualifies leads, matches products, generates offers
- **Health Agent** — builds health cards, identifies creditworthy NTC customers
- **Risk Agent** — monitors default risk, escalates, recommends interventions
- **Engagement Agent** — customer-facing comms, multilingual, channel-aware

### Layer 5: AgentCore Infrastructure
- **AgentCore Runtime** — serverless agent execution, auto-scaling
- **AgentCore Memory** — semantic + episodic + preference memory per customer
- **AgentCore Gateway** — single MCP endpoint connecting all external APIs
- **AgentCore Identity** — credential management per bank deployment
- **AgentCore Policy Engine** — Cedar policies for agent access boundaries


---

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Agent Framework | Strands Agents SDK (Python) | AWS-native, lightweight, tool-calling, multi-agent patterns |
| Agent Deployment | AWS Bedrock AgentCore Runtime | Serverless, session-based, auto-scaling, pay-per-use |
| API Integration | AgentCore Gateway (MCP protocol) | Single endpoint for all bank APIs, semantic tool search |
| Agent Memory | AgentCore Memory | Semantic + episodic memory, customer context persistence |
| Credential Mgmt | AgentCore Identity | Per-bank credential isolation, OAuth + API key vault |
| Access Control | AgentCore Policy Engine (Cedar) | Fine-grained agent permissions per bank/role |
| LLM | AWS Bedrock (Claude Sonnet, ap-south-1) | Mumbai region, RBI compliant, fast reasoning |
| ML Models | SageMaker Endpoints / EC2 (g4dn) | XGBoost + Transformer inference |
| Feature Store | AWS Feature Store / Redis | Low-latency feature serving |
| Event Bus | AWS EventBridge | Real-time trigger routing |
| Database | PostgreSQL (RDS Mumbai) + DynamoDB | Customer profiles, audit logs |
| TTS/Translation | Sarvam AI | 11 Indian languages, India AI Mission |
| Notifications | AWS SNS + SES + custom | SMS, push, email, WhatsApp |
| Frontend | Next.js + Recharts | Internal dashboards |
| Observability | AgentCore Observability + CloudWatch | Tracing, audit, RBI compliance |

---

## Compliance & Governance

### RBI Compliance
- ✅ All data processed and stored in India (AWS Mumbai ap-south-1)
- ✅ Human-in-the-loop — tiered autonomy, high-risk actions need human approval
- ✅ Kill-switch — any agent/model can be deactivated via AgentCore Runtime
- ✅ Model Risk Management Framework — drift monitoring, validation, inventory
- ✅ Explainability — SHAP for ML models, reasoning traces for agent decisions
- ✅ Audit trail — every agent action logged via AgentCore Observability

### SEBI Compliance (for advisory)
- ✅ Risk profiling before any recommendation
- ✅ Suitability checks embedded in agent logic
- ✅ Clear disclaimers in customer communications

### DPDP Act
- ✅ Purpose limitation — data used only for stated purposes
- ✅ Data minimization — agents access only what they need (Policy Engine)
- ✅ Consent management — Account Aggregator enforces user consent

### Data Localization
- ✅ AWS Mumbai region for all compute and storage
- ✅ Sarvam AI — Indian sovereign AI platform
- ✅ No customer data leaves Indian infrastructure


---

## Detailed Agent Design

### Supervisor Agent

**Role:** Central coordinator that receives all ML signals and routes them to appropriate sub-agents.

**System Prompt (summary):**
```
You are the coordinator of a banking intelligence system. You receive 
signals from ML models (propensity scores, health changes, default risk 
spikes, life events). Your job is to:
1. Assess urgency and priority
2. Route to the correct sub-agent
3. Prevent duplicate actions (check Memory)
4. Enforce compliance guardrails
5. Handle conflicts (e.g., don't send loan offer to deteriorating customer)
```

**Tools:**
- `get_ml_signals()` — fetch latest scores/flags from ML service
- `check_recent_actions(customer_id)` — query Memory for recent interactions
- `route_to_agent(agent_name, payload)` — delegate to sub-agent
- `check_guardrails(action_type, customer_id)` — verify policy compliance

**Decision Logic:**
```
IF propensity_score > 70 AND default_risk < 15%:
    → Route to Prospect Agent
IF health_score_delta < -15 in 30 days:
    → Route to Risk Agent
IF life_event_detected:
    → Route to Engagement Agent
IF new_customer AND consent_received:
    → Route to Health Agent
```

---

### Prospect Agent

**Role:** Qualifies leads, matches them to loan products, generates personalized offers, and either auto-sends or routes to RM.

**System Prompt (summary):**
```
You identify and qualify loan prospects. Given a customer's propensity 
score, transaction patterns, and financial profile, you:
1. Validate the intent signal (is it genuine?)
2. Assess repayment capacity (surplus, stability, existing debt)
3. Match to optimal loan product (Personal/Home/Auto/Mortgage)
4. Calculate suitable loan amount and EMI
5. Generate a personalized pre-approved offer
6. Decide channel and timing for outreach
```

**Tools:**
- `get_propensity_details(customer_id)` — score breakdown + intent signals
- `get_financial_profile(customer_id)` — income, expenses, existing debt
- `calculate_loan_eligibility(income, existing_emi, product_type)` — max loan amount
- `generate_offer(customer_id, product, amount, rate)` — create offer document
- `notify_rm(rm_id, customer_id, brief)` — add to RM's action list
- `send_customer_nudge(customer_id, message, channel, language)` — direct outreach

**Autonomy Tiers:**
- Tier 1 (Auto): Add to RM call list with context
- Tier 1 (Auto): Send informational nudge to customer
- Tier 2 (Act + Notify): Send pre-approved offer
- Tier 3 (Recommend): Approve loan disbursement (always human)

---

### Health Agent

**Role:** Computes multi-dimensional financial health cards for NTC/NTB customers using alternate data, enabling credit decisions without traditional documents.

**System Prompt (summary):**
```
You assess the financial health of customers who lack traditional credit 
history. Using Account Aggregator data, UPI patterns, GST filings, and 
EPFO contributions, you:
1. Compute scores across 6 dimensions
2. Identify strengths and risks
3. Compare against peer benchmarks
4. Generate a visual Health Card
5. Provide an overall creditworthiness assessment
6. Flag specific concerns for underwriters
```

**6 Health Dimensions:**
1. **Income Stability** — regularity, growth, diversification
2. **Spending Discipline** — discretionary ratio, consistency, no splurges
3. **Cash Flow Adequacy** — surplus maintenance, min balance, no overdrafts
4. **Debt Management** — EMI-to-income ratio, on-time payments, no bounces
5. **Growth Trajectory** — savings rate trend, investment growth, income trajectory
6. **External Compliance** — GST filing on time, EPFO regular, utility payments current

**Tools:**
- `pull_aa_data(customer_id, consent_handle)` — Account Aggregator data fetch
- `get_gst_summary(gstin)` — GST filing regularity and revenue
- `get_epfo_data(uan)` — Employment and contribution history
- `compute_health_score(features)` — ML model inference
- `get_peer_benchmark(segment, region)` — comparative data
- `generate_health_card(customer_id, scores)` — visual output
- `flag_underwriter(customer_id, concerns, recommendation)` — escalate

---

### Risk Agent

**Role:** Continuously monitors existing loan portfolio for behavioral deterioration. Detects stress 12 months before default and triggers interventions.

**System Prompt (summary):**
```
You monitor the loan portfolio for early signs of financial stress. 
When a customer's default probability increases, you:
1. Analyze what changed (which behaviors shifted?)
2. Assess severity and trajectory
3. Classify root cause (job loss, medical, temporary gap, systemic)
4. Recommend intervention (call, restructure, moratorium, recall)
5. Determine urgency and escalation path
6. Track if intervention was effective
```

**Stress Signal Hierarchy:**
```
Level 1 (Watch): SIP reduced, savings rate dropping
Level 2 (Alert): EMI delayed, FD pre-closed, credit card maxing
Level 3 (Action): EMI bounced, salary credit missed, cash advances
Level 4 (Escalate): Multiple bounces, legal notices, account dormant
```

**Tools:**
- `get_default_probability(customer_id)` — current PD + trend
- `get_stress_timeline(customer_id)` — chronological behavioral changes
- `get_shap_explanation(customer_id)` — why PD increased
- `alert_rm(rm_id, customer_id, urgency, brief)` — RM notification
- `recommend_restructure(customer_id, options)` — propose EMI changes
- `escalate_risk_committee(customer_id, assessment)` — high-severity escalation
- `send_courtesy_message(customer_id, message)` — gentle customer outreach

---

### Engagement Agent

**Role:** Customer-facing agent that crafts personalized, multilingual communications and manages proactive engagement based on detected life events and behavioral triggers.

**System Prompt (summary):**
```
You craft and deliver personalized customer communications for IDBI Bank. 
You are warm, helpful, and never pushy. You:
1. Generate messages in the customer's preferred language
2. Choose the right channel (push/SMS/WhatsApp/email/in-app)
3. Time messages appropriately (not too early, not too late)
4. Respect frequency limits (no spam)
5. Track responses and outcomes
6. Hand off to human RM when customer wants deeper conversation
```

**Tools:**
- `get_customer_preferences(customer_id)` — language, channel, timing
- `check_contact_history(customer_id)` — recent messages, responses
- `generate_message(template, params, language)` — LLM + Sarvam translation
- `send_notification(customer_id, message, channel)` — deliver message
- `schedule_followup(customer_id, days, context)` — future reminder
- `log_interaction(customer_id, type, content, outcome)` — audit + memory
- `handoff_to_rm(customer_id, context)` — escalate to human

**Life Event Triggers:**
| Event Detected | Action | Products to Suggest |
|---------------|--------|-------------------|
| Marriage signals (venue, jeweler, catering) | Congratulate + offer | Personal loan, gold loan, term insurance |
| New baby (hospital, baby products) | Gentle nudge after 2 weeks | Child plan, term insurance upgrade, health insurance |
| Job change (salary source changed) | Welcome + salary account | Salary account switch, credit card upgrade |
| Retirement (pension credits starting) | Proactive planning | FD ladder, senior citizen savings, health insurance |
| Home purchase (stamp duty, registration) | Assist | Home loan top-up, home insurance, renovation loan |
| Business growth (GST revenue up) | Congratulate + offer | Working capital, business loan, overdraft |


---

## AgentCore Memory Design

Memory is what separates a stateless scoring engine from a truly intelligent agent system. Each customer has persistent memory that agents read and write to.

### Memory Strategies

**1. Semantic Memory (Long-term knowledge)**
- Customer financial profile summary
- Key life events detected
- Product holdings and preferences
- Risk assessment history
- Example: "Ramesh is a 34-year-old IT professional, moderate risk appetite, goal: retirement by 2045, has no auto loan, monthly surplus ₹42K"

**2. Episodic Memory (Interaction history)**
- Every agent action taken for this customer
- Customer responses to nudges/offers
- RM conversation summaries
- Example: "2026-06-15: Sent auto loan nudge via push. Customer opened but didn't respond. 2026-06-20: RM called, customer said 'maybe next month.'"

**3. User Preference Memory (Communication style)**
- Preferred language (Hindi/English/Tamil/etc.)
- Preferred channel (WhatsApp/SMS/push/email)
- Preferred timing (morning/evening/weekday only)
- Contact frequency tolerance
- Example: "Prefers Hindi, WhatsApp, evening messages. Max 2 contacts per week."

### How Memory Prevents Bad Behavior

```
Scenario: ML flags customer as high-propensity for personal loan

Agent checks Memory:
- Episodic: "Offered personal loan 2 weeks ago. Customer said 'not interested.'"
- Action: SKIP. Don't re-offer. Wait 90 days.

Scenario: ML flags customer for early warning

Agent checks Memory:
- Episodic: "RM called yesterday about same concern. Customer explained job change."
- Action: SKIP. Already addressed. Monitor only.

Scenario: Engagement Agent wants to send evening notification

Agent checks Memory:
- Preference: "DND after 9 PM"
- Current time: 9:30 PM
- Action: SCHEDULE for tomorrow 6 PM instead.
```

---

## User Stories & Detailed Scenarios

### Scenario 1: End-to-End Prospect Identification & Conversion

**Context:** Ramesh Kumar, IDBI savings account holder, salaried IT professional.

**Step 1 — ML Detection (Background)**
```
Transaction data from last 14 days:
- ₹2,000 UPI to "Maruti Suzuki Arena, Whitefield" (test drive booking)
- ₹500 UPI to "PolicyBazaar" (insurance comparison)
- ₹1,500 UPI to "CarDekho Premium" (car comparison subscription)
- Regular salary: ₹1,50,000/month (consistent 18 months)
- Monthly surplus after all expenses: ₹42,000
- No existing auto loan
- Existing EMIs: ₹15,000 (personal loan, 8 months remaining)

ML Propensity Model Output:
- Propensity Score: 87/100
- Predicted Product: Auto Loan
- Confidence: High (multiple corroborating signals)
- Timing Readiness: Immediate (active shopping behavior)
- Repayment Capacity: ₹25,000 EMI supportable
```

**Step 2 — Supervisor Agent Receives Signal**
```
Signal: {customer: "RAMESH_001", type: "propensity_spike", 
         score: 87, product: "auto_loan", urgency: "high"}

Supervisor checks:
- Memory: No recent offers sent. Last interaction 45 days ago (FD maturity reminder).
- Default Risk: 3% (very low)
- Health Score: 82 (healthy)
- Guardrails: No compliance blocks

Decision: Route to Prospect Agent with full context.
```

**Step 3 — Prospect Agent Qualifies**
```
Prospect Agent reasoning:
1. Intent validation: 3 independent auto-related merchants in 14 days = GENUINE
2. Capacity: Surplus ₹42K - existing EMI headroom consideration
   - Current EMI: ₹15K (personal loan, ends in 8 months)
   - Post personal loan closure: ₹57K available
   - Recommended auto EMI: ₹18-22K (comfortable)
3. Product match: Auto Loan
4. Loan sizing: ₹8-12L (based on car segment signals — Maruti Arena = ₹8-15L range)
5. Rate: 8.5% (salaried, good profile)

Decision: Generate pre-approved offer. Send via Engagement Agent.
Also add to RM call list for day+2 follow-up.
```

**Step 4 — Engagement Agent Delivers**
```
Engagement Agent checks:
- Language preference: English (from Memory)
- Channel: Push notification (primary), followed by in-app message
- Timing: Evening (customer typically active 7-9 PM)
- Last contact: 45 days ago (safe to send)

Message generated:
"Hi Ramesh! 🚗 Looking at a new car? We've got something that might help — 
a pre-approved auto loan up to ₹10L at 8.5%. Zero processing fee this month. 
Tap to see your personalized offer."

Actions:
1. Push notification sent at 7:15 PM
2. In-app offer card created with details
3. RM (Priya Sharma) notified: "Ramesh — auto loan prospect, score 87. 
   Call on Jul 6 if no response to push notification."
4. Memory updated: {action: "auto_loan_offer_sent", date: "2026-07-04", 
   channel: "push", awaiting_response: true}
```

**Step 5 — Follow-up Loop**
```
Day+1: Customer opened notification, viewed offer details (tracked)
Day+2: No application started
Day+2: RM Priya calls: "Hi Ramesh, noticed you might be car shopping. 
        We have a pre-approved loan for you — any questions?"
Ramesh: "Actually yes, what's the max tenure?"
RM: Discusses details, Ramesh starts application.
Day+5: Loan sanctioned.

Outcome logged → Propensity model learns → Accuracy improves.
Conversion achieved in 5 days.
```

---

### Scenario 2: MSME Health Card for New-to-Credit Business

**Context:** Priya Textiles, a small textile shop in Surat. Owner: Priya Patel. No CIBIL history, no ITR, no formal balance sheet. Applying for ₹10L working capital loan.

**Step 1 — Trigger**
```
Priya visits IDBI branch, fills loan application.
Branch officer initiates Health Card assessment.
System sends consent request via Account Aggregator.
Priya approves on her phone (Sahamati consent flow).
```

**Step 2 — Health Agent Activates**
```
Health Agent receives: {customer: "PRIYA_TEX_001", type: "new_assessment",
                        consent_handle: "AA_CONSENT_xyz", loan_requested: 1000000}

Agent actions:
1. Pull AA data: 12 months bank statements from 2 accounts
2. Pull GST data: 12 months filing history (GSTIN linked)
3. Pull EPFO data: 5 employees contributing
4. Pull utility data: Electricity bills (commercial connection)
```

**Step 3 — Feature Extraction & Scoring**
```
From AA (bank statements):
- Average monthly credits: ₹4,80,000
- Average monthly debits: ₹3,90,000
- Average monthly surplus: ₹90,000
- Min balance maintained: ₹45,000 (never zero)
- Income volatility: Moderate (seasonal — dips in June-July)
- No bounced cheques
- No cash advance behavior

From GST:
- Filed on time: 11 out of 12 months (missed August — monsoon season)
- Revenue trend: +18% YoY
- B2B vs B2C ratio: 60:40

From EPFO:
- 5 employees, consistent contributions 12 months
- No employee exits in 6 months (stable workforce)

From Utility:
- Commercial electricity: ₹15K-25K/month (correlates with revenue)
- Never defaulted on utility payment

Health Score Generated:
┌────────────────────────────────────────────────┐
│  PRIYA TEXTILES — Financial Health Score: 74/100│
│                                                │
│  Income Stability:      ████████░░  78/100     │
│  Spending Discipline:   ███████░░░  68/100     │
│  Cash Flow Adequacy:    ████████░░  82/100     │
│  Debt Management:       █████████░  92/100     │
│  Growth Trajectory:     ██████░░░░  65/100     │
│  External Compliance:   ███████░░░  72/100     │
│                                                │
│  ⚠️ Flag: Revenue seasonal (dips Jun-Jul)      │
│  ⚠️ Flag: Growth trajectory moderate           │
│  ✓ Strength: Zero bounced payments             │
│  ✓ Strength: GST filed consistently            │
│  ✓ Strength: Stable workforce (EPFO)           │
│                                                │
│  Peer Rank: Top 35% of textile MSMEs, Surat   │
│  Recommended: Approve ₹8L (reduced for season) │
│  Structure: Lower EMI in Jun-Jul (₹12K vs ₹18K)│
└────────────────────────────────────────────────┘
```

**Step 4 — Agent Recommendation**
```
Health Agent decision:
- Overall score 74 > threshold 60 (approvable)
- Concern: Seasonality — recommend structured EMI
- Capacity: Surplus ₹90K supports ₹18K EMI easily
- Recommendation: Approve ₹8L (not full ₹10L due to moderate growth score)
- EMI structure: ₹18K normal months, ₹12K lean months (Jun-Jul)

Action: Send Health Card + recommendation to Underwriter (Tier 3 — human decides)
```

**Step 5 — Underwriter Reviews**
```
Underwriter sees:
- Full Health Card with 6 dimensions
- Peer comparison (top 35%)
- Specific concerns flagged
- Agent's recommendation with reasoning
- Raw data available for drill-down

Decision: Approve ₹8L, structured EMI as suggested.
Priya gets working capital without a single traditional document.
```

---

### Scenario 3: Early Warning — Preventing NPA

**Context:** Suresh Verma, personal loan of ₹5L, EMI ₹12,500/month, 18 months remaining. Has been a good borrower for 30 months.

**Step 1 — ML Detection (Gradual)**
```
Default Prediction Model tracks Suresh daily:

Day 0 (45 days ago): PD = 6% (healthy)
Day 15: PD = 9% — SIP of ₹5K cancelled (Level 1: Watch)
Day 30: PD = 18% — FD of ₹2L pre-closed (Level 2: Alert)
Day 37: PD = 26% — Salary credit delayed by 12 days
Day 40: PD = 31% — 3 cash advances on credit card in 5 days
Day 42: PD = 38% — Minimum balance breached twice

Signal fires at Day 30 (PD crossed 15% threshold): Alert
Signal fires again at Day 40 (PD crossed 30%): Action Required
```

**Step 2 — Risk Agent Activated**
```
Risk Agent receives: {customer: "SURESH_001", type: "pd_spike",
                      current_pd: 38%, previous_pd: 6%, 
                      trend: "rapid_deterioration", days: 42}

Agent pulls context:
- SHAP explanation: Top drivers are salary_delay (35%), 
  fd_preclosure (25%), cash_advance_spike (20%), sip_cancel (12%)
- Pattern match: Resembles "job transition" pattern (not systematic default)
- Memory: No recent contact. Last interaction 4 months ago (EMI reminder).
- Loan details: ₹3.8L outstanding, EMI ₹12,500, next EMI due in 5 days
```

**Step 3 — Risk Agent Reasons**
```
Agent analysis:
1. Root cause assessment: LIKELY job change/transition
   - Salary delayed (not stopped) — suggests transition, not termination
   - FD closure = building liquidity buffer
   - Cash advances = bridging short-term gap
   - NOT a systematic defaulter pattern (no lifestyle inflation, no new debt)
   
2. Severity: HIGH but likely TEMPORARY
   
3. Urgency: CRITICAL — EMI due in 5 days, high bounce risk
   
4. Recommended action:
   - Immediate: RM call (not SMS — this needs human touch)
   - Offer: 1-2 month EMI moratorium or restructure
   - Objective: Prevent bounce, preserve NPA clock
```

**Step 4 — Dual Action**
```
Risk Agent executes:

Action 1 (Tier 1 — Auto):
- Alert RM (Ajay Kumar): "URGENT: Suresh Verma — PD spiked to 38%. 
  Likely job transition. EMI due in 5 days — high bounce risk. 
  Call TODAY. Suggest 2-month moratorium. Context attached."
  
Action 2 (Tier 1 — Auto):
- Gentle customer message (via Engagement Agent):
  "Hi Suresh, we noticed some changes in your account. If you need 
  any flexibility with your upcoming EMI, we're here to help. 
  Your RM Ajay will reach out shortly."
  
Action 3 (Tier 2 — Act + Notify):
- Flag to risk team weekly report: "Suresh_001 added to watchlist. 
  Intervention initiated. Monitor for 30 days."

Memory updated: {event: "ews_triggered", pd: 38%, cause: "job_transition_likely",
                  rm_alerted: true, customer_contacted: true, 
                  intervention: "moratorium_offered"}
```

**Step 5 — Resolution**
```
Day 43: RM Ajay calls Suresh.
Suresh: "Haan sir, actually I changed companies. Gap between salaries. 
         New salary will come from 15th next month."
Ajay: "No problem. Let me give you a 2-month pause on EMI. 
       Resume from September with normal schedule."
       
Day 44: Moratorium approved (Tier 3 — human decision, agent prepared paperwork)
Day 60: New salary starts flowing. Higher than before (+20%).
Day 75: PD drops back to 8%.

Account saved. No NPA. No bounce. Customer loyalty strengthened.
ML model learns: "salary_delay + fd_closure + cash_advance in this 
pattern = temporary, not structural"
```

---

### Scenario 4: Proactive Life Event Engagement (SBI Theme 3)

**Context:** Meera Sharma, 29, savings account holder. Not currently a borrower.

**Step 1 — Life Event Detection**
```
Transaction patterns over last 30 days:
- ₹50,000 UPI to "Taj Palace Banquets" (venue booking)
- ₹25,000 UPI to "Tanishq Jewellers" × 3 occasions
- ₹15,000 UPI to "Bombay Catering Services"
- ₹8,000 UPI to "MakeMyTrip" (honeymoon?)
- ₹12,000 UPI to "Meena Bazaar" (shopping spike)

Life Event Model Output:
- Event: MARRIAGE (confidence: 94%)
- Estimated timeline: 4-6 weeks from now
- Spending trajectory: Increasing
```

**Step 2 — Supervisor Routes to Engagement Agent**
```
Supervisor checks:
- Memory: No life event engagement before. Customer acquired 2 years ago.
- Health Score: 71 (healthy, moderate savings)
- Products held: Savings account only. No loan, no insurance, no investments.
- Opportunity: High (multiple relevant products for marriage life stage)

Routes to: Engagement Agent
Context: "Marriage detected. Customer has only savings account. 
          Multiple product opportunities. Be warm, not sales-y."
```

**Step 3 — Engagement Agent Plans & Executes**
```
Engagement Agent reasoning:
1. Timing: Wait 5 days (don't seem like you're watching)
2. Tone: Congratulatory, helpful, not pushy
3. Channel: In-app notification (least intrusive for first contact)
4. Language: English (from preference memory)
5. Products to suggest (ordered by relevance):
   - Term insurance (life stage trigger — spouse protection)
   - Joint savings account
   - Personal loan (if wedding expenses exceed savings)
   - Recurring deposit (post-wedding savings habit)

Message crafted:
"Congratulations Meera! 🎉 A new chapter deserves a fresh financial plan. 
Many couples find this a great time to:
• Start a joint savings goal together
• Get covered with term insurance (it's cheapest at your age!)
• Set up a post-wedding savings plan

Want a quick financial health check? It takes 2 minutes."

Sent via: In-app card (7 PM, Thursday — her typical active time)
Follow-up scheduled: If no response in 5 days, gentle SMS reminder
```

**Step 4 — Customer Engages**
```
Day+2: Meera taps "Financial health check"
System: Quick 5-question assessment (conversational, not form-like)
Result: Recommended products ranked by priority

Day+3: Meera explores term insurance option
Day+5: Meera purchases ₹1Cr term plan via app

Outcome: Cross-sell achieved. Zero RM involvement. Fully autonomous.
Memory: {event: "marriage_engagement_successful", product_sold: "term_insurance",
         customer_response: "positive", time_to_conversion: "5_days"}
```

---

### Scenario 5: Portfolio-Level Risk Monitoring (CRO View)

**Context:** Chief Risk Officer wants to understand portfolio health trends.

**Step 1 — Daily Batch Processing**
```
Every night at 2 AM:
- ML pipeline re-scores all 45,000 active loans
- Aggregates by segment, region, product type
- Compares with previous day/week/month
- Identifies systemic trends vs individual cases
```

**Step 2 — Risk Agent Generates Portfolio Report**
```
Portfolio Summary (July 4, 2026):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Active Loans: 45,000
Total Exposure: ₹12,400 Cr

Risk Distribution:
  Green  (PD < 10%):  38,200 (84.9%) — ₹10,200 Cr
  Amber  (PD 10-30%):  5,100 (11.3%) — ₹1,680 Cr
  Red    (PD > 30%):   1,700 (3.8%)  — ₹520 Cr

Month-over-Month Changes:
  Green → Amber migrations: 340 accounts (+12% vs last month) ⚠️
  Amber → Red migrations: 89 accounts (flat)
  Amber → Green recoveries: 210 accounts (interventions working ✓)

Segment Analysis:
  Personal Loans (IT sector): Risk INCREASING
    - Cause: Layoff news in 3 major IT companies
    - 45 accounts showing salary delay patterns
    - Recommendation: Tighten underwriting for IT unsecured
    
  Home Loans: STABLE
    - No systemic concern
    - 12 accounts flagged for individual review
    
  MSME (Textile, Surat): IMPROVING
    - GST collections up 15% QoQ
    - 8 accounts moved from Amber → Green
    
  Auto Loans: SLIGHT UPTICK
    - Fuel cost impact on EMI stress
    - 23 accounts showing early stress signals
    - Recommendation: Monitor, no action yet
```

**Step 3 — Automated Actions**
```
Risk Agent (autonomous — Tier 1):
- Sent daily portfolio digest to CRO
- Flagged 45 IT sector accounts to respective RMs
- Generated individual intervention plans for 89 Red accounts
- Updated risk dashboard with real-time data

Risk Agent (recommendation — Tier 3):
- Proposed to CRO: "Reduce unsecured lending exposure to IT sector 
  by 15% this quarter. Shift to secured products."
- CRO reviews in morning standup, approves with modification.
```


---

## ML Pipeline — Data Requirements

### Transaction Data (Primary Source)

| Data Field | Type | Source | Used For |
|-----------|------|--------|----------|
| Transaction amount | Numeric | CBS/AA | All models |
| Transaction timestamp | DateTime | CBS/AA | Temporal patterns |
| Merchant name/category | Categorical | UPI/CBS | Intent signals, spending behavior |
| Transaction type (credit/debit) | Binary | CBS/AA | Cash flow computation |
| Payment mode (UPI/NEFT/cash/card) | Categorical | CBS | Behavioral profiling |
| Balance after transaction | Numeric | CBS/AA | Min balance, volatility |
| Counter-party (where money goes/comes from) | Text | UPI/CBS | Merchant identification |
| Transaction narration | Text | CBS | NLP-based categorization |
| Recurring flag (EMI, SIP, salary) | Derived | Feature eng. | Income/obligation identification |
| Geolocation (where transaction happened) | Geo | UPI | Mobility patterns (PLOS ONE approach) |

### Derived Features (Feature Engineering)

**Cash Flow Features (Monthly Aggregates)**
| Feature | Computation | Predictive For |
|---------|------------|----------------|
| monthly_surplus | total_credits - total_debits | Capacity (all models) |
| surplus_volatility | std_dev(monthly_surplus, 12mo) | Stability (health, default) |
| min_balance_trend | slope(min_daily_balance, 6mo) | Stress detection (default) |
| income_regularity | coefficient_of_variation(salary_credits) | Income stability (health) |
| income_growth_rate | (recent_3mo_avg / prev_3mo_avg) - 1 | Growth trajectory |
| expense_to_income_ratio | total_debits / total_credits | Discipline (health) |
| discretionary_spend_ratio | discretionary / total_spend | Spending behavior |

**Behavioral Features**
| Feature | Computation | Predictive For |
|---------|------------|----------------|
| merchant_diversity_index | unique_merchants / total_transactions | Financial activity level |
| payment_timing_score | avg(days_before_due_date) for bills | Discipline |
| bounce_rate | bounced_transactions / attempted | Default risk |
| upi_adoption_score | upi_txns / total_txns | Digital behavior |
| savings_rate_trend | slope(savings_balance, 12mo) | Financial health |
| new_merchant_velocity | new_merchants_per_month | Lifestyle changes |
| weekend_spend_ratio | weekend_spend / total_spend | Behavioral profiling |

**Intent Signal Features (Propensity-Specific)**
| Feature | How Detected | Maps To |
|---------|-------------|---------|
| auto_dealer_payments | Merchant category = "Auto Dealer" | Auto Loan |
| property_portal_payments | MagicBricks, 99acres, Housing.com | Home Loan |
| education_portal_payments | School fees increase, EdTech subs | Education Loan |
| wedding_vendor_payments | Venue, catering, jeweler cluster | Personal Loan |
| insurance_comparison | PolicyBazaar, Coverfox payments | Insurance cross-sell |
| investment_platform | Zerodha, Groww, MF portals | Wealth advisory |
| travel_spike | MakeMyTrip, IRCTC, airlines cluster | Personal Loan |

**Stress Indicator Features (Default-Specific)**
| Feature | Signal | Severity |
|---------|--------|----------|
| sip_cancellation | SIP debit stops appearing | Level 1 |
| fd_premature_closure | FD broken before maturity | Level 2 |
| savings_withdrawal_spike | Large savings → current transfers | Level 2 |
| cash_advance_count | Credit card cash withdrawals | Level 3 |
| emi_delay_days | Days past due date for each EMI | Level 3 |
| salary_delay | Days past expected salary date | Level 3 |
| new_debt_acquisition | New EMI payments appearing | Level 2 |
| utility_default | Missed electricity/telecom payment | Level 2 |
| minimum_balance_breach | Balance < minimum required | Level 2 |
| overdraft_utilization | OD used / OD limit | Level 3 |

**External Data Features (Health Score — NTC/NTB Specific)**
| Data Source | Features Extracted | Why |
|------------|-------------------|-----|
| GST Portal | filing_regularity, revenue_trend, b2b_ratio, tax_compliance | Business health for MSMEs |
| EPFO | contribution_regularity, employee_count_trend, employer_stability | Employment & workforce stability |
| Utility Bills | payment_consistency, consumption_trend, commercial_vs_residential | Activity level proxy |
| Account Aggregator | cross_bank_balances, total_obligations, inflow_sources | Complete financial picture |
| Bureau (if available) | existing_score, inquiry_count, vintage | Traditional credit signal |

### Training Data Requirements

| Model | Training Labels | Source | Min Records |
|-------|----------------|--------|-------------|
| Propensity | did_take_loan (0/1) within 90 days | Historical CBS data | 50K+ customers |
| Health Score | manually_rated_health (1-100) OR proxy: did_default within 12mo | Expert labels or outcome-based | 10K+ MSMEs |
| Default | did_default_12mo (0/1) | Historical NPA data | 100K+ loans (with 5%+ default rate) |
| Life Event | event_type (marriage/baby/job_change/etc.) | Labeled transaction sequences | 5K+ per event type |

### Synthetic Data Strategy (for PoC)

Since we won't have real bank data for the hackathon, we'll generate realistic synthetic data:

1. **Transaction Generator** — Python script that creates realistic transaction sequences
   - Salaried profiles: Regular salary, EMIs, SIPs, groceries, utilities, discretionary
   - MSME profiles: Irregular revenue, seasonal patterns, vendor payments, GST timing
   - Embed intent signals: Inject car dealer payments for some customers
   - Embed stress signals: Inject salary delays, SIP stops for some customers

2. **Profile Diversity** — 500 synthetic customers across:
   - 200 salaried (various income levels)
   - 150 MSMEs (various sectors)
   - 100 NTC/NTB (limited history)
   - 50 deliberately stressed/deteriorating

3. **Outcome Labels** — Manually assigned based on embedded signals
   - 30% labeled as high-propensity (intent signals present)
   - 20% labeled as low-health (stress signals present)
   - 10% labeled as likely-to-default (severe stress)

---

## Research Papers & Academic Foundation

### Core Papers (Validate Our Approach)

**1. Customer Mobility Signatures & Financial Indicators for Product Prediction**
- Source: PLOS ONE, 2018
- Link: http://journals.plos.org/plosone/article?id=10.1371/journal.pone.0201197
- Key Result: AUC = 0.942 using transaction + mobility features
- Relevance: Proves transaction behavioral data predicts loan purchase intent with >94% accuracy

**2. Modeling Financial Habits with Transformers (2025)**
- Source: arXiv
- Link: https://arxiv.org/html/2507.23267v1
- Key Result: Transformer on raw transaction sequences outperforms hand-crafted features
- Relevance: Architecture for our transaction embedding layer

**3. Cash Flow Underwriting with Bank Transaction Data (2025)**
- Source: arXiv
- Link: https://arxiv.org/html/2510.16066v1
- Key Result: Transaction features boost credit scoring for new-to-lending MSMEs
- Relevance: Directly validates Health Score approach for NTC customers

**4. ML for Credit Scoring Using Behavioral & Transactional Data (2025)**
- Source: WJARR
- Link: https://wjarr.com/content/machine-learning-credit-scoring-and-loan-default-prediction-using-behavioral-and
- Key Result: Spending patterns + payment timing predict default better than static scores
- Relevance: Core for Default Prediction model features

**5. Checking Account Activity & Credit Default Risk (2017)**
- Source: arXiv
- Link: https://ar5iv.labs.arxiv.org/html/1707.00757
- Key Result: Transaction data OUTPERFORMS financial ratios for default prediction
- Relevance: Foundational validation — transactions > documents

**6. Bill Payment Habits + Explainable AI for Credit Risk (2025)**
- Source: MDPI Applied Sciences
- Link: https://www.mdpi.com/2076-3417/15/10/5723
- Key Result: Payment habits + SHAP provides accurate AND explainable credit risk
- Relevance: Methodology for Health Score + RBI-compliant explainability

**7. Universal Representations for Financial Transactional Data (2024)**
- Source: arXiv
- Link: https://arxiv.org/abs/2404.02047
- Key Result: One embedding model → multiple downstream tasks
- Relevance: Validates our "shared feature layer, multiple prediction heads" architecture

**8. Detecting Financial Vulnerability via Open Banking Data (2023)**
- Source: arXiv
- Link: https://arxiv.org/abs/2306.01749
- Key Result: Hidden Markov Models detect state transitions (healthy → stressed)
- Relevance: State-transition detection for Early Warning system

**9. Enhancing Credit Scoring with Alternative Data (2024)**
- Source: PLOS ONE / PMC
- Link: https://pmc.ncbi.nlm.nih.gov/articles/PMC11108212/
- Key Result: Alternative data significantly improves NTC credit scoring
- Relevance: Validates GST/EPFO/utility data usage for Health Score

**10. Next-Product-to-Buy Models for Cross-Selling (Journal of Interactive Marketing)**
- Source: ResearchGate
- Link: https://www.researchgate.net/publication/227704541_Next-product-to-buy_models_for_cross-selling_applications
- Key Result: Predicting next product reduces waste in targeting
- Relevance: Product matching logic in Prospect Agent

---

## Business Model

### Phase 1: Hackathon Win → Pilot with IDBI/SBI
- Demonstrate working PoC
- Win pilot deployment opportunity
- Deploy within bank's AWS environment

### Phase 2: Productize → Multi-Bank SaaS
- Same agent code, different Gateway targets per bank
- Per-bank AgentCore deployment (data isolation)
- Pricing: Per customer assessed per month (₹5-15/customer/month)
- Target: 40+ public/private banks, 200+ NBFCs

### Phase 3: Platform → India Stack Native Financial Intelligence
- Integrate with OCEN (Open Credit Enablement Network)
- Integrate with ULI (Unified Lending Interface)
- Become the "intelligence layer" between India Stack rails and bank decisions
- API marketplace: Other fintechs consume our scores

### Revenue Model
| Tier | What | Price |
|------|------|-------|
| Scoring API | Propensity + Health + Default per customer | ₹10/assessment |
| Agent Platform | Full autonomous agent system | ₹50K-2L/month per bank |
| Enterprise | Custom deployment + training + support | ₹20L+/year |

### Competitive Moat
- Research-backed (not vibes-based scoring)
- India Stack native (AA, ULI, OCEN integration)
- RBI compliant from day one (AgentCore + Mumbai region)
- Agentic (acts, doesn't just score) — 10x value over dashboards
- Multi-lingual engagement (Sarvam integration)
- Memory-driven (learns from every interaction, improves over time)

---

## Sprint Plan

| Day | Focus | Deliverable |
|-----|-------|-------------|
| Day 1 | Synthetic data generation + feature engineering code | 500 customer profiles with transactions |
| Day 2 | Train ML models (XGBoost: propensity, health, default) | 3 working models + SHAP |
| Day 3 | Strands agents: Supervisor + Prospect + Health + Risk | Agent code with tools |
| Day 4 | AgentCore deployment: Runtime + Gateway + Memory | Agents running on AgentCore |
| Day 5 | Frontend dashboard (3 views) + end-to-end demo flow | Working demo |
| Day 6 | Deck prep, polish, deploy, record demo video | Submission-ready |
| Jul 9 | Submit IDBI | |
| Post Jul 9 | Add Engagement Agent + conversational layer for SBI | SBI submission |
