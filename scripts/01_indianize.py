"""
01_indianize.py  —  Phase 1 of the IDBI ML pipeline.

Transforms the raw Czech Berka (PKDD'99) dataset into a realistic *Indianized*
transaction ledger, and extracts Indian-context assets from the AgamiAI Indian
Bank Statements. Also injects loan-intent signals (Propensity) and MSME/health
patterns (Health Score) as specified in feature-engineering-README.md.

INPUTS  (read-only):
  Master_data/berka/{trans,loan,account,client,disp,district}.csv   (sep=';')
  Master_data/train/India_Bank_Statement_Digital_Type{1,2}/*.json

OUTPUTS (data/processed/):
  indianized_transactions.csv   all txns (original + synthetic), Indianized
  account_labels.csv            per-account labels/tags (default, propensity, msme)
  indian_context.json           merchants / modes / INR ranges from AgamiAI

Design notes:
  * CZK -> INR at x3.5 (per README).
  * Balances are recomputed as a running signed cumulative sum per account so that
    injected synthetic transactions keep balances internally consistent.
  * Fully idempotent: fixed random seed, outputs overwritten on each run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
SEED = 42
CZK_TO_INR = 3.5

ROOT = Path(__file__).resolve().parents[1]
BERKA_DIR = ROOT / "Master_data" / "berka"
AGAMAI_DIR = ROOT / "Master_data" / "train"
OUT_DIR = ROOT / "data" / "processed"

TRANS_OUT = OUT_DIR / "indianized_transactions.csv"
LABELS_OUT = OUT_DIR / "account_labels.csv"
CONTEXT_OUT = OUT_DIR / "indian_context.json"

rng = np.random.default_rng(SEED)


def log(msg: str) -> None:
    print(f"[01_indianize] {msg}", flush=True)


# --------------------------------------------------------------------------- #
# Mappings (Czech -> Indian), per README
# --------------------------------------------------------------------------- #
# k_symbol -> Indian category
KSYMBOL_CATEGORY = {
    "POJISTNE": "Insurance Premium",
    "SLUZBY": "Service Charge",
    "UROK": "Interest Credit",
    "SANKC. UROK": "Penalty Interest",
    "SIPO": "Utility Bill",
    "DUCHOD": "Salary",
    "UVER": "EMI Payment",
}

# operation -> Indian payment mode
OPERATION_MODE = {
    "VYBER KARTOU": "Card",
    "VKLAD": "Cash Deposit",
    "PREVOD Z UCTU": "NEFT/IMPS",
    "VYBER": "ATM Withdrawal",
    "PREVOD NA UCET": "UPI/NEFT",
    "": "Other",
}

# Indian merchant pools by category
MERCHANTS = {
    "Salary": ["TCS Ltd", "Infosys Ltd", "Wipro Ltd", "HCL Tech", "Reliance Ind",
               "Tech Mahindra", "Accenture India", "Cognizant India"],
    "Utility Bill": ["BESCOM", "Jio Postpaid", "Airtel", "BWSSB", "Indane Gas",
                     "Tata Power", "Mahanagar Gas"],
    "EMI Payment": ["HDFC Bank EMI", "ICICI EMI", "Bajaj Finserv EMI",
                    "Axis Bank EMI", "SBI Home Loan EMI"],
    "Insurance Premium": ["LIC Premium", "HDFC Life", "ICICI Prudential",
                          "SBI Life", "Max Life"],
    "SIP Investment": ["SBI MF SIP", "HDFC MF SIP", "Axis MF SIP", "Groww SIP"],
    "Interest Credit": ["Savings Interest"],
    "Penalty Interest": ["Min Balance Penalty"],
    "Service Charge": ["Bank Service Charge"],
    "Cash Deposit": ["Self Cash Deposit", "Branch Deposit"],
    "ATM Withdrawal": ["ATM Withdrawal"],
    "Card Spend": ["Amazon India", "Flipkart", "Swiggy", "Zomato", "BigBasket",
                   "DMart", "Reliance Fresh", "Myntra", "Croma"],
}

# Counterparty pool for generic bank transfers (augmented by AgamiAI extraction)
DEFAULT_TRANSFER_NAMES = [
    "Rajesh Kumar", "Priya Sharma", "Amit Patel", "Sneha Reddy", "Vikram Singh",
    "Anjali Gupta", "Suresh Nair", "Kavya Iyer", "Global Traders Pvt Ltd",
    "Sunrise Enterprises", "Metro Distributors", "Sri Balaji Traders",
]

# Intent-signal merchant pools (Propensity — PS2)
INTENT_MERCHANTS = {
    "auto": ["Maruti Suzuki Arena", "Hyundai Showroom", "Tata Motors Showroom",
             "CarDekho Premium", "Maruti Suzuki Nexa", "Mahindra Auto"],
    "property": ["MagicBricks", "99acres Premium", "NoBroker", "Housing.com"],
    "wedding": ["Taj Banquets", "Tanishq Jewellers", "FNP Weddings",
                "Bombay Catering Services", "Meena Bazaar"],
    "travel": ["MakeMyTrip", "IRCTC", "IndiGo Airlines", "Yatra"],
    "education": ["DPS School Fee", "Byju's", "Unacademy", "Aakash Institute"],
    "insurance_cmp": ["PolicyBazaar", "Coverfox"],
}

# MSME synthetic pools (Health Score — PS3)
B2B_VENDORS = ["Reliance Retail", "Tata Steel", "Adani Wilmar", "ITC Ltd",
               "Vendor Settlement", "Wholesale Mandi", "Textile Suppliers Co",
               "Raw Material Traders"]


# --------------------------------------------------------------------------- #
# Step 1 — Load raw Berka
# --------------------------------------------------------------------------- #
def parse_berka_date(series: pd.Series) -> pd.Series:
    """Berka dates are YYMMDD integers in 1993-1998 -> datetime."""
    s = series.astype("Int64").astype(str).str.zfill(6)
    return pd.to_datetime(s, format="%y%m%d", errors="coerce")


def load_berka() -> dict:
    log("Loading raw Berka CSVs (sep=';') ...")
    trans = pd.read_csv(
        BERKA_DIR / "trans.csv", sep=";",
        dtype={"type": str, "operation": str, "k_symbol": str,
               "bank": str, "account": str},
        keep_default_na=False,
    )
    # numeric coercions (empty strings -> NaN -> 0 where appropriate)
    for col in ("amount", "balance"):
        trans[col] = pd.to_numeric(trans[col], errors="coerce")
    trans["date"] = parse_berka_date(trans["date"])
    trans["k_symbol"] = trans["k_symbol"].str.strip()  # ' ' -> ''
    trans["operation"] = trans["operation"].str.strip()

    loan = pd.read_csv(BERKA_DIR / "loan.csv", sep=";",
                       dtype={"status": str}, keep_default_na=False)
    loan["date"] = parse_berka_date(loan["date"])
    for col in ("amount", "payments"):
        loan[col] = pd.to_numeric(loan[col], errors="coerce")

    account = pd.read_csv(BERKA_DIR / "account.csv", sep=";",
                          dtype={"frequency": str}, keep_default_na=False)
    account["date"] = parse_berka_date(account["date"])

    disp = pd.read_csv(BERKA_DIR / "disp.csv", sep=";",
                       dtype={"type": str}, keep_default_na=False)
    client = pd.read_csv(BERKA_DIR / "client.csv", sep=";", keep_default_na=False)
    district = pd.read_csv(BERKA_DIR / "district.csv", sep=";", keep_default_na=False)

    log(f"  trans={len(trans):,}  loan={len(loan):,}  account={len(account):,}  "
        f"client={len(client):,}  disp={len(disp):,}  district={len(district):,}")
    return {"trans": trans, "loan": loan, "account": account,
            "disp": disp, "client": client, "district": district}


# --------------------------------------------------------------------------- #
# Step 2 — Extract Indian context from AgamiAI digital statements
# --------------------------------------------------------------------------- #
_MODE_TOKENS = ["UPI", "NEFT", "RTGS", "IMPS", "CASH", "ATM", "POS", "ACH"]
_STOP_TOKENS = {
    "CR", "DR", "NEFT", "RTGS", "IMPS", "UPI", "CASH", "BNA", "SELF", "ACH",
    "POS", "ATM", "PAID", "CHQ", "MICR", "INWARD", "CLEARING", "NONE", "LTD",
    "BANK", "INDIA", "PVT", "TO", "FROM", "TRANSFER", "PAYMENT",
}


def _clean_merchant_token(desc: str) -> str | None:
    """Pull a plausible merchant/counterparty name out of a narration string."""
    parts = [p.strip() for p in desc.replace("/", "-").split("-")]
    best = None
    for p in parts:
        letters = "".join(ch for ch in p if ch.isalpha() or ch == " ").strip()
        if len(letters) < 4:
            continue
        toks = [t for t in letters.upper().split() if t not in _STOP_TOKENS]
        if not toks:
            continue
        candidate = " ".join(w.capitalize() for w in " ".join(toks).split())
        if len(candidate) >= 4:
            best = candidate  # keep the last good candidate (usually the name)
    return best


def extract_indian_context() -> dict:
    log("Extracting Indian context from AgamiAI digital statements ...")
    merchants: dict[str, int] = {}
    mode_counts: dict[str, int] = {t: 0 for t in _MODE_TOKENS}
    credit_amounts: list[float] = []
    debit_amounts: list[float] = []
    files_read = 0

    for sub in ("India_Bank_Statement_Digital_Type1",
                "India_Bank_Statement_Digital_Type2"):
        folder = AGAMAI_DIR / sub
        if not folder.exists():
            continue
        for fp in sorted(folder.glob("*.json")):
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
            except Exception:
                continue
            files_read += 1
            for t in data.get("transactions", []):
                desc = str(t.get("description", ""))
                up = desc.upper()
                for tok in _MODE_TOKENS:
                    if tok in up:
                        mode_counts[tok] += 1
                name = _clean_merchant_token(desc)
                if name:
                    merchants[name] = merchants.get(name, 0) + 1
                if t.get("credit") not in (None, "", 0):
                    try:
                        credit_amounts.append(float(t["credit"]))
                    except (TypeError, ValueError):
                        pass
                if t.get("debit") not in (None, "", 0):
                    try:
                        debit_amounts.append(float(t["debit"]))
                    except (TypeError, ValueError):
                        pass

    top_merchants = sorted(merchants.items(), key=lambda x: x[1], reverse=True)
    top_names = [m for m, _ in top_merchants[:200]]

    def _pct(arr):
        if not arr:
            return {}
        a = np.array(arr, dtype=float)
        return {
            "count": int(a.size),
            "min": float(np.min(a)), "p25": float(np.percentile(a, 25)),
            "median": float(np.median(a)), "p75": float(np.percentile(a, 75)),
            "p95": float(np.percentile(a, 95)), "max": float(np.max(a)),
            "mean": float(np.mean(a)),
        }

    context = {
        "files_read": files_read,
        "top_merchants": top_names,
        "payment_mode_counts": mode_counts,
        "credit_amount_stats_inr": _pct(credit_amounts),
        "debit_amount_stats_inr": _pct(debit_amounts),
    }
    log(f"  parsed {files_read} statements, {len(top_names)} distinct merchant names")
    return context


# --------------------------------------------------------------------------- #
# Step 3 — Indianize the Berka transactions
# --------------------------------------------------------------------------- #
def derive_category(row_ksym: str, row_op: str, is_credit: bool) -> str:
    if row_ksym in KSYMBOL_CATEGORY:
        return KSYMBOL_CATEGORY[row_ksym]
    # fall back on operation
    if row_op == "VKLAD":
        return "Cash Deposit"
    if row_op == "VYBER KARTOU":
        return "Card Spend"
    if row_op == "VYBER":
        return "ATM Withdrawal"
    if row_op in ("PREVOD Z UCTU", "PREVOD NA UCET"):
        return "Transfer Credit" if is_credit else "Transfer Payment"
    # no operation, no k_symbol
    return "Interest Credit" if is_credit else "Misc Payment"


def indianize(trans: pd.DataFrame, context: dict) -> pd.DataFrame:
    log("Indianizing Berka transactions ...")
    df = trans.copy()

    # credit/debit + signed amount
    df["is_credit"] = df["type"].eq("PRIJEM")
    df["amount_inr"] = (df["amount"].fillna(0.0) * CZK_TO_INR).round(2)
    df["direction"] = np.where(df["is_credit"], "credit", "debit")

    # payment mode
    df["payment_mode"] = df["operation"].map(OPERATION_MODE).fillna("Other")
    df.loc[(df["payment_mode"] == "Other") & df["is_credit"], "payment_mode"] = "NEFT/IMPS"
    df.loc[(df["payment_mode"] == "Other") & ~df["is_credit"], "payment_mode"] = "UPI/NEFT"

    # category (vectorized via unique combos)
    combo = df[["k_symbol", "operation", "is_credit"]].drop_duplicates()
    combo["category"] = combo.apply(
        lambda r: derive_category(r["k_symbol"], r["operation"], r["is_credit"]), axis=1)
    df = df.merge(combo, on=["k_symbol", "operation", "is_credit"], how="left")

    # merchant assignment
    df["merchant"] = _assign_merchants(df, context)

    df["is_synthetic"] = False
    df["synthetic_purpose"] = ""
    return df


def _assign_merchants(df: pd.DataFrame, context: dict) -> np.ndarray:
    """Assign an Indian merchant/counterparty per transaction row."""
    transfer_names = list(dict.fromkeys(
        (context.get("top_merchants") or []) + DEFAULT_TRANSFER_NAMES))
    out = np.empty(len(df), dtype=object)
    out[:] = ""

    # consistent salary employer per account
    salary_mask = df["category"].eq("Salary").to_numpy()
    if salary_mask.any():
        accts = df.loc[salary_mask, "account_id"].unique()
        emp_pool = MERCHANTS["Salary"]
        emp_map = {a: emp_pool[int(rng.integers(len(emp_pool)))] for a in accts}
        out[salary_mask] = df.loc[salary_mask, "account_id"].map(emp_map).to_numpy()

    cat = df["category"].to_numpy()
    for category, pool in MERCHANTS.items():
        if category == "Salary":
            continue
        m = cat == category
        n = int(m.sum())
        if n:
            out[m] = rng.choice(pool, size=n)

    for category in ("Transfer Credit", "Transfer Payment", "Misc Payment"):
        m = cat == category
        n = int(m.sum())
        if n:
            out[m] = rng.choice(transfer_names, size=n)

    # anything still blank -> generic
    blank = out == ""
    if blank.any():
        out[blank] = "Misc Counterparty"
    return out


# --------------------------------------------------------------------------- #
# Step 4 — Inject intent signals (Propensity — PS2)
# --------------------------------------------------------------------------- #
def _new_rows(records: list[dict]) -> pd.DataFrame:
    return pd.DataFrame.from_records(records)


def inject_intent(df: pd.DataFrame, eligible_accounts: np.ndarray,
                  next_trans_id: int) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    """Add auto/property/personal loan intent transactions to 50 accounts."""
    log("Injecting loan-intent signals for 50 accounts ...")
    chosen = rng.choice(eligible_accounts, size=50, replace=False)
    auto, prop, pers = chosen[:20], chosen[20:35], chosen[35:50]

    # per-account last transaction date (anchor)
    last_date = df.groupby("account_id")["date"].max()

    plans = [
        (auto, "auto", "Auto Loan", 30, (2000, 8000)),
        (prop, "property", "Home Loan", 45, (1500, 5000)),
        (pers, "wedding", "Personal Loan", 30, (12000, 60000)),
    ]
    new_records = []
    tag_rows = []
    tid = next_trans_id
    for accts, pool_key, product, window, amt_range in plans:
        pool = INTENT_MERCHANTS[pool_key]
        for acc in accts:
            anchor = last_date.get(acc, pd.Timestamp("1998-12-31"))
            n_txn = int(rng.integers(3, 6))  # 3..5
            for _ in range(n_txn):
                day_offset = int(rng.integers(0, window))
                amt = round(float(rng.uniform(*amt_range)), 2)
                new_records.append({
                    "trans_id": tid, "account_id": acc,
                    "date": anchor - pd.Timedelta(days=day_offset),
                    "type": "VYDAJ", "operation": "PREVOD NA UCET",
                    "amount": amt / CZK_TO_INR, "balance": np.nan, "k_symbol": "",
                    "bank": "", "account": "", "is_credit": False,
                    "amount_inr": amt, "direction": "debit",
                    "payment_mode": "UPI/NEFT",
                    "category": f"Intent-{product}",
                    "merchant": pool[int(rng.integers(len(pool)))],
                    "is_synthetic": True, "synthetic_purpose": f"intent_{pool_key}",
                })
                tid += 1
            # one insurance-comparison signal for auto shoppers
            if pool_key == "auto" and rng.random() < 0.5:
                new_records.append({
                    "trans_id": tid, "account_id": acc,
                    "date": anchor - pd.Timedelta(days=int(rng.integers(0, window))),
                    "type": "VYDAJ", "operation": "VYBER KARTOU",
                    "amount": 500 / CZK_TO_INR, "balance": np.nan, "k_symbol": "",
                    "bank": "", "account": "", "is_credit": False,
                    "amount_inr": 500.0, "direction": "debit", "payment_mode": "Card",
                    "category": "Intent-Insurance", "merchant": "PolicyBazaar",
                    "is_synthetic": True, "synthetic_purpose": "intent_insurance_cmp",
                })
                tid += 1
            tag_rows.append({"account_id": acc, "propensity_target": 1,
                             "intent_product": product})

    new_df = _new_rows(new_records)
    tags = pd.DataFrame(tag_rows)
    log(f"  added {len(new_df):,} intent transactions across {len(chosen)} accounts")
    return new_df, tags, tid


# --------------------------------------------------------------------------- #
# Step 5 — Inject MSME / health patterns (Health Score — PS3)
# --------------------------------------------------------------------------- #
def inject_msme(df: pd.DataFrame, eligible_accounts: np.ndarray,
                next_trans_id: int) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    """Add irregular revenue + GST + EPFO patterns to 100 MSME accounts."""
    log("Injecting MSME/health patterns for 100 accounts ...")
    chosen = rng.choice(eligible_accounts, size=100, replace=False)
    quality = (["healthy"] * 60) + (["borderline"] * 25) + (["unhealthy"] * 15)
    rng.shuffle(quality)

    last_date = df.groupby("account_id")["date"].max()
    new_records = []
    tag_rows = []
    tid = next_trans_id

    # quality -> parameters
    q_params = {
        "healthy":    dict(rev_base=(300000, 600000), rev_var=0.15, gst_skip=0.0,
                           epfo_skip=0.0, employees=(4, 8)),
        "borderline": dict(rev_base=(150000, 350000), rev_var=0.35, gst_skip=0.25,
                           epfo_skip=0.15, employees=(2, 5)),
        "unhealthy":  dict(rev_base=(80000, 200000), rev_var=0.60, gst_skip=0.5,
                           epfo_skip=0.4, employees=(1, 3)),
    }

    for acc, q in zip(chosen, quality):
        p = q_params[q]
        anchor = last_date.get(acc, pd.Timestamp("1998-12-31"))
        n_emp = int(rng.integers(p["employees"][0], p["employees"][1] + 1))
        rev_lo, rev_hi = p["rev_base"]
        base_rev = float(rng.uniform(rev_lo, rev_hi))

        # 12 months of irregular business revenue (credits) + EPFO + quarterly GST
        for m in range(12):
            month_anchor = anchor - pd.DateOffset(months=(11 - m))
            # irregular revenue: 2-4 credits per month with variance
            seasonal = 0.7 if month_anchor.month in (6, 7) else 1.0  # monsoon dip
            for _ in range(int(rng.integers(2, 5))):
                amt = round(base_rev / 3 * seasonal *
                            (1 + float(rng.normal(0, p["rev_var"]))), 2)
                amt = max(amt, 1000.0)
                new_records.append(_msme_row(
                    tid, acc, month_anchor - pd.Timedelta(days=int(rng.integers(0, 27))),
                    "PRIJEM", "PREVOD Z UCTU", amt, True, "NEFT/IMPS",
                    "Business Revenue", B2B_VENDORS[int(rng.integers(len(B2B_VENDORS)))],
                    "msme_revenue"))
                tid += 1
            # EPFO monthly (fixed small debit) unless skipped
            if rng.random() >= p["epfo_skip"]:
                epfo_amt = round(n_emp * float(rng.uniform(1800, 5000)), 2)
                new_records.append(_msme_row(
                    tid, acc, month_anchor - pd.Timedelta(days=5),
                    "VYDAJ", "PREVOD NA UCET", epfo_amt, False, "UPI/NEFT",
                    "EPFO Contribution", "EPFO", "msme_epfo"))
                tid += 1
            # quarterly GST outflow
            if m % 3 == 2 and rng.random() >= p["gst_skip"]:
                gst_amt = round(base_rev * float(rng.uniform(0.05, 0.12)), 2)
                new_records.append(_msme_row(
                    tid, acc, month_anchor - pd.Timedelta(days=3),
                    "VYDAJ", "PREVOD NA UCET", gst_amt, False, "UPI/NEFT",
                    "GST Payment", "GST Portal", "msme_gst"))
                tid += 1

        tag_rows.append({"account_id": acc, "msme_flag": 1,
                         "health_quality": q, "employee_count": n_emp})

    new_df = _new_rows(new_records)
    tags = pd.DataFrame(tag_rows)
    log(f"  added {len(new_df):,} MSME transactions across {len(chosen)} accounts")
    return new_df, tags, tid


def _msme_row(tid, acc, date, ttype, op, amt_inr, is_credit, mode, cat, merch, purpose):
    return {
        "trans_id": tid, "account_id": acc, "date": date, "type": ttype,
        "operation": op, "amount": amt_inr / CZK_TO_INR, "balance": np.nan,
        "k_symbol": "", "bank": "", "account": "", "is_credit": is_credit,
        "amount_inr": amt_inr, "direction": "credit" if is_credit else "debit",
        "payment_mode": mode, "category": cat, "merchant": merch,
        "is_synthetic": True, "synthetic_purpose": purpose,
    }


# --------------------------------------------------------------------------- #
# Step 6 — Recompute running balances (keeps synthetic rows consistent)
# --------------------------------------------------------------------------- #
def recompute_balances(df: pd.DataFrame) -> pd.DataFrame:
    log("Recomputing running balances per account ...")
    df = df.sort_values(["account_id", "date", "trans_id"]).reset_index(drop=True)
    signed = np.where(df["is_credit"].to_numpy(), df["amount_inr"].to_numpy(),
                      -df["amount_inr"].to_numpy())
    df["signed_amount_inr"] = signed
    df["balance_inr"] = (df.groupby("account_id")["signed_amount_inr"]
                         .cumsum().round(2))
    return df


# --------------------------------------------------------------------------- #
# Step 7 — Build per-account labels/tags
# --------------------------------------------------------------------------- #
def build_labels(berka: dict, intent_tags: pd.DataFrame,
                 msme_tags: pd.DataFrame) -> pd.DataFrame:
    log("Building account_labels ...")
    account = berka["account"][["account_id", "district_id"]].copy()

    loan = berka["loan"].copy()
    loan["default_flag"] = loan["status"].isin(["B", "D"]).astype(int)
    loan_agg = loan[["account_id", "loan_id", "amount", "duration",
                     "payments", "status", "default_flag"]].rename(
        columns={"amount": "loan_amount", "duration": "loan_duration",
                 "payments": "loan_payments", "status": "loan_status"})

    labels = account.merge(loan_agg, on="account_id", how="left")
    labels["has_loan"] = labels["loan_id"].notna().astype(int)

    labels = labels.merge(intent_tags, on="account_id", how="left")
    labels = labels.merge(msme_tags, on="account_id", how="left")
    labels["propensity_target"] = labels["propensity_target"].fillna(0).astype(int)
    labels["intent_product"] = labels["intent_product"].fillna("")
    labels["msme_flag"] = labels["msme_flag"].fillna(0).astype(int)
    labels["health_quality"] = labels["health_quality"].fillna("")
    labels["employee_count"] = labels["employee_count"].fillna(0).astype(int)
    return labels


# --------------------------------------------------------------------------- #
# Step 8 — Validation
# --------------------------------------------------------------------------- #
def validate(df: pd.DataFrame, labels: pd.DataFrame) -> None:
    log("Validating outputs ...")
    problems = []

    num_cols = ["amount_inr", "balance_inr", "signed_amount_inr"]
    for c in num_cols:
        if not np.isfinite(df[c].to_numpy()).all():
            problems.append(f"non-finite values in {c}")
    if df["merchant"].isna().any() or (df["merchant"] == "").any():
        problems.append("blank merchant values present")
    if df["category"].isna().any():
        problems.append("null category values present")
    if df["date"].isna().any():
        problems.append("unparsed dates present")

    # sanity: credit amounts should have realistic INR spread
    med_credit = df.loc[df["is_credit"], "amount_inr"].median()
    if not (100 <= med_credit <= 5_000_000):
        problems.append(f"median credit INR looks off: {med_credit:,.0f}")

    if problems:
        log("VALIDATION FAILED:")
        for p in problems:
            log(f"   - {p}")
        raise SystemExit(1)

    # ----- summary report -----
    orig = int((~df["is_synthetic"]).sum())
    synth = int(df["is_synthetic"].sum())
    log("VALIDATION PASSED")
    log(f"  transactions total       : {len(df):,}  (original {orig:,} + synthetic {synth:,})")
    log(f"  distinct accounts        : {df['account_id'].nunique():,}")
    log(f"  date range               : {df['date'].min().date()} -> {df['date'].max().date()}")
    log(f"  median credit / debit INR: {med_credit:,.0f} / "
        f"{df.loc[~df['is_credit'],'amount_inr'].median():,.0f}")
    log("  payment mode distribution:")
    for mode, cnt in df["payment_mode"].value_counts().items():
        log(f"     {mode:<15} {cnt:>10,}")
    log("  top categories:")
    for cat, cnt in df["category"].value_counts().head(12).items():
        log(f"     {cat:<22} {cnt:>10,}")
    log("  labels:")
    log(f"     accounts w/ loan       : {int(labels['has_loan'].sum()):,}")
    log(f"     default=1 (B/D)        : {int(labels['default_flag'].fillna(0).sum()):,}")
    log(f"     propensity_target=1    : {int(labels['propensity_target'].sum()):,}")
    log(f"     msme_flag=1            : {int(labels['msme_flag'].sum()):,}")
    hq = labels.loc[labels['msme_flag'] == 1, 'health_quality'].value_counts()
    log(f"     msme quality split     : {dict(hq)}")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not BERKA_DIR.exists():
        log(f"ERROR: {BERKA_DIR} not found."); raise SystemExit(1)

    berka = load_berka()
    context = extract_indian_context()

    df = indianize(berka["trans"], context)

    # eligible accounts = those with >=1 year of history (stable anchors)
    span = berka["trans"].groupby("account_id")["date"].agg(["min", "max"])
    span["days"] = (span["max"] - span["min"]).dt.days
    eligible = span.index[span["days"] >= 365].to_numpy()
    log(f"Eligible accounts for injection (>=365 days history): {len(eligible):,}")

    next_id = int(df["trans_id"].max()) + 1
    intent_df, intent_tags, next_id = inject_intent(df, eligible, next_id)

    # MSME accounts must be disjoint from intent accounts
    intent_accts = set(intent_tags["account_id"])
    msme_eligible = np.array([a for a in eligible if a not in intent_accts])
    msme_df, msme_tags, next_id = inject_msme(df, msme_eligible, next_id)

    df = pd.concat([df, intent_df, msme_df], ignore_index=True)
    df = recompute_balances(df)

    labels = build_labels(berka, intent_tags, msme_tags)

    # ----- write outputs -----
    col_order = ["trans_id", "account_id", "date", "direction", "payment_mode",
                 "category", "merchant", "amount_inr", "balance_inr",
                 "signed_amount_inr", "type", "operation", "k_symbol",
                 "is_synthetic", "synthetic_purpose"]
    df_out = df[col_order].copy()
    df_out["date"] = df_out["date"].dt.strftime("%Y-%m-%d")

    log(f"Writing {TRANS_OUT.name} ...")
    df_out.to_csv(TRANS_OUT, index=False)
    log(f"Writing {LABELS_OUT.name} ...")
    labels.to_csv(LABELS_OUT, index=False)
    log(f"Writing {CONTEXT_OUT.name} ...")
    CONTEXT_OUT.write_text(json.dumps(context, indent=2), encoding="utf-8")

    validate(df, labels)
    log("Phase 1 complete.")


if __name__ == "__main__":
    main()
