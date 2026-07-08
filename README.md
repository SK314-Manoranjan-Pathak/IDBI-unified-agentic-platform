# FinPulse — Unified Agentic Intelligence Platform for Banking

> **by ShellKode** | Built for IDBI Innovate 2026 & SBI Hackathon

A unified ML scoring platform that reads customer transaction behavior and produces three actionable intelligence signals — **Propensity**, **Financial Health**, and **Default Prediction** — powered by XGBoost, SHAP explainability, and a real-time FastAPI + Next.js dashboard.

---

## Table of Contents

- [Overview](#overview)
- [Problem Statements Addressed](#problem-statements-addressed)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Pipeline Execution](#pipeline-execution)
- [API Reference](#api-reference)
- [Frontend Dashboard](#frontend-dashboard)
- [Model Performance](#model-performance)
- [Demo Customers](#demo-customers)
- [License](#license)

---

## Overview

Every lending decision — who to lend to, how healthy they are, whether they'll default — is answered by the same underlying signal: **how people actually move money.** One shared feature layer (51 features) powers all three prediction heads.

| Signal | Business Question | Stakeholder |
|--------|-------------------|-------------|
| **Propensity Score** | "Who is likely to want a loan and what product?" | Sales / RM Team |
| **Financial Health Score** | "Is this NTC/NTB customer creditworthy?" | Underwriting / Credit |
| **Default Prediction (EWS)** | "Which existing borrowers are deteriorating?" | Risk / Collections |

---

## Problem Statements Addressed

### IDBI Innovate 2026

| PS | Problem | Solution |
|----|---------|----------|
| 2 | Low loan conversion due to traditional metrics | Propensity model identifies intent + capacity from transactions |
| 3 | NTC/NTB MSMEs lack documents for credit assessment | Health Score builds 6-dimension assessment from alternate data |
| 4 | Default prediction accuracy only 16-22% | Early Warning detects behavioral deterioration 12 months before default |

### SBI Hackathon (Agentic AI & Emerging Tech)

| Theme | Problem | Solution |
|-------|---------|----------|
| 1 | Identify, qualify, convert via personalized engagement | Prospect + Engagement agents qualify and convert |
| 2 | Contextual AI for digital service adoption | Behavioral nudges based on life events |
| 3 | Proactive interaction based on behaviors & life events | Full agent loop: detect → reason → act → learn |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RAW DATA (Master_data/)                            │
│   Berka CSVs  │  AgamiAI JSON  │  Home Credit CSVs  │  PaySim (optional)   │
└──────┬────────┴────────┬───────┴─────────┬──────────┴───────────────────────┘
       │                 │                  │
       ▼                 ▼                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  Phase 1: 01_indianize.py                                                    │
│  CZK→INR conversion · Indian categories/merchants · Intent injection (50)    │
│  MSME pattern injection (100) · Running balance recomputation                │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  Phase 2: 02_feature_engineering.py                                          │
│  51 features across 6 groups: Cashflow · Behavioral · Intent · Stress ·     │
│  External/MSME · Home Credit DPD enrichment                                  │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  Phase 3: 03_train_models.py                                                 │
│  Propensity (XGBoost binary) · Health Score (6×XGBRegressor) ·               │
│  Default Prediction (XGBoost binary) · 5-Fold CV                             │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  Phase 4: 04_generate_shap.py                                                │
│  Per-customer SHAP values · Global importance charts · Explainability CSVs   │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  Phase 5: api/main.py (FastAPI)                                              │
│  8 endpoints · Pre-loaded models · <10ms response · CORS enabled             │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  Phase 6: frontend/ (Next.js + Recharts)                                     │
│  5 views: Portfolio Overview · Customer Lookup · Prospect Assist ·            │
│  Health Card · Early Warning System                                          │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
IDBI-unified-agentic-platform/
│
├── Master_data/                     # Raw datasets (not committed to git)
│   ├── berka/                       # PKDD'99 Financial Dataset (Czech bank, sep=';')
│   │   ├── trans.csv                #   1,056,320 transactions
│   │   ├── loan.csv                 #   682 loans (A/B/C/D status)
│   │   ├── account.csv             #   4,500 accounts
│   │   ├── client.csv              #   5,369 clients
│   │   ├── disp.csv                #   Client-account relationships
│   │   ├── district.csv            #   77 regional demographics
│   │   ├── order.csv               #   6,471 standing orders
│   │   └── card.csv                #   892 credit cards
│   ├── train/                       # AgamiAI Indian Bank Statements (JSON)
│   ├── home-credit-default-risk/    # Kaggle Home Credit (DPD/bureau enrichment)
│   └── PS_2017.../                  # PaySim mobile money (UPI reference, optional)
│
├── scripts/                         # ML Pipeline (run in order)
│   ├── 01_indianize.py              #   Phase 1: Data ingestion + Indianization
│   ├── 02_feature_engineering.py    #   Phase 2: 51-feature matrix generation
│   ├── 03_train_models.py          #   Phase 3: XGBoost model training + CV
│   ├── 04_generate_shap.py         #   Phase 4: SHAP explanations + plots
│   └── validate_checklist.py       #   Validation: 7-point pipeline check
│
├── data/
│   ├── processed/                   # Pipeline outputs
│   │   ├── indianized_transactions.csv  # 1,061,611 Indianized transactions
│   │   ├── account_labels.csv          # Per-account labels (default, propensity, MSME)
│   │   ├── feature_matrix.csv          # 4,500 rows × 65 columns (51 features + labels)
│   │   ├── customer_profiles.csv       # Lightweight per-account summary
│   │   ├── health_labels.csv           # Self-supervised health scores (6 dims)
│   │   ├── home_credit_dpd_reference.csv # Real Home Credit aggregates
│   │   └── indian_context.json         # Extracted merchant/mode context from AgamiAI
│   └── models/                      # Trained model artifacts
│       ├── propensity_model.pkl     #   XGBoost binary classifier
│       ├── health_model.pkl         #   Dict of 6 XGBRegressors
│       ├── default_model.pkl        #   XGBoost binary classifier
│       ├── model_metadata.json      #   Metrics, feature columns, thresholds
│       ├── shap_propensity.csv      #   Per-customer SHAP values
│       ├── shap_default.csv         #   Per-customer SHAP values
│       ├── shap_health_*.csv        #   Per-dimension SHAP (6 files)
│       ├── shap_global_importance.json  # Top-20 features per model
│       └── plots/                   #   Global importance bar charts (PNG)
│
├── api/
│   └── main.py                      # FastAPI scoring service (8 endpoints)
│
├── frontend/                        # Next.js 16 + React 19 + Recharts dashboard
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx           #   Root layout (dark theme, metadata)
│   │   │   ├── page.tsx             #   Main page with tabbed navigation
│   │   │   └── globals.css          #   Global styles + CSS variables
│   │   ├── components/
│   │   │   ├── PortfolioOverview.tsx #   KPIs, risk pie chart, top prospects
│   │   │   ├── CustomerLookup.tsx   #   360° view, radar + SHAP charts
│   │   │   ├── ProspectList.tsx     #   Ranked prospects with threshold slider
│   │   │   ├── HealthCard.tsx       #   6-dimension radar + breakdown
│   │   │   └── EarlyWarning.tsx     #   Flagged accounts + SHAP drill-down
│   │   └── lib/
│   │       └── api.ts               #   API client + TypeScript interfaces
│   ├── next.config.ts               #   Rewrites /api/* → FastAPI backend
│   ├── package.json                 #   Dependencies (Next, React, Recharts, Tailwind)
│   └── postcss.config.mjs           #   PostCSS + Tailwind 4 configuration
│
├── run_pipeline.py                  # Master script — runs all 4 phases in one command
├── requirements.txt                 # Python dependencies (pinned versions)
├── DEMO_CUSTOMERS.md                # 3 curated demo customer narratives
├── ML_PIPELINE_DOCUMENTATION.md     # Comprehensive technical documentation
├── feature-engineering-README.md    # Dataset download guide + feature specs
├── idea.md                          # Business model + agent design + scenarios
├── diagrams.md                      # Architecture diagrams
└── .gitignore
```

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| ML Models | XGBoost | 3.1.2 |
| Explainability | SHAP | 0.50.0 |
| Data Processing | Pandas, NumPy | 2.3.3, 2.3.5 |
| ML Utilities | scikit-learn | 1.7.2 |
| API Backend | FastAPI + Uvicorn | 0.109.0, 0.41.0 |
| Frontend | Next.js + React | 16.2, 19.1 |
| Visualization | Recharts | 2.15.3 |
| Styling | Tailwind CSS | 4.1.10 |
| Language | TypeScript | 5.8.3 |
| Python | 3.10+ | — |

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Raw datasets placed in `Master_data/` (see [feature-engineering-README.md](feature-engineering-README.md) for download links)

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd IDBI-unified-agentic-platform

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

---

## Pipeline Execution

### One-Command Run (Recommended)

```bash
# Run the full pipeline (Phases 1-4)
python run_pipeline.py

# Run with validation checklist at the end
python run_pipeline.py --validate

# Resume from a specific phase (e.g., skip Indianization if already done)
python run_pipeline.py --from 2

# Run only a specific phase
python run_pipeline.py --only 3
```

### Individual Scripts (Manual)

Each script is idempotent with fixed seeds and can be run independently:

```bash
# Phase 1: Indianize raw Berka data → data/processed/indianized_transactions.csv
python scripts/01_indianize.py

# Phase 2: Feature engineering → data/processed/feature_matrix.csv (4,500 × 51 features)
python scripts/02_feature_engineering.py

# Phase 3: Train models → data/models/*.pkl
python scripts/03_train_models.py

# Phase 4: Generate SHAP → data/models/shap_*.csv + plots/
python scripts/04_generate_shap.py

# (Optional) Validate pipeline
python scripts/validate_checklist.py
```

### Start the Application

```bash
# Terminal 1: Start the API backend
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start the frontend
cd frontend
npm run dev
```

Access the dashboard at **http://localhost:3000**

---

## API Reference

Base URL: `http://localhost:8000`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/customers` | List customers with summary scores (paginated) |
| GET | `/api/customers/{id}` | Full profile + all scores for a customer |
| GET | `/api/customers/{id}/propensity` | Propensity score + predicted product + SHAP factors |
| GET | `/api/customers/{id}/health` | 6-dimension health card + per-dimension SHAP |
| GET | `/api/customers/{id}/default` | Default probability + stress level + SHAP factors |
| GET | `/api/prospects` | Ranked prospects (propensity > threshold, PD < 15%) |
| GET | `/api/early-warning` | Loan accounts with elevated default risk |
| POST | `/api/agent/analyze/{id}` | Agent-style reasoning summary with recommended action |

### Query Parameters

| Endpoint | Parameter | Default | Description |
|----------|-----------|---------|-------------|
| `/api/customers` | `limit` | 50 | Results per page (max 4500) |
| `/api/customers` | `offset` | 0 | Pagination offset |
| `/api/prospects` | `threshold` | 70.0 | Minimum propensity score |
| `/api/prospects` | `limit` | 50 | Max results |
| `/api/early-warning` | `threshold` | 15.0 | Minimum default probability % |
| `/api/early-warning` | `limit` | 50 | Max results |

### Example Response

```json
// GET /api/customers/2048/propensity
{
  "account_id": 2048,
  "propensity_score": 100.0,
  "predicted_product": "Auto Loan",
  "confidence": "High",
  "top_factors": [
    {"feature": "auto_dealer_txn_count_30d", "shap_value": 5.8996},
    {"feature": "discretionary_spend_ratio", "shap_value": 2.6457}
  ]
}
```

---

## Frontend Dashboard

The dashboard provides 5 modules accessible via a sidebar:

### 1. Portfolio Overview
- KPI cards: total customers, low/high risk counts, hot prospects
- Risk distribution pie chart (Green/Amber/Red)
- Top 15 prospects bar chart
- Early warning table with top stress factors

### 2. Customer Lookup (360° View)
- Search by Account ID
- Financial metrics (income, surplus, balance, loan status)
- Score cards: Propensity, Default Risk, Health Score
- 6-dimension Health Radar Chart
- SHAP waterfall for default risk drivers

### 3. Prospect Assist (PS2)
- Adjustable propensity threshold slider
- Ranked prospect table with product predictions
- Product mix breakdown bar chart

### 4. Financial Health Card (PS3)
- 6-dimension radar visualization
- Dimension breakdown with progress bars
- Per-dimension SHAP drivers
- Approve / Review / Decline recommendation

### 5. Early Warning System (PS4)
- PD alert threshold slider
- Flagged accounts table (sortable by risk)
- SHAP drill-down on click
- Intervention matrix (Level 1/2/3)

---

## Model Performance

| Model | Metric | Score | Target |
|-------|--------|-------|--------|
| Propensity | 5-Fold CV AUC-ROC | **0.9999** | > 0.85 |
| Default Prediction | 5-Fold CV AUC-ROC | **0.9992** | > 0.90 |
| Health Score (avg R²) | 5-Fold CV | **0.9944** | Reasonable distribution |

### Health Score Per-Dimension R²

| Dimension | R² |
|-----------|----|
| Income Stability | 0.9982 |
| Spending Discipline | 0.9891 |
| Cash Flow Adequacy | 0.9869 |
| Debt Management | 0.9962 |
| Growth Trajectory | 0.9975 |
| External Compliance | 0.9986 |

> **Note:** High scores are expected for PoC — propensity uses synthetically injected intent signals, and health labels are self-supervised. These validate the pipeline is correctly wired. Real-world deployment would see 0.85-0.94 range.

---

## Demo Customers

| Account | Persona | Key Signal | Use Case |
|---------|---------|------------|----------|
| **2048** | Salaried professional, auto shopper | Propensity 100/100, PD 0.3% | PS2 — Prospect identification |
| **2926** | MSME textile business (NTC) | Health Score 79.7, Approve | PS3 — Financial health card |
| **4462** | Existing borrower, deteriorating | PD 99.7%, Level 3 stress | PS4 — Early warning system |

See [DEMO_CUSTOMERS.md](DEMO_CUSTOMERS.md) for full narratives.

---

## Feature Engineering — 51 Features Across 6 Groups

| Group | Count | Purpose |
|-------|-------|---------|
| A. Cash Flow | 14 | Income/expense/surplus/balance dynamics |
| B. Behavioral | 9 | Merchant diversity, timing, channel mix |
| C. Intent Signals | 6 | Auto/property/wedding activity (Propensity) |
| D. Stress Indicators | 9 | EMI delays, balance breaches (Default) |
| E. External/MSME | 7 | GST, EPFO, revenue trends (Health) |
| F. Home Credit Enrichment | 7 | DPD, bureau inquiries, active loans |

See [ML_PIPELINE_DOCUMENTATION.md](ML_PIPELINE_DOCUMENTATION.md) for detailed feature descriptions and computation logic.

---

## Key Design Decisions

1. **XGBoost over Deep Learning** — Dataset is small (4,500 accounts). XGBoost dominates on tabular data and provides fast exact SHAP values.
2. **Self-supervised health labels** — No external health scores exist for NTC customers. Heuristic rules derive ground truth from features, then XGBoost learns the mapping.
3. **Pre-computed predictions** — All predictions are computed at API startup and served from memory for <10ms response times.
4. **SHAP for explainability** — Every prediction has per-feature attribution. Critical for RBI compliance (no black-box decisions).
5. **Shared feature layer** — One feature matrix feeds all three models. Reduces engineering overhead and ensures consistency.

---

## Future Enhancements

- **Strands Agents SDK** — Multi-agent system (Supervisor, Prospect, Health, Risk, Engagement agents) on AWS Bedrock AgentCore
- **Transaction Transformer** — Raw sequence modeling for temporal pattern detection
- **Account Aggregator integration** — Real-time AA data pull via Sahamati
- **Multilingual engagement** — Sarvam AI for 11 Indian languages
- **AgentCore Memory** — Semantic + episodic customer memory for personalized interactions
- **Real-time scoring** — EventBridge triggers for transaction-level re-scoring

---

## Documentation

| Document | Description |
|----------|-------------|
| [ML_PIPELINE_DOCUMENTATION.md](ML_PIPELINE_DOCUMENTATION.md) | Complete technical docs — features, models, validation |
| [feature-engineering-README.md](feature-engineering-README.md) | Dataset download links + feature specs |
| [DEMO_CUSTOMERS.md](DEMO_CUSTOMERS.md) | 3 curated demo customer narratives |
| [idea.md](idea.md) | Business model, agent design, user scenarios |
| [diagrams.md](diagrams.md) | Architecture diagrams |

---

## License

Proprietary — ShellKode. All rights reserved.
