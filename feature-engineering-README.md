# Feature Engineering Pipeline — Setup & Guide

## Datasets to Download

### 1. Berka (PKDD'99 Financial Dataset) — PRIMARY
The backbone of our data. Real Czech bank transactions with loan default labels.

**Download:** https://relational.fit.cvut.cz/dataset/Financial
**Alternative (GitHub with CSVs):** https://github.com/sorayutmild/loan-default-prediction (check `transformed_data/` folder)
**Kaggle mirror:** Search "Berka financial dataset" or "PKDD 99 Financial"

**What you get:**
| File | Records | Content |
|------|---------|---------|
| trans.csv | 1,056,320 | All transactions (date, type, amount, balance, category) |
| loan.csv | 682 | Loans with status: A (OK), B (defaulted), C (running OK), D (running in debt) |
| account.csv | 4,500 | Account creation date, district |
| client.csv | 5,369 | Birth date, gender, district |
| disp.csv | 5,369 | Client-account relationship |
| order.csv | 6,471 | Permanent/recurring orders (standing instructions) |
| card.csv | 892 | Credit cards issued |
| district.csv | 77 | Regional demographics (unemployment, avg salary, crime, population) |

**Key columns in trans.csv:**
```
trans_id | account_id | date | type | operation | amount | balance | k_symbol | bank | account
```
- type: PRIJEM (credit) / VYDAJ (debit)
- operation: Credit Card Withdrawal, Cash Deposit, Collection from Another Bank, Cash Withdrawal, Remittance to Another Bank
- k_symbol: Insurance, Household, Pension, Interest, Loan Payment, Statement, Sanction Interest
- balance: Account balance AFTER the transaction

**Key columns in loan.csv:**
```
loan_id | account_id | date | amount | duration | payments | status
```
- status: A = finished OK, B = finished DEFAULTED, C = running OK, D = running IN DEBT
- **B and D are our positive labels (default = 1)**

---

### 2. AgamiAI/Indian-Bank-Statements — INDIANIZATION
Synthetic Indian business bank statements with realistic patterns.

**Download:** https://huggingface.co/datasets/AgamiAI/Indian-Bank-Statements
**Alternative fork:** https://huggingface.co/datasets/Akashved/Indian-Bank-Statements

**What you get:**
- JSON format Indian bank statements
- Indian merchant names (Reliance, Tata, Swiggy, BigBasket, etc.)
- UPI/NEFT/RTGS/IMPS transaction modes
- INR amounts with realistic Indian spending ranges
- Business patterns (B2B payments, vendor settlements)

**Use this for:**
- Extracting Indian merchant name lists
- Understanding Indian transaction narration patterns
- Getting realistic INR amount ranges per category
- UPI-specific transaction mode distribution

---

### 3. Home Credit Default Risk (Kaggle) — BEHAVIORAL ENRICHMENT
Rich behavioral payment data for default prediction enhancement.

**Download:** https://www.kaggle.com/c/home-credit-default-risk/data

**Files we need (not all):**
| File | What it gives us |
|------|-----------------|
| installments_payments.csv | Actual vs expected payment dates → Days Past Due (DPD) patterns |
| POS_CASH_balance.csv | Monthly loan balance snapshots → deterioration curves |
| bureau.csv | External credit history → inquiry count, active loans |
| previous_application.csv | Past loan applications → approval/rejection patterns |

**Key behavioral features we'll derive:**
- Average DPD (days past due) — strongest default predictor
- DPD trend (increasing = trouble)
- Number of missed payments in last 6 months
- Payment-to-due ratio over time
- Credit utilization trend

---

### 4. PaySim (Optional — UPI Pattern Reference)
Synthetic mobile money transactions simulating UPI-like patterns.

**Download:** https://www.kaggle.com/datasets/ealaxi/paysim1

**Schema:**
```
step | type | amount | nameOrig | oldbalanceOrg | newbalanceOrig | nameDest | oldbalanceDest | newbalanceDest | isFraud
```
- type: CASH_IN, CASH_OUT, PAYMENT, TRANSFER, DEBIT
- 6.3M transactions

**Use this for:** Understanding P2P/P2M transaction distributions (maps to UPI)

---

## Post-Download Steps

### Step 1: Place Files in Project Structure

```
unified-agentic-platform/
├── data/
│   ├── raw/
│   │   ├── berka/
│   │   │   ├── trans.csv
│   │   │   ├── loan.csv
│   │   │   ├── account.csv
│   │   │   ├── client.csv
│   │   │   ├── disp.csv
│   │   │   ├── order.csv
│   │   │   ├── card.csv
│   │   │   └── district.csv
│   │   ├── agamai/
│   │   │   └── indian_bank_statements.json
│   │   ├── home_credit/
│   │   │   ├── installments_payments.csv
│   │   │   ├── POS_CASH_balance.csv
│   │   │   ├── bureau.csv
│   │   │   └── previous_application.csv
│   │   └── paysim/
│   │       └── PS_20174392719_1491204016305_log.csv (optional)
│   ├── processed/
│   │   ├── indianized_transactions.csv
│   │   ├── customer_profiles.csv
│   │   └── feature_matrix.csv
│   └── models/
│       ├── propensity_model.pkl
│       ├── health_model.pkl
│       └── default_model.pkl
├── scripts/
│   ├── 01_indianize_berka.py
│   ├── 02_feature_engineering.py
│   ├── 03_train_models.py
│   └── 04_generate_shap.py
├── api/
│   └── main.py (FastAPI)
├── frontend/
│   └── (Next.js app)
└── agents/
    └── (Strands agent code)
```

---

### Step 2: Indianize Berka Data (`01_indianize_berka.py`)

**Currency Conversion:**
- 1 CZK ≈ 3.5 INR (use as multiplier)
- Round to realistic Indian amounts

**Category Mapping (k_symbol → Indian):**
```python
CATEGORY_MAP = {
    "POJISTNE": "LIC Premium",           # Insurance
    "SLUZBY": "Service Charge",           # Bank statement fees
    "UROK": "Interest Credit",            # Interest earned
    "SANKC. UROK": "Penalty Interest",    # Penalty for low balance
    "SIPO": "Electricity Bill",           # Household/utility
    "DUCHOD": "Salary",                   # Pension → we'll use as salary
    "UVER": "EMI Payment",               # Loan payment
}
```

**Operation Mapping (operation → Indian payment modes):**
```python
OPERATION_MAP = {
    "VYBER KARTOU": "Card",               # Card withdrawal
    "VKLAD": "Cash Deposit",              # Cash deposit
    "PREVOD Z UCTU": "NEFT/IMPS",         # Transfer from another bank
    "VYBER": "ATM Withdrawal",            # Cash withdrawal
    "PREVOD NA UCET": "UPI/NEFT",         # Transfer to another bank
}
```

**Add Indian Merchant Names (by category):**
```python
MERCHANTS = {
    "salary": ["TCS Ltd", "Infosys Ltd", "Wipro Ltd", "HCL Tech", "Reliance Ind"],
    "grocery": ["BigBasket", "DMart", "Reliance Fresh", "More Supermarket"],
    "food": ["Swiggy", "Zomato", "Dominos", "McDonalds"],
    "utility": ["BESCOM", "Jio Postpaid", "Airtel", "BWSSB", "Indane Gas"],
    "emi": ["HDFC Bank EMI", "ICICI EMI", "Bajaj Finserv EMI"],
    "sip": ["SBI MF SIP", "HDFC MF SIP", "Axis MF SIP"],
    "insurance": ["LIC Premium", "HDFC Life", "ICICI Prudential"],
    "rent": ["House Rent", "Flat Rent Transfer"],
    "auto_dealer": ["Maruti Suzuki Arena", "Hyundai Showroom", "Tata Motors"],
    "property": ["MagicBricks", "99acres Premium", "NoBroker"],
    "education": ["DPS School Fee", "Byju's", "Unacademy"],
    "travel": ["MakeMyTrip", "IRCTC", "IndiGo Airlines"],
    "wedding": ["Taj Banquets", "Tanishq Jewellers", "FNP Weddings"],
}
```

**Inject Intent Signals (for Propensity — PS2):**
- Pick 50 accounts randomly
- For 20: Add 3-5 auto_dealer transactions in last 30 days → Auto Loan intent
- For 15: Add 3-5 property transactions in last 45 days → Home Loan intent
- For 15: Add wedding/travel/education spikes → Personal Loan intent
- Label these as `propensity_target = 1`

**Inject MSME Patterns (for Health Score — PS3):**
- Pick 100 accounts
- Change their income pattern to irregular (variable daily/weekly credits instead of monthly salary)
- Add GST-like quarterly outflow patterns
- Add EPFO-like monthly fixed small debits (₹1800-5000 range × employee count)
- Vary quality: 60 healthy, 25 borderline, 15 unhealthy

---

### Step 3: Feature Engineering (`02_feature_engineering.py`)

**Per-customer features to compute (grouped):**

#### A. Cash Flow Features (from transactions)
```python
features_cashflow = {
    "monthly_income_avg": "avg of all credits per month",
    "monthly_expense_avg": "avg of all debits per month", 
    "monthly_surplus_avg": "income - expense per month, averaged",
    "surplus_volatility": "std_dev of monthly surplus",
    "min_balance_30d": "minimum balance in last 30 days",
    "min_balance_trend": "slope of monthly min_balance over 12 months",
    "income_regularity": "coefficient of variation of income amounts",
    "income_growth_rate": "last 3mo avg income / prev 3mo avg income",
    "balance_volatility": "std_dev of daily closing balance",
    "overdraft_frequency": "count of days balance < 0 or < min_threshold",
}
```

#### B. Behavioral Features (from transaction patterns)
```python
features_behavioral = {
    "transaction_count_monthly": "total txns per month, averaged",
    "credit_txn_ratio": "credits / total txns",
    "unique_merchants": "count of unique payees/merchants",
    "merchant_diversity_index": "unique / total",
    "discretionary_spend_ratio": "food+shopping+travel / total spend",
    "utility_payment_regularity": "std_dev of days between utility payments",
    "weekend_spend_ratio": "weekend spend / total",
    "large_txn_frequency": "txns > 2x average amount, per month",
    "recurring_payment_count": "count of identified recurring debits (EMI, SIP, rent)",
    "cash_vs_digital_ratio": "cash txns / digital txns",
}
```

#### C. Intent Signal Features (for Propensity)
```python
features_intent = {
    "auto_dealer_txn_count_30d": "transactions to auto merchants in 30 days",
    "property_portal_txn_count_45d": "transactions to property merchants in 45 days",
    "education_txn_spike": "education spend this month / avg education spend",
    "wedding_cluster_score": "wedding-related merchant count in 30 days",
    "insurance_comparison_flag": "any txn to insurance aggregators",
    "new_merchant_velocity_30d": "new merchants this month vs average",
}
```

#### D. Stress Indicators (for Default Prediction)
```python
features_stress = {
    "sip_active": "is SIP still running (1/0)",
    "sip_cancelled_recently": "was SIP active before but stopped in last 60d",
    "emi_delay_avg_days": "average days past expected EMI date",
    "emi_bounce_count_6m": "count of months where EMI was not paid",
    "salary_delay_days": "days past expected salary credit date",
    "balance_below_min_count": "days in last 90 where balance < 5000",
    "large_withdrawal_flag": "any single withdrawal > 50% of balance",
    "fd_preclosure_flag": "any FD broken before maturity (from narration)",
    "cash_advance_count_30d": "cash advances / ATM beyond normal pattern",
    "new_emi_appeared": "new recurring debit started (new debt acquisition)",
}
```

#### E. External/MSME Features (for Health Score)
```python
features_external = {
    "gst_filing_regularity": "simulated: months filed on time / 12",
    "epfo_contribution_regularity": "simulated: months contributed / 12",
    "utility_payment_ontime_pct": "% of utility payments before due date",
    "revenue_trend_3m": "last 3mo revenue / prev 3mo revenue (MSMEs)",
    "employee_count_proxy": "count of EPFO-like debits / avg EPFO amount",
    "business_txn_diversity": "unique business payees (B2B indicator)",
}
```

#### F. Home Credit Behavioral Features (nice-to-have enrichment)
```python
features_home_credit = {
    "avg_dpd_installments": "average days past due across installments",
    "max_dpd_last_6m": "worst DPD in last 6 months",
    "dpd_trend": "slope of DPD over time (increasing = bad)",
    "payment_to_due_ratio": "actual payment / expected payment, averaged",
    "missed_payments_count_12m": "installments where payment = 0",
    "credit_utilization_avg": "used credit / credit limit, from POS data",
    "bureau_inquiry_count": "number of credit inquiries in last 6mo",
    "active_loans_count": "current active loans from bureau",
}
```

---

### Step 4: Train Models (`03_train_models.py`)

#### Model 1: Propensity Model
```
Target: propensity_target (1 = took loan or has intent signals, 0 = didn't)
Features: All cashflow + behavioral + intent features
Algorithm: XGBoost (binary classification)
Metric: AUC-ROC, Precision@30% (we want 30%+ conversion)
```

#### Model 2: Health Score Model
```
Target: Multi-output — 6 dimension scores (0-100 each)
  - income_stability_score
  - spending_discipline_score
  - cashflow_adequacy_score
  - debt_management_score
  - growth_trajectory_score
  - external_compliance_score

Features: All cashflow + behavioral + external features
Algorithm: XGBoost (multi-output regression) or 6 separate regressors
Labels: Computed from heuristic rules on features (self-supervised):
  - income_stability = f(income_regularity, income_growth, volatility)
  - spending_discipline = f(discretionary_ratio, large_txn_freq, ...)
  - etc.
```

#### Model 3: Default Prediction Model
```
Target: default_flag (1 = status B or D from Berka, 0 = status A or C)
Features: All cashflow + behavioral + stress + home_credit features
Algorithm: XGBoost (binary classification)
Metric: AUC-ROC (target: 0.90+), Recall at 30% threshold
```

---

### Step 5: Generate SHAP Explanations (`04_generate_shap.py`)

For each model, generate:
- Global feature importance (bar chart)
- Per-prediction SHAP values (waterfall chart for individual customers)
- Save SHAP values alongside predictions for the API to serve

```python
import shap
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)
# Save per-customer SHAP for API serving
```

---

### Step 6: Serve via FastAPI (`api/main.py`)

Endpoints:
```
GET  /api/customers                    → list all customers with scores
GET  /api/customers/{id}               → full profile + all scores
GET  /api/customers/{id}/propensity    → propensity score + SHAP
GET  /api/customers/{id}/health        → 6-dimension health card
GET  /api/customers/{id}/default       → PD score + stress timeline + SHAP
GET  /api/prospects                    → ranked prospect list (score > threshold)
GET  /api/early-warning               → accounts with PD spike
POST /api/agent/analyze/{id}           → trigger Strands agent reasoning
```

---

## Quick Validation Checklist

After running the pipeline, verify:
- [ ] Indianized transactions look realistic (₹ amounts, Indian merchants, UPI modes)
- [ ] Feature matrix has no NaN/inf values
- [ ] Propensity model AUC > 0.85
- [ ] Default model AUC > 0.85 (target 0.90)
- [ ] Health scores distribute reasonably (not all clustered at 50)
- [ ] SHAP explanations make intuitive sense (salary_regularity matters for income_stability, etc.)
- [ ] API serves all endpoints with < 200ms response time
- [ ] At least 3 "demo customers" with interesting stories (high propensity, deteriorating health, stress timeline)
