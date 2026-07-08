# Demo Customers — IDBI Unified Agentic Platform

Three curated customer stories demonstrating the end-to-end pipeline across all three
problem statements.

---

## Demo 1: High-Propensity Prospect (IDBI PS2 / SBI Theme 1)

**Account 2048** — Salaried professional, active auto-loan shopper

| Attribute | Value |
|-----------|-------|
| Account ID | 2048 |
| District | 76 |
| Monthly Income (avg) | ₹54,474 |
| Monthly Surplus | ₹6,432 |
| Balance (latest) | ₹1,41,504 |
| Has Existing Loan | No |
| Default Risk | 0.3% (Healthy) |
| **Propensity Score** | **100 / 100** |
| Predicted Product | **Auto Loan** |
| Confidence | High |

**Why the model flagged this customer (SHAP top factors):**
1. `auto_dealer_txn_count_30d` = 5 transactions (SHAP +5.90) — visited Maruti Suzuki, Hyundai
2. `discretionary_spend_ratio` elevated (SHAP +2.65) — spending pattern shifted
3. `insurance_comparison_flag` = 1 (SHAP +0.49) — visited PolicyBazaar

**Health Card (composite = 71.0):**
- Income Stability: 91.0 ✓
- Spending Discipline: 91.9 ✓
- Cash Flow Adequacy: 41.9 (moderate — surplus is modest)
- Debt Management: 100.0 ✓ (no existing debt)
- Growth Trajectory: 72.2 ✓
- External Compliance: 29.2 (neutral — no MSME signals)

**Agent Recommendation:** `route_to_prospect_agent` | Urgency: HIGH

**Demo Narrative (maps to Scenario 1 in idea.md):**
> The ML pipeline detects 5 auto-dealer UPI payments in the last 30 days — Maruti
> Suzuki Arena, Hyundai Showroom, CarDekho. Combined with a PolicyBazaar payment
> (insurance comparison), stable ₹54K monthly income, zero existing EMIs, and a
> healthy ₹1.4L balance, the Propensity model scores this at 100/100 for Auto Loan.
> The Supervisor Agent routes to the Prospect Agent, which sizes the loan at ₹8-10L
> (based on surplus ₹6,432 supporting ~₹18K EMI) and triggers a personalized push
> notification via the Engagement Agent.

---

## Demo 2: MSME Health Card (IDBI PS3)

**Account 2926** — Small business, no traditional credit history (NTC)

| Attribute | Value |
|-----------|-------|
| Account ID | 2926 |
| District | (from Berka) |
| Monthly Revenue (avg) | ₹1,16,245 |
| Monthly Surplus | ₹69,406 |
| MSME Flag | Yes |
| Health Quality | **Healthy** |
| Default Risk | 0.4% (Healthy) |
| Propensity Score | 0.0 (not shopping for a loan) |
| **Composite Health Score** | **79.7 / 100** |
| Recommendation | **Approve** |

**6-Dimension Health Card:**

| Dimension | Score | Top Driver (SHAP) |
|-----------|-------|-------------------|
| Income Stability | 34.7 | `income_regularity` — irregular but expected for MSME |
| Spending Discipline | 92.3 | `large_txn_frequency` — well-controlled |
| Cash Flow Adequacy | **78.8** | `monthly_surplus_avg` — strong surplus |
| Debt Management | **100.0** | `emi_bounce_count_6m` = 0 — never bounced |
| Growth Trajectory | **100.0** | `income_growth_rate` — revenue growing |
| External Compliance | **72.5** | `gst_filing_regularity` — GST filed on time |

**Agent Recommendation:** `monitor` | Urgency: low

**Demo Narrative (maps to Scenario 2 in idea.md):**
> Priya Textiles (simulated as account 2926) applies for ₹10L working capital.
> No CIBIL history, no ITR filed. The Health Agent pulls Account Aggregator data
> (12 months of transactions), EPFO contributions (4-5 employees, regular monthly),
> and GST filings (filed on time). Despite irregular income (normal for textile
> MSME — seasonal monsoon dips), the model identifies strong cash flow adequacy
> (78.8), perfect debt management (100), rapid growth trajectory (100), and good
> GST/EPFO compliance (72.5). Composite health score = 79.7 → **Recommend: Approve**
> with structured EMI. The underwriter sees the visual Health Card with SHAP
> explanations for each dimension.

---

## Demo 3: Early Warning — Preventing NPA (IDBI PS4)

**Account 4462** — Existing borrower, behavioral deterioration detected

| Attribute | Value |
|-----------|-------|
| Account ID | 4462 |
| District | 73 |
| Monthly Income (avg) | ₹92,921 |
| Monthly Surplus | ₹2,249 (thin) |
| Balance (latest) | ₹83,227 |
| Has Loan | Yes |
| Loan Status | **B (Defaulted)** |
| **Default Probability** | **99.7%** |
| Stress Level | **Level 3 — Action Required** |
| Composite Health Score | 46.1 (declining) |

**Why the model flagged this customer (SHAP top factors):**
1. `overdraft_frequency` (SHAP +3.20) — frequent negative/zero balance episodes
2. `balance_below_min_count` (SHAP +1.25) — chronic low balance
3. `emi_delay_avg_days` (SHAP +0.73) — EMIs consistently late
4. `utility_payment_ontime_pct` (SHAP +0.19) — even utilities are being paid late
5. `income_regularity` (SHAP +0.11) — income has become volatile

**Health Card Breakdown (composite = 46.1):**
- Income Stability: 35.9 ⚠️
- Spending Discipline: 94.7 ✓ (not a splurger — stress is external)
- Cash Flow Adequacy: 26.8 ⚠️ (surplus nearly zero)
- Debt Management: 36.7 ⚠️ (EMI bounces + delays)
- Growth Trajectory: 67.3 (moderate)
- External Compliance: 15.0 ⚠️

**Agent Recommendation:** `route_to_risk_agent` | Urgency: **CRITICAL**

**Demo Narrative (maps to Scenario 3 in idea.md):**
> The Risk Agent's continuous monitoring detects behavioral deterioration over 6
> weeks. First, the customer's income becomes irregular (salary delays). Then,
> overdraft episodes spike and balance stays below ₹5K threshold repeatedly. The
> Default Prediction model (Transformer + XGBoost ensemble in production; XGBoost
> here for PoC) spikes the PD from ~5% to 99.7%. SHAP explanations pinpoint:
> overdraft frequency (#1), chronic low balance (#2), EMI delays (#3). The pattern
> matches "job loss / income disruption" — spending discipline remains high (94.7),
> meaning this isn't reckless spending, it's external stress.
>
> The Risk Agent classifies this as Level 3 (Action Required), alerts the RM with
> SHAP-backed reasoning, and sends a gentle courtesy message: "Need flexibility
> with your upcoming EMI? We're here to help." The agent recommends a 2-month EMI
> moratorium to prevent NPA and preserve the customer relationship.

---

## Validation Checklist (all passed)

| # | Check | Result |
|---|-------|--------|
| 1 | Indianized transactions look realistic (₹ amounts, Indian merchants, UPI modes) | ✓ |
| 2 | Feature matrix has no NaN/inf values | ✓ |
| 3 | Propensity model AUC > 0.85 | ✓ (0.9999) |
| 4 | Default model AUC > 0.85 (target 0.90) | ✓ (0.9992) |
| 5 | Health scores distribute reasonably | ✓ (range 0-100, varied std) |
| 6 | SHAP explanations make intuitive sense | ✓ (domain-coherent drivers) |
| 7 | API serves all endpoints with < 200ms response time | ✓ |
| 8 | At least 3 demo customers with interesting stories | ✓ (above) |
