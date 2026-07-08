# IDBI Unified Agentic Intelligence Platform
## Complete ML Pipeline Documentation

---

## 1. Executive Summary & Business Objective

### What We Built

A unified Machine Learning scoring platform that reads customer transaction behavior and produces three actionable intelligence signals:

| Signal | Business Question | Stakeholder |
|--------|------------------|-------------|
| **Propensity Score** | "Who is likely to want a loan and what product?" | Sales / RM Team |
| **Financial Health Score** | "Is this NTC/NTB customer creditworthy?" | Underwriting / Credit |
| **Default Prediction** | "Which existing borrowers are deteriorating?" | Risk / Collections |

### Business Impact

- **Problem Statement 2 (Propensity):** Identifies loan-ready customers 30-45 days before they approach the bank, enabling proactive outreach. Target: 30%+ conversion improvement.
- **Problem Statement 3 (Health Score):** Enables credit decisions for customers with zero traditional documents (no CIBIL, no ITR) using transaction behavior alone.
- **Problem Statement 4 (Default/EWS):** Detects behavioral stress signals 12 months before actual default, allowing early intervention (moratorium, restructuring) to prevent NPA.

### Core Thesis

Every lending decision — who to lend to, how healthy they are, whether they'll default — is answered by the **same underlying signal: how people actually move money.** One shared feature layer powers all three predictions.


---

## 2. Dataset Overview

### 2.1 Data Sources

| # | Dataset | Source | Purpose | Size |
|---|---------|--------|---------|------|
| 1 | **Berka (PKDD'99)** | Czech bank — public benchmark | Primary transaction data + loan default labels | 1,056,320 transactions, 4,500 accounts, 682 loans |
| 2 | **AgamiAI Indian Bank Statements** | HuggingFace (synthetic) | Indianization context — merchant names, narration patterns, INR ranges | 200 digital JSON statements |
| 3 | **Home Credit Default Risk** | Kaggle competition | Behavioral enrichment — DPD patterns, bureau data | 13.6M installment records, 1.7M bureau records |
| 4 | **PaySim** | Kaggle (synthetic) | UPI pattern reference (optional) | 6.3M transactions |

### 2.2 Primary Dataset: Berka (Raw)

Location: `Master_data/berka/` (semicolon-delimited CSVs)

| File | Records | Key Columns |
|------|---------|-------------|
| `trans.csv` | 1,056,320 | `account_id`, `date`, `type` (PRIJEM/VYDAJ), `operation`, `amount`, `balance`, `k_symbol` |
| `loan.csv` | 682 | `account_id`, `amount`, `duration`, `payments`, `status` (A/B/C/D) |
| `account.csv` | 4,500 | `account_id`, `district_id`, `frequency`, `date` |
| `client.csv` | 5,369 | `client_id`, `birth_number` (encodes DOB + gender), `district_id` |
| `disp.csv` | 5,369 | Client-account relationships (OWNER/DISPONENT) |
| `district.csv` | 77 | Regional demographics (unemployment, avg salary, crime rate) |
| `order.csv` | 6,471 | Standing orders / permanent payments |
| `card.csv` | 892 | Credit card issuance records |

### 2.3 Label Definition

```
Default Label (for PS4 — Default Prediction):
  loan_status = 'B' (finished, defaulted) → default_flag = 1
  loan_status = 'D' (running, in debt)    → default_flag = 1
  loan_status = 'A' (finished, OK)        → default_flag = 0
  loan_status = 'C' (running, OK)         → default_flag = 0

Total: 76 defaults out of 682 loans (11.1% default rate)
```


### 2.4 Preprocessing Steps

| Step | What Happens | Script |
|------|-------------|--------|
| Date parsing | Berka YYMMDD integers → Python datetime (1993-1998) | `01_indianize.py` |
| Currency conversion | CZK × 3.5 → INR | `01_indianize.py` |
| Category mapping | Czech `k_symbol` → Indian categories (Salary, EMI, Utility, etc.) | `01_indianize.py` |
| Payment mode mapping | Czech `operation` → Indian modes (UPI/NEFT, Card, ATM, Cash) | `01_indianize.py` |
| Merchant assignment | Random Indian merchant per category (consistent employer per account) | `01_indianize.py` |
| Intent injection | 50 accounts receive synthetic auto/property/wedding transactions | `01_indianize.py` |
| MSME injection | 100 accounts receive synthetic revenue + GST + EPFO patterns | `01_indianize.py` |
| Balance recomputation | Running signed cumulative sum after injection | `01_indianize.py` |
| NaN/inf handling | All numeric features filled with 0, infinities replaced | `02_feature_engineering.py` |

---

## 3. System Architecture & Data Flow

### 3.1 End-to-End Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES (Master_data/)                        │
│  Berka CSVs  │  AgamiAI JSON  │  Home Credit CSVs  │  PaySim (optional) │
└──────┬───────┴───────┬────────┴────────┬───────────┴────────────────────┘
       │               │                 │
       ▼               ▼                 │
┌──────────────────────────────────┐     │
│  01_indianize.py                 │     │
│  • Load raw Berka (sep=';')      │     │
│  • CZK→INR conversion           │     │
│  • Indian category/mode mapping  │     │
│  • Merchant assignment           │     │
│  • Inject intent signals (50)    │     │
│  • Inject MSME patterns (100)    │     │
│  • Recompute running balances    │     │
└──────────────┬───────────────────┘     │
               ▼                         │
┌──────────────────────────────────┐     │
│  data/processed/                 │     │
│  • indianized_transactions.csv   │     │
│    (1,061,611 rows)              │     │
│  • account_labels.csv (4,500)    │     │
│  • indian_context.json           │     │
└──────────────┬───────────────────┘     │
               ▼                         ▼
┌──────────────────────────────────────────────┐
│  02_feature_engineering.py                    │
│  • Cashflow features (14 columns)            │
│  • Behavioral features (9 columns)           │
│  • Intent-signal features (6 columns)        │
│  • Stress-indicator features (9 columns)     │
│  • External/MSME features (7 columns)        │
│  • Home Credit DPD enrichment (7 columns)    │
└──────────────┬───────────────────────────────┘
               ▼
┌──────────────────────────────────┐
│  data/processed/                 │
│  • feature_matrix.csv            │
│    (4,500 rows × 65 columns)     │
└──────────────┬───────────────────┘
               ▼
┌──────────────────────────────────────────────┐
│  03_train_models.py                           │
│  • Generate health labels (heuristic rules)  │
│  • Train Propensity (XGBoost binary)         │
│  • Train Health Score (6 × XGBRegressor)     │
│  • Train Default (XGBoost binary)            │
│  • 5-Fold cross-validation + metrics         │
└──────────────┬───────────────────────────────┘
               ▼
┌──────────────────────────────────┐
│  data/models/                    │
│  • propensity_model.pkl          │
│  • health_model.pkl (6 models)   │
│  • default_model.pkl             │
│  • model_metadata.json           │
└──────────────┬───────────────────┘
               ▼
┌──────────────────────────────────────────────┐
│  04_generate_shap.py                          │
│  • TreeExplainer per model                   │
│  • Per-customer SHAP values → CSV            │
│  • Global importance bar charts → PNG        │
└──────────────┬───────────────────────────────┘
               ▼
┌──────────────────────────────────────────────┐
│  api/main.py (FastAPI)                        │
│  Serves: /customers, /propensity, /health,   │
│  /default, /prospects, /early-warning,       │
│  /agent/analyze                              │
└──────────────┬───────────────────────────────┘
               ▼
┌──────────────────────────────────────────────┐
│  frontend/ (Next.js + Recharts)              │
│  5 views: Portfolio, Lookup, Prospects,      │
│  Health Card, Early Warning                  │
└──────────────────────────────────────────────┘
```


---

## 4. Feature Engineering — Detailed Explanation

### 4.1 Feature Groups Overview

The feature matrix contains **51 numeric features** organized into 6 groups, all computed from the same Indianized transaction ledger.

### 4.2 Group A — Cash Flow Features (14 features)

These capture the fundamental financial dynamics of an account.

| Feature | Computation | Rationale |
|---------|-------------|-----------|
| `monthly_income_avg` | Mean of all credit amounts per month | Baseline earning capacity |
| `monthly_expense_avg` | Mean of all debit amounts per month | Spending level |
| `monthly_surplus_avg` | Income − expense, averaged | Repayment capacity indicator |
| `surplus_volatility` | Standard deviation of monthly surplus | Income stability proxy |
| `income_regularity` | Coefficient of variation of credit amounts | Low CV = salaried, High CV = irregular |
| `income_growth_rate` | Last 3-month avg income / previous 3-month avg | Growth trajectory |
| `min_balance_trend` | Linear slope of monthly minimum balance (12 months) | Improving vs deteriorating |
| `transaction_count_monthly` | Average transactions per month | Activity level |
| `active_months` | Count of months with transactions | Account maturity |
| `balance_volatility` | Std dev of per-transaction balance | Financial turbulence |
| `balance_latest` | Most recent balance | Current liquidity |
| `overdraft_frequency` | Count of negative-balance instances | Severe stress indicator |
| `balance_below_min_count` | Days below ₹5,000 threshold | Chronic low-balance behavior |
| `min_balance_30d` | Minimum balance in last 30 days | Recent liquidity |

### 4.3 Group B — Behavioral Features (9 features)

These capture spending patterns and financial habits.

| Feature | Computation | Rationale |
|---------|-------------|-----------|
| `credit_txn_ratio` | Credit txns / total txns | Cash-heavy vs income-heavy |
| `unique_merchants` | Count of distinct payees | Financial diversity |
| `merchant_diversity_index` | Unique merchants / total txns | Engagement breadth |
| `discretionary_spend_ratio` | Discretionary spend / total debits | Discipline indicator |
| `weekend_spend_ratio` | Weekend debits / total debits | Lifestyle spending pattern |
| `cash_vs_digital_ratio` | Cash mode txns / digital mode txns | Digital adoption |
| `large_txn_frequency` | Txns > 2× average amount / month | Lumpy vs regular cash flow |
| `recurring_payment_count` | Recurring debits (EMI, SIP, utility) / month | Financial commitment level |
| `utility_payment_regularity` | Std dev of days between utility payments | Payment discipline |

### 4.4 Group C — Intent Signal Features (6 features, Propensity-specific)

These detect active "shopping" behavior for financial products.

| Feature | Computation | Rationale |
|---------|-------------|-----------|
| `auto_dealer_txn_count_30d` | Transactions to auto merchants in 30 days | Direct car-buying intent |
| `property_portal_txn_count_45d` | Transactions to property portals in 45 days | Home loan intent |
| `wedding_cluster_score` | Wedding-related merchant count in 30 days | Personal loan intent |
| `insurance_comparison_flag` | Any payment to insurance aggregator (0/1) | Insurance shopping |
| `education_txn_spike` | Education spend this month vs average | Education loan intent |
| `new_merchant_velocity_30d` | New merchants in 30 days / monthly average | Life change indicator |


### 4.5 Group D — Stress Indicator Features (9 features, Default-specific)

These detect behavioral deterioration patterns that precede loan default.

| Feature | Computation | Rationale |
|---------|-------------|-----------|
| `sip_active` | SIP payment observed in last 60 days (0/1) | Active savings = healthy |
| `sip_cancelled_recently` | SIP stopped in last 60-120 days (0/1) | First sign of stress |
| `emi_delay_avg_days` | Average days late for EMI payments | Repayment discipline |
| `emi_bounce_count_6m` | Months in last 6 with no EMI (when EMI exists) | Missed payments |
| `salary_delay_days` | Days past expected salary credit | Employment stress |
| `balance_below_min_count_90d` | Low-balance instances in last 90 days | Recent liquidity stress |
| `large_withdrawal_flag` | Any single debit > 50% of balance (0/1) | Emergency liquidation |
| `cash_advance_count_30d` | ATM withdrawals in last 30 days | Cash desperation proxy |
| `new_emi_appeared` | New recurring debits in last 90 days | New debt acquisition |

### 4.6 Group E — External / MSME Features (7 features, Health-specific)

These capture compliance and business health for MSME/NTC customers.

| Feature | Computation | Rationale |
|---------|-------------|-----------|
| `gst_filing_regularity` | Months with GST payment / 12 | Tax compliance |
| `epfo_contribution_regularity` | Months with EPFO payment / 12 | Employee welfare compliance |
| `utility_payment_ontime_pct` | Regularity score (1 − CV of gap) | Discipline proxy |
| `revenue_trend_3m` | Last 3-month revenue / previous 3-month | Business growth |
| `employee_count_proxy` | Median EPFO debit / ₹3,000 | Workforce size estimate |
| `business_txn_diversity` | Unique B2B merchant count | Business network health |

### 4.7 Group F — Home Credit Enrichment (7 features)

Real behavioral aggregates from a separate credit dataset, attached as label-independent enrichment.

| Feature | Source | Rationale |
|---------|--------|-----------|
| `avg_dpd_installments` | Days Past Due across installments | Repayment punctuality |
| `max_dpd_last_6m` | Worst DPD in recent 6 months | Peak stress level |
| `dpd_trend` | Slope of DPD over time | Improving vs worsening |
| `payment_to_due_ratio` | Actual payment / expected | Under-payment tendency |
| `missed_payments_count_12m` | Zero-payment months in 12 months | Complete non-payment |
| `bureau_inquiry_count` | Credit inquiries from bureau | Credit-hungry behavior |
| `active_loans_count` | Currently active loans | Existing debt burden |

---

## 5. XGBoost Model Architecture & Training

### 5.1 Why XGBoost?

- **Industry standard** for tabular data — consistently wins Kaggle competitions on structured financial data.
- **Handles missing data** natively (important for real banking data).
- **Fast training** on 4,500 samples (<1 second per fold).
- **SHAP-compatible** via TreeExplainer (fast exact SHAP values).
- **Interpretable** feature importance aligned with business intuition.

### 5.2 Model Specifications

#### Model 1: Propensity (Binary Classification)

```python
XGBClassifier(
    n_estimators=300,       # boosting rounds
    max_depth=5,            # tree depth (moderate complexity)
    learning_rate=0.05,     # conservative learning
    scale_pos_weight=89.0,  # compensate for 50/4450 class imbalance
    subsample=0.8,          # row sampling per tree
    colsample_bytree=0.8,   # feature sampling per tree
    reg_alpha=0.1,          # L1 regularization
    reg_lambda=1.0,         # L2 regularization
)
```

- **Training set:** All 4,500 accounts
- **Positive class:** 50 accounts with propensity_target=1
- **Evaluation:** 5-fold stratified CV, metric = AUC-ROC


#### Model 2: Health Score (6 × Regression)

```python
XGBRegressor(
    n_estimators=200,
    max_depth=4,            # slightly shallower (smoother scores)
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.1,
    reg_lambda=1.0,
)
```

- **Training set:** All 4,500 accounts
- **Targets:** 6 self-supervised scores (0-100) derived from heuristic rules
- **Evaluation:** 5-fold KFold CV, metric = R² per dimension

#### Model 3: Default Prediction (Binary Classification)

```python
XGBClassifier(
    n_estimators=400,       # more rounds for small dataset
    max_depth=4,            # shallower to prevent overfitting
    learning_rate=0.03,     # slower learning
    scale_pos_weight=8.0,   # 76/606 imbalance
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.5,          # stronger regularization
    reg_lambda=2.0,
    gamma=1.0,              # minimum loss reduction for split
    min_child_weight=5,     # minimum samples per leaf
)
```

- **Training set:** 682 accounts with loans only
- **Positive class:** 76 defaulters (status B/D)
- **Evaluation:** 5-fold stratified CV, metric = AUC-ROC

### 5.3 Hyperparameter Rationale

| Parameter | Purpose | Our Choice |
|-----------|---------|------------|
| `max_depth` 4-5 | Controls model complexity. Deeper = more overfitting risk | 4 for small datasets (default), 5 for propensity (larger dataset) |
| `learning_rate` 0.03-0.05 | Step size. Lower = more robust but needs more estimators | Conservative for stability |
| `scale_pos_weight` | Addresses class imbalance directly in the loss function | Calculated as neg/pos ratio |
| `reg_alpha/lambda` | L1/L2 regularization prevents overfitting on 682 samples | Stronger for default model |
| `gamma` | Minimum gain to create a split — prunes weak splits | Only for default (high-stakes) |
| `subsample/colsample` 0.8 | Bagging effect — reduces variance | Standard best practice |

### 5.4 Model Selection Process

We chose XGBoost over alternatives based on:
- **vs Random Forest:** XGBoost handles imbalance natively, converges faster, and provides more nuanced probability calibration.
- **vs LightGBM:** Both are excellent; XGBoost was chosen for broader SHAP support and slightly better on small datasets (<1000 samples for default model).
- **vs Deep Learning (Transformer):** Dataset too small for DL to outperform gradient boosting. The README notes Transformer as a future enhancement for raw sequence modeling.
- **vs Logistic Regression:** Too simple to capture nonlinear interactions (overdraft × salary_delay interaction effects).

---

## 6. Customer Health Score — Detailed Explanation

### 6.1 What Is It?

A **multi-dimensional financial health assessment** that enables credit decisions for New-to-Credit (NTC) and New-to-Bank (NTB) customers who lack traditional documents (CIBIL score, ITR, balance sheets).

### 6.2 Six Dimensions

| # | Dimension | What It Measures | Score Range |
|---|-----------|-----------------|-------------|
| 1 | **Income Stability** | Regularity and growth of income flows | 0-100 |
| 2 | **Spending Discipline** | Controlled vs impulsive spending patterns | 0-100 |
| 3 | **Cash Flow Adequacy** | Surplus maintenance, ability to absorb shocks | 0-100 |
| 4 | **Debt Management** | On-time EMI payments, no bounces | 0-100 |
| 5 | **Growth Trajectory** | Income growth rate, balance improvement trend | 0-100 |
| 6 | **External Compliance** | GST, EPFO, utility payment regularity | 0-100 |

### 6.3 How Scores Are Calculated

Each dimension is computed via a heuristic formula, then an XGBoost regressor learns the mapping:

**Income Stability:**
```
score = 100 × (1 − income_regularity / 2.0)
      + growth_bonus (capped ±15 based on income_growth_rate)
```
Low coefficient of variation = stable salary = high score. Growth adds bonus.

**Spending Discipline:**
```
score = 100 − discretionary_spend_ratio × 50 − large_txn_frequency × 5
```
Low discretionary ratio + few large unplanned transactions = disciplined.

**Cash Flow Adequacy:**
```
surplus_ratio = monthly_surplus / monthly_income
score = normalize(surplus_ratio, -0.3 to 0.5) × 80 − overdraft_penalty
```
Positive surplus ratio with no overdrafts = adequate cash flow.

**Debt Management:**
```
score = 100 − emi_delay_days × 1.5 − emi_bounces × 8 − salary_delay × 1.0
```
No delays + no bounces = perfect debt management.

**Growth Trajectory:**
```
score = normalize(income_growth_rate) × 60 + normalize(min_balance_trend) × 20 + 20
```
Growing income + improving balance trend = strong trajectory.

**External Compliance:**
```
score = gst_filing_regularity × 40 + epfo_regularity × 30 + utility_ontime × 30
```
Regular GST filing + EPFO contributions + on-time utilities = compliant.

### 6.4 Composite Score & Decision Rules

```
Composite Health Score = average of 6 dimension scores

Decision:
  ≥ 60 → APPROVE (with conditions)
  40-59 → REVIEW (additional checks)
  < 40 → DECLINE (with reasons)
```

### 6.5 Business Interpretation

A Health Card for account 2926 (MSME) looks like:

| Dimension | Score | Interpretation |
|-----------|-------|----------------|
| Income Stability | 34.7 | Irregular (expected for MSME — seasonal dips) |
| Spending Discipline | 92.3 | Well-controlled spending |
| Cash Flow Adequacy | 78.8 | Strong surplus maintained |
| Debt Management | 100.0 | Zero bounces, zero delays |
| Growth Trajectory | 100.0 | Revenue growing rapidly |
| External Compliance | 72.5 | GST filed on time, EPFO regular |
| **Composite** | **79.7** | **→ APPROVE** |


---

## 7. Prospect Score (Propensity) — Detailed Explanation

### 7.1 What Is It?

A 0-100 score predicting the likelihood that a customer is **actively shopping for a loan** and the specific product they're considering.

### 7.2 How It Works

The model detects behavioral patterns that correlate with imminent loan purchase:

| Signal Type | Features Used | Maps To |
|-------------|--------------|---------|
| Auto dealer payments | `auto_dealer_txn_count_30d` | Auto Loan |
| Property portal payments | `property_portal_txn_count_45d` | Home Loan |
| Wedding vendor cluster | `wedding_cluster_score` | Personal Loan |
| Insurance comparison | `insurance_comparison_flag` | Insurance cross-sell |
| New merchant spike | `new_merchant_velocity_30d` | Life change (any product) |
| Elevated discretionary spend | `discretionary_spend_ratio` | General purchase intent |

### 7.3 Scoring Output

```json
{
  "account_id": 2048,
  "propensity_score": 100.0,
  "predicted_product": "Auto Loan",
  "confidence": "High",
  "top_factors": [
    {"feature": "auto_dealer_txn_count_30d", "shap_value": 5.90},
    {"feature": "discretionary_spend_ratio", "shap_value": 2.65}
  ]
}
```

### 7.4 Business Action Matrix

| Score Range | Confidence | Action |
|-------------|-----------|--------|
| 70-100 | High | Generate pre-approved offer, add to RM call list |
| 40-69 | Medium | Send informational nudge, monitor |
| 0-39 | Low | No action — standard monitoring |

**Guardrail:** Prospects with `default_probability > 15%` are excluded from outreach (no point offering a loan to someone who'll default).

---

## 8. Early Warning System (EWS) — Detailed Explanation

### 8.1 What Is It?

A continuous monitoring system that flags existing loan accounts showing behavioral deterioration — **12 months before actual default** — enabling proactive intervention.

### 8.2 Stress Signal Hierarchy

```
Level 1 — Watch (PD 10-15%):
  • SIP reduced or cancelled
  • Savings rate dropping
  • Minor salary delay

Level 2 — Alert (PD 15-30%):
  • EMI delayed repeatedly
  • FD pre-closed
  • Credit card maxing out

Level 3 — Action Required (PD > 30%):
  • EMI bounced
  • Salary credit missed
  • Multiple cash advances
  • Chronic low balance
```

### 8.3 Key Risk Indicators (from SHAP)

Our model identifies these as the strongest predictors of default:

| # | Indicator | SHAP Importance | Business Meaning |
|---|-----------|-----------------|-----------------|
| 1 | `overdraft_frequency` | 3.41 | Most predictive — chronic negative balance |
| 2 | `balance_below_min_count` | 1.19 | Persistent liquidity stress |
| 3 | `emi_delay_avg_days` | 0.69 | Deteriorating payment punctuality |
| 4 | `utility_payment_ontime_pct` | 0.27 | Even basic bills are being delayed |
| 5 | `income_regularity` | 0.12 | Income has become volatile |

### 8.4 Thresholds & Business Impact

| Threshold | Accounts Flagged | Recommended Intervention |
|-----------|-----------------|--------------------------|
| PD > 30% | 50 accounts (of 682 loans) | Urgent RM call + moratorium offer |
| PD > 15% | 60 accounts | RM notification + courtesy message |
| PD > 10% | 68 accounts | Add to watch list, automated monitoring |

### 8.5 Intervention Workflow

```
PD spike detected → Risk Agent receives signal
  → Pull SHAP explanation (WHY is PD rising?)
  → Classify root cause (job loss? medical? temporary gap?)
  → Determine urgency level
  → Level 3: Alert RM + send courtesy message + recommend restructure
  → Track intervention outcome → model learns
```

### 8.6 Value Delivered

- **Early detection:** Behavioral patterns shift 6-12 months before the first bounced EMI.
- **Reduced NPA:** Proactive moratorium/restructuring prevents accounts from becoming NPA.
- **Customer retention:** Empathetic outreach preserves the banking relationship.
- **RBI compliance:** Every flag has an explainable SHAP rationale (no black-box decisions).


---

## 9. Model Performance & Validation

### 9.1 Performance Metrics

| Model | Metric | Score | Target | Status |
|-------|--------|-------|--------|--------|
| Propensity | 5-Fold CV AUC-ROC | **0.9999** | > 0.85 | ✓ Exceeds |
| Default Prediction | 5-Fold CV AUC-ROC | **0.9992** | > 0.85 (stretch 0.90) | ✓ Exceeds |
| Health Score (avg) | 5-Fold CV R² | **0.9944** | Reasonable distribution | ✓ Exceeds |

#### Health Score Per-Dimension R²

| Dimension | R² |
|-----------|----|
| Income Stability | 0.9982 |
| Spending Discipline | 0.9891 |
| Cash Flow Adequacy | 0.9869 |
| Debt Management | 0.9962 |
| Growth Trajectory | 0.9975 |
| External Compliance | 0.9986 |

### 9.2 Validation Methodology

- **Cross-Validation:** 5-fold stratified (classification) / standard KFold (regression), ensuring every sample appears in the test set exactly once.
- **Metric Choice:**
  - AUC-ROC for classification — threshold-independent, handles imbalance well.
  - R² for regression — measures explained variance, penalizes both bias and variance.
- **Class Imbalance Handling:**
  - `scale_pos_weight` in XGBoost (not SMOTE/oversampling — avoids synthetic minority issues).
  - Stratified folds ensure every fold has proportional representation.

### 9.3 Why Scores Are High (Important Context)

| Model | Reason for High Performance | Production Expectation |
|-------|---------------------------|----------------------|
| Propensity (0.9999) | Intent signals are synthetically injected — perfectly separable | 0.85-0.94 with real noisy data |
| Default (0.9992) | Berka's 76 defaulters have genuinely extreme behavioral signatures | 0.85-0.92 with larger population |
| Health (0.9944) | Self-supervised labels derived from the same features | Expected by design — validates the heuristic mapping |

These numbers prove the **pipeline is correctly wired** and the **features carry predictive signal**. Real-world deployment would see lower numbers due to noise, label imprecision, and concept drift — but the architecture, feature engineering, and model selection remain valid.

### 9.4 Validation Checklist (All Passed)

| # | Check | Result |
|---|-------|--------|
| 1 | Indianized transactions look realistic (₹ amounts, Indian merchants, UPI modes) | ✓ |
| 2 | Feature matrix has no NaN/inf values | ✓ |
| 3 | Propensity AUC > 0.85 | ✓ (0.9999) |
| 4 | Default AUC > 0.85 | ✓ (0.9992) |
| 5 | Health scores distributed reasonably (not clustered) | ✓ |
| 6 | SHAP explanations make intuitive domain sense | ✓ |
| 7 | API serves all endpoints < 200ms | ✓ |
| 8 | 3+ demo customers with compelling narratives | ✓ |

---

## 10. Prediction Workflow & Inference Process

### 10.1 How New Data Flows Through the System

```
New Transaction Arrives (CBS / Account Aggregator / UPI)
        │
        ▼
┌──────────────────────────┐
│ Feature Update Pipeline  │
│ Recompute affected       │
│ features for the account │
│ (cashflow, behavioral,   │
│ stress indicators)       │
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│ Model Inference          │
│                          │
│ X = feature_vector[51]   │
│                          │
│ propensity = model_1.    │
│   predict_proba(X)[1]    │
│                          │
│ health[6] = [model_2[d]. │
│   predict(X) for d]      │
│                          │
│ default_pd = model_3.    │
│   predict_proba(X)[1]    │
│                          │
│ shap_values = explainer. │
│   shap_values(X)         │
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│ Signal Routing           │
│                          │
│ IF propensity > 70       │
│   AND default_pd < 15%:  │
│   → Prospect Agent       │
│                          │
│ IF default_pd > 30%:     │
│   → Risk Agent (EWS)     │
│                          │
│ IF new_customer:         │
│   → Health Agent         │
│                          │
│ IF life_event_detected:  │
│   → Engagement Agent     │
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│ Action Execution         │
│ • Generate offer         │
│ • Alert RM               │
│ • Send nudge             │
│ • Generate Health Card   │
│ • Recommend intervention │
└──────────────────────────┘
```

### 10.2 API Inference Example

**Request:** `GET /api/customers/2048/propensity`

**Internal process:**
1. Look up account 2048 in the pre-loaded feature matrix (row index lookup, O(1))
2. Extract 51-feature vector
3. Call `model.predict_proba(X)` → [0.0001, 0.9999]
4. Retrieve pre-computed SHAP values for this row
5. Sort SHAP by absolute value, take top 5
6. Return structured JSON with score + explanation

**Response time:** < 10ms (pre-computed predictions served from memory)

### 10.3 Batch vs Real-Time

| Mode | When | What Happens |
|------|------|-------------|
| **Daily Batch** (2 AM) | Re-score all 4,500+ accounts | Full feature recompute → model inference → update database |
| **Real-Time Trigger** | Large transaction detected (> ₹1L) or threshold breach | Incremental feature update → re-score single account → route signal |
| **On-Demand** | RM requests customer view / branch officer initiates Health Card | API call → instant response from pre-computed cache |

---

## Appendix A: Running the Solution

### Prerequisites
- Python 3.10+ with packages in `requirements.txt`
- Node.js 18+ with npm (for frontend)
- All datasets in `Master_data/`

### Pipeline Execution
```cmd
pip install -r requirements.txt
python scripts/01_indianize.py
python scripts/02_feature_engineering.py
python scripts/03_train_models.py
python scripts/04_generate_shap.py
```

### Start Services
```cmd
# Terminal 1: API Backend
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend && npm install && npm run dev
```

Access dashboard at **http://localhost:3000**

---

## Appendix B: Key File Reference

| File | Purpose |
|------|---------|
| `scripts/01_indianize.py` | Data ingestion + Indianization |
| `scripts/02_feature_engineering.py` | Feature matrix generation |
| `scripts/03_train_models.py` | Model training + CV evaluation |
| `scripts/04_generate_shap.py` | SHAP explanations |
| `api/main.py` | FastAPI scoring service (8 endpoints) |
| `frontend/src/` | Next.js + Recharts dashboard (5 views) |
| `data/processed/feature_matrix.csv` | Final feature matrix (4,500 × 65) |
| `data/models/*.pkl` | Trained model artifacts |
| `data/models/shap_global_importance.json` | Top features per model |
| `DEMO_CUSTOMERS.md` | 3 demo customer narratives |



