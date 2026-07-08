"""
02_feature_engineering.py  —  Phase 2 of the IDBI ML pipeline.

Builds the per-customer (per-account) feature matrix from the Indianized Berka
ledger produced in Phase 1, across the feature groups defined in
feature-engineering-README.md:

  A. Cash-flow features        (income/expense/surplus/balance dynamics)
  B. Behavioral features       (merchant diversity, timing, channel mix)
  C. Intent-signal features    (auto/property/wedding — Propensity)
  D. Stress-indicator features (salary/EMI delays, balance breaches — Default)
  E. External / MSME features  (GST/EPFO/revenue — Health Score)
  F. Home-Credit enrichment    (DPD / bureau aggregates — see NOTE below)

NOTE on group F: Home Credit is a *different customer population* with no shared
key to Berka. We therefore compute real per-applicant DPD/bureau aggregates from
Home Credit and attach them to Berka accounts as LABEL-INDEPENDENT enrichment
(random seeded sampling from the real distributions). These `hc_*` columns carry
realistic values but are not linked to a specific Berka customer and must not be
treated as leakage. A standalone reference table is also written.

INPUTS  (data/processed/):
  indianized_transactions.csv, account_labels.csv
INPUTS  (Master_data/home-credit-default-risk/):
  installments_payments.csv, bureau.csv

OUTPUTS (data/processed/):
  feature_matrix.csv            one row per account, all features + labels
  customer_profiles.csv         lightweight human-readable per-account profile
  home_credit_dpd_reference.csv real Home Credit per-applicant aggregates

Idempotent: fixed seed, outputs overwritten.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
HC_DIR = ROOT / "Master_data" / "home-credit-default-risk"

TRANS_IN = PROC / "indianized_transactions.csv"
LABELS_IN = PROC / "account_labels.csv"
FEATURES_OUT = PROC / "feature_matrix.csv"
PROFILES_OUT = PROC / "customer_profiles.csv"
HC_REF_OUT = PROC / "home_credit_dpd_reference.csv"

rng = np.random.default_rng(SEED)

# category groupings
DISCRETIONARY = {"Card Spend", "Intent-Auto Loan", "Intent-Home Loan",
                 "Intent-Personal Loan", "Intent-Insurance"}
RECURRING = {"EMI Payment", "Insurance Premium", "Utility Bill",
             "SIP Investment", "EPFO Contribution"}
CASH_MODES = {"Cash Deposit", "ATM Withdrawal"}
DIGITAL_MODES = {"NEFT/IMPS", "UPI/NEFT", "Card"}
MIN_BAL_THRESHOLD = 5000.0  # INR


def log(msg: str) -> None:
    print(f"[02_features] {msg}", flush=True)


def _slope(y: np.ndarray) -> float:
    y = np.asarray(y, dtype=float)
    if y.size < 2 or np.allclose(y, y[0]):
        return 0.0
    x = np.arange(y.size, dtype=float)
    return float(np.polyfit(x, y, 1)[0])


def _safe_div(a: float, b: float, default: float = 0.0) -> float:
    return float(a) / float(b) if b else default


# --------------------------------------------------------------------------- #
# Load
# --------------------------------------------------------------------------- #
def load_transactions() -> pd.DataFrame:
    log("Loading indianized transactions ...")
    df = pd.read_csv(
        TRANS_IN,
        dtype={"account_id": "int64", "direction": "category",
               "payment_mode": "category", "category": "category",
               "merchant": str, "synthetic_purpose": str},
        parse_dates=["date"],
    )
    df["is_credit"] = df["direction"].eq("credit")
    df["ym"] = df["date"].dt.to_period("M")
    df["weekday"] = df["date"].dt.weekday
    df["credit_amt"] = np.where(df["is_credit"], df["amount_inr"], 0.0)
    df["debit_amt"] = np.where(~df["is_credit"], df["amount_inr"], 0.0)
    log(f"  {len(df):,} rows, {df['account_id'].nunique():,} accounts")
    return df


# --------------------------------------------------------------------------- #
# Monthly aggregation -> cash-flow features
# --------------------------------------------------------------------------- #
def cashflow_features(df: pd.DataFrame, asof: pd.Series) -> pd.DataFrame:
    log("Computing cash-flow features (monthly aggregation) ...")
    monthly = (df.groupby(["account_id", "ym"], observed=True)
               .agg(credit_sum=("credit_amt", "sum"),
                    debit_sum=("debit_amt", "sum"),
                    txn_count=("trans_id", "size"),
                    min_balance=("balance_inr", "min"))
               .reset_index())
    monthly["surplus"] = monthly["credit_sum"] - monthly["debit_sum"]
    monthly = monthly.sort_values(["account_id", "ym"])

    rows = []
    for acc, g in monthly.groupby("account_id", sort=False):
        credit = g["credit_sum"].to_numpy()
        surplus = g["surplus"].to_numpy()
        minbal = g["min_balance"].to_numpy()
        n = len(g)
        inc_mean = float(credit.mean()) if n else 0.0
        # income growth: last 3 vs previous 3 months
        if n >= 6:
            growth = _safe_div(credit[-3:].mean(), credit[-6:-3].mean(), 1.0)
        elif n >= 2:
            growth = _safe_div(credit[-1], credit[0], 1.0)
        else:
            growth = 1.0
        rows.append({
            "account_id": acc,
            "monthly_income_avg": inc_mean,
            "monthly_expense_avg": float(g["debit_sum"].mean()),
            "monthly_surplus_avg": float(surplus.mean()),
            "surplus_volatility": float(surplus.std(ddof=0)),
            "income_regularity": _safe_div(credit.std(ddof=0), inc_mean, 0.0),
            "income_growth_rate": growth,
            "min_balance_trend": _slope(minbal[-12:]),
            "transaction_count_monthly": float(g["txn_count"].mean()),
            "active_months": n,
        })
    cf = pd.DataFrame(rows)

    # balance-level features (per-transaction balance)
    bal = (df.groupby("account_id")
           .agg(balance_volatility=("balance_inr", lambda s: float(s.std(ddof=0))),
                balance_latest=("balance_inr", "last"),
                overdraft_frequency=("balance_inr", lambda s: int((s < 0).sum())),
                balance_below_min_count=("balance_inr",
                                         lambda s: int((s < MIN_BAL_THRESHOLD).sum())))
           .reset_index())
    cf = cf.merge(bal, on="account_id", how="left")

    # min balance in last 30 days (relative to each account's as-of date)
    df2 = df[["account_id", "date", "balance_inr"]].merge(
        asof.rename("asof"), left_on="account_id", right_index=True, how="left")
    recent = df2[df2["date"] >= (df2["asof"] - pd.Timedelta(days=30))]
    mb30 = recent.groupby("account_id")["balance_inr"].min().rename("min_balance_30d")
    cf = cf.merge(mb30, on="account_id", how="left")
    cf["min_balance_30d"] = cf["min_balance_30d"].fillna(cf["balance_latest"])
    return cf


# --------------------------------------------------------------------------- #
# Behavioral features
# --------------------------------------------------------------------------- #
def behavioral_features(df: pd.DataFrame) -> pd.DataFrame:
    log("Computing behavioral features ...")
    total = df.groupby("account_id").size().rename("n_txn")
    credits = df.groupby("account_id")["is_credit"].sum().rename("n_credit")
    uniq_m = df.groupby("account_id")["merchant"].nunique().rename("unique_merchants")

    debit = df[~df["is_credit"]]
    debit_total = debit.groupby("account_id")["amount_inr"].sum().rename("debit_total")
    disc = (debit[debit["category"].isin(DISCRETIONARY)]
            .groupby("account_id")["amount_inr"].sum().rename("disc_spend"))
    wk = (debit[debit["weekday"] >= 5]
          .groupby("account_id")["amount_inr"].sum().rename("weekend_spend"))

    cash_txn = (df[df["payment_mode"].isin(CASH_MODES)]
                .groupby("account_id").size().rename("cash_txn"))
    dig_txn = (df[df["payment_mode"].isin(DIGITAL_MODES)]
               .groupby("account_id").size().rename("digital_txn"))

    # large transaction frequency (per month)
    avg_amt = df.groupby("account_id")["amount_inr"].mean().rename("avg_amt")
    d2 = df.merge(avg_amt, on="account_id")
    large = (d2[d2["amount_inr"] > 2 * d2["avg_amt"]]
             .groupby("account_id").size().rename("large_txn_count"))
    months = df.groupby("account_id")["ym"].nunique().rename("n_months")

    # recurring txns per month
    rec = (df[df["category"].isin(RECURRING)]
           .groupby("account_id").size().rename("recurring_txn"))

    # utility payment regularity: std of gaps (days) between utility payments
    util = df[df["category"].eq("Utility Bill")].sort_values(["account_id", "date"])
    util_reg = (util.groupby("account_id")["date"]
                .apply(lambda s: float(s.diff().dt.days.dropna().std(ddof=0))
                       if s.size > 2 else 0.0)
                .rename("utility_payment_regularity"))

    b = pd.concat([total, credits, uniq_m, debit_total, disc, wk,
                   cash_txn, dig_txn, large, months, rec], axis=1).reset_index()
    b = b.merge(util_reg, on="account_id", how="left")
    for c in ["n_credit", "debit_total", "disc_spend", "weekend_spend",
              "cash_txn", "digital_txn", "large_txn_count", "recurring_txn"]:
        b[c] = b[c].fillna(0)
    b["utility_payment_regularity"] = b["utility_payment_regularity"].fillna(0.0)

    out = pd.DataFrame({"account_id": b["account_id"]})
    out["credit_txn_ratio"] = b["n_credit"] / b["n_txn"]
    out["unique_merchants"] = b["unique_merchants"]
    out["merchant_diversity_index"] = b["unique_merchants"] / b["n_txn"]
    out["discretionary_spend_ratio"] = np.where(
        b["debit_total"] > 0, b["disc_spend"] / b["debit_total"], 0.0)
    out["weekend_spend_ratio"] = np.where(
        b["debit_total"] > 0, b["weekend_spend"] / b["debit_total"], 0.0)
    out["cash_vs_digital_ratio"] = np.where(
        b["digital_txn"] > 0, b["cash_txn"] / b["digital_txn"], b["cash_txn"])
    out["large_txn_frequency"] = b["large_txn_count"] / b["n_months"].clip(lower=1)
    out["recurring_payment_count"] = b["recurring_txn"] / b["n_months"].clip(lower=1)
    out["utility_payment_regularity"] = b["utility_payment_regularity"]
    return out


# --------------------------------------------------------------------------- #
# Intent-signal features (Propensity)
# --------------------------------------------------------------------------- #
def intent_features(df: pd.DataFrame, asof: pd.Series) -> pd.DataFrame:
    log("Computing intent-signal features ...")
    d = df.merge(asof.rename("asof"), left_on="account_id",
                 right_index=True, how="left")
    d["days_before_asof"] = (d["asof"] - d["date"]).dt.days

    def _count(mask, within):
        sub = d[mask & (d["days_before_asof"] <= within)]
        return sub.groupby("account_id").size()

    auto = _count(d["synthetic_purpose"].eq("intent_auto"), 30)
    prop = _count(d["synthetic_purpose"].eq("intent_property"), 45)
    wed = _count(d["synthetic_purpose"].eq("intent_wedding"), 30)
    ins = _count(d["synthetic_purpose"].eq("intent_insurance_cmp"), 60)

    accts = df["account_id"].unique()
    out = pd.DataFrame({"account_id": accts}).set_index("account_id")
    out["auto_dealer_txn_count_30d"] = auto
    out["property_portal_txn_count_45d"] = prop
    out["wedding_cluster_score"] = wed
    out["insurance_comparison_flag"] = (ins.reindex(accts).fillna(0) > 0).astype(int)
    out["education_txn_spike"] = 0.0  # not present in Berka; neutral

    # new merchant velocity: distinct merchants in last 30d vs monthly average
    recent = d[d["days_before_asof"] <= 30]
    new_m = recent.groupby("account_id")["merchant"].nunique().rename("recent_m")
    months = df.groupby("account_id")["ym"].nunique().rename("n_months")
    avg_m = (df.groupby("account_id")["merchant"].nunique() /
             months.clip(lower=1)).rename("avg_m_per_month")
    nm = pd.concat([new_m, avg_m], axis=1)
    out["new_merchant_velocity_30d"] = (nm["recent_m"] /
                                        nm["avg_m_per_month"].replace(0, np.nan))
    out = out.fillna(0.0).reset_index()
    for c in ["auto_dealer_txn_count_30d", "property_portal_txn_count_45d",
              "wedding_cluster_score"]:
        out[c] = out[c].astype(int)
    return out


# --------------------------------------------------------------------------- #
# Stress-indicator features (Default Prediction)
# --------------------------------------------------------------------------- #
def stress_features(df: pd.DataFrame, asof: pd.Series) -> pd.DataFrame:
    log("Computing stress-indicator features ...")
    d = df.merge(asof.rename("asof"), left_on="account_id",
                 right_index=True, how="left")
    d["days_before_asof"] = (d["asof"] - d["date"]).dt.days

    accts = df["account_id"].unique()
    out = pd.DataFrame({"account_id": accts}).set_index("account_id")

    # SIP active / recently cancelled
    sip_last = (d[d["category"].eq("SIP Investment")]
                .groupby("account_id")["days_before_asof"].min())
    out["sip_active"] = (sip_last.reindex(accts).fillna(9999) <= 60).astype(int)
    out["sip_cancelled_recently"] = ((sip_last.reindex(accts).fillna(9999) > 60) &
                                      (sip_last.reindex(accts).fillna(9999) <= 120)).astype(int)

    # EMI delay: for each EMI payment, how late? (approx: gap > 31d between EMIs)
    emi = d[d["category"].eq("EMI Payment")].sort_values(["account_id", "date"])
    emi_gap = (emi.groupby("account_id")["date"]
               .apply(lambda s: float(s.diff().dt.days.dropna().mean()) - 30.0
                      if s.size > 1 else 0.0)
               .rename("emi_delay_avg_days"))
    out["emi_delay_avg_days"] = emi_gap.reindex(accts).fillna(0.0).clip(lower=0.0)

    # EMI bounce proxy: months in last 6 where NO EMI appeared (if >=1 EMI ever)
    emi_months_recent = (d[(d["category"].eq("EMI Payment")) &
                           (d["days_before_asof"] <= 180)]
                         .groupby("account_id")["ym"].nunique().rename("emi_m6"))
    ever_emi = (d[d["category"].eq("EMI Payment")]
                .groupby("account_id").size() > 0)
    out["emi_bounce_count_6m"] = 0
    has_emi = ever_emi.reindex(accts, fill_value=False)
    em6 = emi_months_recent.reindex(accts, fill_value=0)
    out.loc[has_emi, "emi_bounce_count_6m"] = (6 - em6[has_emi]).clip(lower=0)

    # Salary delay: expected monthly, compute latest gap from salary credits
    sal = d[d["category"].eq("Salary")].sort_values(["account_id", "date"])
    sal_gap = (sal.groupby("account_id")["date"]
               .apply(lambda s: float(s.diff().dt.days.dropna().iloc[-1]) - 30.0
                      if s.size > 1 else 0.0)
               .rename("salary_delay_days"))
    out["salary_delay_days"] = sal_gap.reindex(accts).fillna(0.0).clip(lower=0.0)

    # Balance below min threshold in last 90 days
    recent90 = d[d["days_before_asof"] <= 90]
    bal_low = (recent90.groupby("account_id")["balance_inr"]
               .apply(lambda s: int((s < MIN_BAL_THRESHOLD).sum()))
               .rename("balance_below_min_count_90d"))
    out["balance_below_min_count_90d"] = bal_low.reindex(accts).fillna(0).astype(int)

    # Large withdrawal flag: any single debit > 50% of latest balance
    debit_r = recent90[~recent90["is_credit"]].copy()
    if not debit_r.empty:
        latest_bal = d.groupby("account_id")["balance_inr"].last()
        debit_r = debit_r.merge(latest_bal.rename("lb"), left_on="account_id",
                                right_index=True, how="left")
        lwf = (debit_r.groupby("account_id")
               .apply(lambda g: int((g["amount_inr"] > 0.5 * g["lb"].abs()).any()))
               .rename("large_withdrawal_flag"))
    else:
        lwf = pd.Series(dtype=int, name="large_withdrawal_flag")
    out["large_withdrawal_flag"] = lwf.reindex(accts).fillna(0).astype(int)

    # Cash advance in last 30 days (ATM beyond normal pattern proxy)
    atm_30 = (d[(d["category"].eq("ATM Withdrawal")) & (d["days_before_asof"] <= 30)]
              .groupby("account_id").size().rename("cash_advance_count_30d"))
    out["cash_advance_count_30d"] = atm_30.reindex(accts).fillna(0).astype(int)

    # New EMI appeared (new recurring debit in last 90d that wasn't there before)
    before = d[(d["category"].eq("EMI Payment")) & (d["days_before_asof"] > 90)]
    after = d[(d["category"].eq("EMI Payment")) & (d["days_before_asof"] <= 90)]
    new_emi = (after.groupby("account_id")["merchant"].nunique().rename("a") -
               before.groupby("account_id")["merchant"].nunique().rename("b"))
    out["new_emi_appeared"] = new_emi.reindex(accts).fillna(0).clip(lower=0).astype(int)

    out = out.reset_index()
    return out


# --------------------------------------------------------------------------- #
# External / MSME features (Health Score)
# --------------------------------------------------------------------------- #
def external_features(df: pd.DataFrame) -> pd.DataFrame:
    log("Computing external / MSME features ...")
    accts = df["account_id"].unique()
    out = pd.DataFrame({"account_id": accts}).set_index("account_id")

    # GST filing regularity: months with GST payment / 12
    gst = (df[df["category"].eq("GST Payment")]
           .groupby("account_id")["ym"].nunique().rename("gst_m"))
    out["gst_filing_regularity"] = (gst.reindex(accts).fillna(0) / 12.0).clip(upper=1.0)

    # EPFO contribution regularity
    epfo = (df[df["category"].eq("EPFO Contribution")]
            .groupby("account_id")["ym"].nunique().rename("epfo_m"))
    out["epfo_contribution_regularity"] = (epfo.reindex(accts).fillna(0) / 12.0).clip(upper=1.0)

    # Utility on-time (%): proxy -> regularity score (1 - CV of gap/30)
    util = df[df["category"].eq("Utility Bill")].sort_values(["account_id", "date"])
    def _util_ontime(g):
        gaps = g["date"].diff().dt.days.dropna()
        if gaps.size < 2:
            return 0.5  # neutral
        cv = gaps.std(ddof=0) / gaps.mean() if gaps.mean() > 0 else 0.5
        return max(0.0, min(1.0, 1.0 - cv))
    util_ot = util.groupby("account_id").apply(_util_ontime).rename("utility_payment_ontime_pct")
    out["utility_payment_ontime_pct"] = util_ot.reindex(accts).fillna(0.5)

    # Revenue trend (MSMEs): last 3mo avg revenue / prev 3mo
    rev = df[df["category"].eq("Business Revenue")].copy()
    if not rev.empty:
        rev_m = (rev.groupby(["account_id", "ym"])["amount_inr"]
                 .sum().reset_index()
                 .sort_values(["account_id", "ym"]))
        def _rev_trend(g):
            v = g["amount_inr"].to_numpy()
            if v.size >= 6:
                return _safe_div(v[-3:].mean(), v[-6:-3].mean(), 1.0)
            elif v.size >= 2:
                return _safe_div(v[-1], v[0], 1.0)
            return 1.0
        rt = rev_m.groupby("account_id").apply(_rev_trend).rename("revenue_trend_3m")
    else:
        rt = pd.Series(dtype=float, name="revenue_trend_3m")
    out["revenue_trend_3m"] = rt.reindex(accts).fillna(1.0)

    # Employee count proxy
    epfo_df = df[df["category"].eq("EPFO Contribution")]
    if not epfo_df.empty:
        ec = (epfo_df.groupby("account_id")["amount_inr"]
              .median().rename("med_epfo"))
        # median EPFO contribution per employee ≈ 3000
        out["employee_count_proxy"] = (ec.reindex(accts).fillna(0) / 3000.0).round(0).clip(lower=0)
    else:
        out["employee_count_proxy"] = 0

    # Business txn diversity (unique B2B merchants)
    b2b = (df[df["category"].eq("Business Revenue")]
           .groupby("account_id")["merchant"].nunique().rename("business_txn_diversity"))
    out["business_txn_diversity"] = b2b.reindex(accts).fillna(0).astype(int)

    out = out.reset_index()
    return out


# --------------------------------------------------------------------------- #
# Home Credit behavioral enrichment (group F)
# --------------------------------------------------------------------------- #
def home_credit_features(n_accounts: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute real aggregates from Home Credit, then sample to enrich Berka.

    Returns (per_berka_account enrichment, standalone HC reference table).
    """
    log("Computing Home Credit DPD / bureau features ...")
    # --- Installments: DPD ---
    inst_file = HC_DIR / "installments_payments.csv"
    if inst_file.exists():
        inst = pd.read_csv(inst_file, usecols=[
            "SK_ID_CURR", "DAYS_INSTALMENT", "DAYS_ENTRY_PAYMENT",
            "AMT_INSTALMENT", "AMT_PAYMENT"])
        inst["dpd"] = (inst["DAYS_ENTRY_PAYMENT"] - inst["DAYS_INSTALMENT"]).clip(lower=0)
        inst["paid_ratio"] = inst["AMT_PAYMENT"] / inst["AMT_INSTALMENT"].replace(0, np.nan)
        inst_agg = inst.groupby("SK_ID_CURR").agg(
            avg_dpd_installments=("dpd", "mean"),
            max_dpd_last_6m=("dpd", lambda s: float(s.tail(6).max())),
            dpd_trend=("dpd", lambda s: _slope(s.to_numpy()[-12:])),
            payment_to_due_ratio=("paid_ratio", "mean"),
            missed_payments_count_12m=("AMT_PAYMENT",
                                       lambda s: int((s.tail(12) == 0).sum())),
        ).reset_index()
    else:
        inst_agg = pd.DataFrame()
        log("  WARNING: installments_payments.csv not found")

    # --- Bureau: inquiries, active loans ---
    bureau_file = HC_DIR / "bureau.csv"
    if bureau_file.exists():
        bur = pd.read_csv(bureau_file, usecols=[
            "SK_ID_CURR", "CREDIT_ACTIVE", "DAYS_CREDIT_UPDATE"])
        bur_agg = bur.groupby("SK_ID_CURR").agg(
            bureau_inquiry_count=("DAYS_CREDIT_UPDATE", "size"),
            active_loans_count=("CREDIT_ACTIVE",
                                lambda s: int((s == "Active").sum())),
        ).reset_index()
    else:
        bur_agg = pd.DataFrame()
        log("  WARNING: bureau.csv not found")

    # merge to get per-SK_ID_CURR table
    if not inst_agg.empty and not bur_agg.empty:
        hc = inst_agg.merge(bur_agg, on="SK_ID_CURR", how="outer")
    elif not inst_agg.empty:
        hc = inst_agg
    elif not bur_agg.empty:
        hc = bur_agg
    else:
        hc = pd.DataFrame()

    hc_cols = ["avg_dpd_installments", "max_dpd_last_6m", "dpd_trend",
               "payment_to_due_ratio", "missed_payments_count_12m",
               "bureau_inquiry_count", "active_loans_count"]
    for c in hc_cols:
        if c not in hc.columns:
            hc[c] = 0.0

    hc_ref = hc.copy()

    # fill NaN in reference
    for c in hc_cols:
        hc[c] = hc[c].fillna(0.0)

    # sample rows from HC for each Berka account (label-independent)
    if len(hc) > 0:
        sampled_idx = rng.integers(0, len(hc), size=n_accounts)
        enrichment = hc.iloc[sampled_idx][hc_cols].reset_index(drop=True)
    else:
        enrichment = pd.DataFrame({c: np.zeros(n_accounts) for c in hc_cols})

    log(f"  HC reference table: {len(hc_ref):,} applicants")
    return enrichment, hc_ref


# --------------------------------------------------------------------------- #
# Assemble and write
# --------------------------------------------------------------------------- #
def main() -> None:
    PROC.mkdir(parents=True, exist_ok=True)
    df = load_transactions()
    labels = pd.read_csv(LABELS_IN)

    # as-of date per account (last transaction date)
    asof = df.groupby("account_id")["date"].max()

    cf = cashflow_features(df, asof)
    beh = behavioral_features(df)
    intent = intent_features(df, asof)
    stress = stress_features(df, asof)
    ext = external_features(df)
    hc_enrichment, hc_ref = home_credit_features(n_accounts=len(labels))

    # merge all
    log("Merging all feature groups ...")
    feat = labels.copy()
    for fdf in [cf, beh, intent, stress, ext]:
        feat = feat.merge(fdf, on="account_id", how="left")

    # attach HC enrichment (already aligned by row position)
    for c in hc_enrichment.columns:
        feat[c] = hc_enrichment[c].to_numpy()

    # fill remaining NaN with 0
    num_cols = feat.select_dtypes(include=[np.number]).columns
    feat[num_cols] = feat[num_cols].fillna(0)

    # replace inf
    feat.replace([np.inf, -np.inf], 0, inplace=True)

    # --- write feature_matrix.csv ---
    log(f"Writing {FEATURES_OUT.name} ({feat.shape[0]:,} rows x {feat.shape[1]} cols) ...")
    feat.to_csv(FEATURES_OUT, index=False)

    # --- lightweight customer profile ---
    log(f"Writing {PROFILES_OUT.name} ...")
    prof_cols = ["account_id", "district_id", "has_loan", "default_flag",
                 "propensity_target", "msme_flag", "health_quality",
                 "monthly_income_avg", "monthly_surplus_avg",
                 "balance_latest", "active_months"]
    profiles = feat[[c for c in prof_cols if c in feat.columns]].copy()
    profiles.to_csv(PROFILES_OUT, index=False)

    # --- HC reference ---
    log(f"Writing {HC_REF_OUT.name} ...")
    hc_ref.to_csv(HC_REF_OUT, index=False)

    # --- Validation ---
    validate(feat)
    log("Phase 2 complete.")


def validate(feat: pd.DataFrame) -> None:
    log("Validating feature matrix ...")
    problems = []
    num_cols = feat.select_dtypes(include=[np.number]).columns
    for c in num_cols:
        arr = feat[c].to_numpy()
        if not np.isfinite(arr).all():
            problems.append(f"non-finite values in column {c}")
    if problems:
        log("VALIDATION FAILED:")
        for p in problems:
            log(f"   - {p}")
        raise SystemExit(1)

    log("VALIDATION PASSED")
    log(f"  rows: {feat.shape[0]:,}  |  cols: {feat.shape[1]}")
    log(f"  feature groups: cashflow + behavioral + intent + stress + external + HC")
    log(f"  label distribution:")
    log(f"     default_flag=1 : {int(feat['default_flag'].sum()):,}")
    log(f"     propensity=1   : {int(feat['propensity_target'].sum()):,}")
    log(f"     msme=1         : {int(feat['msme_flag'].sum()):,}")
    log(f"  numeric feature stats (sample):")
    sample_cols = ["monthly_income_avg", "monthly_surplus_avg", "surplus_volatility",
                   "income_regularity", "credit_txn_ratio", "unique_merchants",
                   "auto_dealer_txn_count_30d", "emi_delay_avg_days",
                   "avg_dpd_installments", "gst_filing_regularity"]
    for c in sample_cols:
        if c in feat.columns:
            s = feat[c]
            log(f"     {c:35s} min={s.min():12.2f}  mean={s.mean():12.2f}  max={s.max():12.2f}")


if __name__ == "__main__":
    main()
