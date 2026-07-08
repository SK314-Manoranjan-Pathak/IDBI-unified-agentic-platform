"""
03_train_models.py  —  Phase 3 of the IDBI ML pipeline.

Trains three model heads on the shared feature matrix produced in Phase 2:

  1. Propensity Model  (XGBoost binary classification)
     Target: propensity_target (1 = high intent for loan)
     Metric: AUC-ROC (target > 0.85)

  2. Health Score Model  (XGBoost multi-output regression, 6 dimensions)
     Targets: self-supervised scores derived from features via heuristic rules
       - income_stability_score
       - spending_discipline_score
       - cashflow_adequacy_score
       - debt_management_score
       - growth_trajectory_score
       - external_compliance_score
     Metric: R² per dimension, realistic distribution check

  3. Default Prediction Model  (XGBoost binary classification)
     Target: default_flag (1 = loan status B or D)
     Metric: AUC-ROC (target > 0.85, stretch 0.90)

INPUTS:
  data/processed/feature_matrix.csv

OUTPUTS:
  data/models/propensity_model.pkl
  data/models/health_model.pkl
  data/models/default_model.pkl
  data/models/model_metadata.json   (metrics, feature lists, thresholds)

Idempotent: fixed seed, outputs overwritten.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, r2_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from xgboost import XGBClassifier, XGBRegressor

SEED = 42
ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
MODEL_DIR = ROOT / "data" / "models"

FEATURES_IN = PROC / "feature_matrix.csv"


def log(msg: str) -> None:
    print(f"[03_train] {msg}", flush=True)


# --------------------------------------------------------------------------- #
# Feature columns (exclude labels/metadata)
# --------------------------------------------------------------------------- #
LABEL_COLS = ["account_id", "district_id", "loan_id", "loan_amount",
              "loan_duration", "loan_payments", "loan_status", "default_flag",
              "has_loan", "propensity_target", "intent_product", "msme_flag",
              "health_quality", "employee_count"]

# Features subsets per model (all numeric features minus labels)
# Propensity: cashflow + behavioral + intent
PROPENSITY_EXCLUDE = ["default_flag", "has_loan", "loan_status", "loan_amount",
                      "loan_duration", "loan_payments", "loan_id"]
# Default: cashflow + behavioral + stress + HC  (exclude intent and MSME labels)
DEFAULT_EXCLUDE = ["propensity_target", "intent_product", "msme_flag",
                   "health_quality"]


# --------------------------------------------------------------------------- #
# Health Score — self-supervised label generation (heuristic rules)
# --------------------------------------------------------------------------- #
def compute_health_labels(feat: pd.DataFrame) -> pd.DataFrame:
    """Generate 6-dimension health scores (0-100) from features via heuristic rules.

    These are *self-supervised* labels: derived deterministically from the feature
    values so the model learns the mapping from raw features to composite health.
    """
    log("Computing self-supervised health score labels (6 dimensions) ...")
    n = len(feat)
    scores = pd.DataFrame(index=feat.index)

    # --- 1. Income Stability (income regularity, growth, volatility) ---
    # Lower CV (income_regularity) = more stable -> higher score
    cv = feat["income_regularity"].clip(upper=2.0)
    scores["income_stability_score"] = (100 * (1 - cv / 2.0)).clip(0, 100)
    # bonus for growth
    growth_bonus = ((feat["income_growth_rate"] - 1.0) * 30).clip(-10, 15)
    scores["income_stability_score"] = (scores["income_stability_score"] +
                                        growth_bonus).clip(0, 100)

    # --- 2. Spending Discipline (discretionary ratio, large txn freq) ---
    disc = feat["discretionary_spend_ratio"].clip(upper=1.0)
    large = feat["large_txn_frequency"].clip(upper=5.0)
    scores["spending_discipline_score"] = (
        100 - disc * 50 - large * 5
    ).clip(0, 100)

    # --- 3. Cash Flow Adequacy (surplus, min balance, overdraft) ---
    # normalize surplus relative to income
    surplus_ratio = np.where(
        feat["monthly_income_avg"] > 0,
        feat["monthly_surplus_avg"] / feat["monthly_income_avg"],
        0.0)
    surplus_score = (np.clip(surplus_ratio, -0.3, 0.5) + 0.3) / 0.8 * 80
    od_penalty = feat["overdraft_frequency"].clip(upper=50) * 0.5
    scores["cashflow_adequacy_score"] = (surplus_score - od_penalty).clip(0, 100)

    # --- 4. Debt Management (EMI delay, bounces, salary delay) ---
    emi_pen = feat["emi_delay_avg_days"].clip(upper=30) * 1.5
    bounce_pen = feat["emi_bounce_count_6m"].clip(upper=6) * 8
    sal_pen = feat["salary_delay_days"].clip(upper=30) * 1.0
    scores["debt_management_score"] = (100 - emi_pen - bounce_pen - sal_pen).clip(0, 100)

    # --- 5. Growth Trajectory (income growth, savings/balance trend) ---
    growth_norm = ((feat["income_growth_rate"] - 0.7) / 0.6).clip(0, 1) * 60
    trend_norm = np.clip(feat["min_balance_trend"] / 5000.0, -1, 1) * 20 + 20
    scores["growth_trajectory_score"] = (growth_norm + trend_norm).clip(0, 100)

    # --- 6. External Compliance (GST, EPFO, utility payments) ---
    gst = feat["gst_filing_regularity"] * 40
    epfo = feat["epfo_contribution_regularity"] * 30
    util = feat["utility_payment_ontime_pct"] * 30
    scores["external_compliance_score"] = (gst + epfo + util).clip(0, 100)

    # round
    for c in scores.columns:
        scores[c] = scores[c].round(1)

    log(f"  Score distributions:")
    for c in scores.columns:
        s = scores[c]
        log(f"    {c:35s}  mean={s.mean():5.1f}  std={s.std():5.1f}  "
            f"min={s.min():5.1f}  max={s.max():5.1f}")
    return scores


# --------------------------------------------------------------------------- #
# Model 1: Propensity
# --------------------------------------------------------------------------- #
def train_propensity(feat: pd.DataFrame, feature_cols: list[str]) -> dict:
    log("=" * 60)
    log("Training Model 1: Propensity (XGBoost binary) ...")
    y = feat["propensity_target"].astype(int).to_numpy()
    X = feat[feature_cols].to_numpy()

    pos = y.sum()
    neg = len(y) - pos
    scale_pos = neg / pos if pos > 0 else 1.0
    log(f"  positive={pos}, negative={neg}, scale_pos_weight={scale_pos:.1f}")

    model = XGBClassifier(
        n_estimators=300, max_depth=5, learning_rate=0.05,
        scale_pos_weight=scale_pos, subsample=0.8, colsample_bytree=0.8,
        reg_alpha=0.1, reg_lambda=1.0, random_state=SEED,
        eval_metric="auc", use_label_encoder=False,
    )

    # cross-val AUC
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    proba = cross_val_predict(model, X, y, cv=cv, method="predict_proba")[:, 1]
    auc = roc_auc_score(y, proba)
    log(f"  CV AUC-ROC: {auc:.4f}  (target > 0.85)")

    # refit on full data
    model.fit(X, y)
    joblib.dump(model, MODEL_DIR / "propensity_model.pkl")
    log("  Saved propensity_model.pkl")
    return {"auc_roc": round(auc, 4), "n_features": len(feature_cols),
            "n_positive": int(pos), "n_total": len(y)}


# --------------------------------------------------------------------------- #
# Model 2: Health Score (multi-output regression)
# --------------------------------------------------------------------------- #
def train_health(feat: pd.DataFrame, feature_cols: list[str],
                 health_labels: pd.DataFrame) -> dict:
    log("=" * 60)
    log("Training Model 2: Health Score (6 XGBRegressors) ...")
    X = feat[feature_cols].to_numpy()
    targets = list(health_labels.columns)

    models = {}
    r2_scores = {}
    for tgt in targets:
        y = health_labels[tgt].to_numpy()
        m = XGBRegressor(
            n_estimators=200, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            reg_alpha=0.1, reg_lambda=1.0, random_state=SEED,
        )
        # cross-val R² — use KFold (regression target is continuous)
        from sklearn.model_selection import KFold
        cv = KFold(n_splits=5, shuffle=True, random_state=SEED)
        preds = cross_val_predict(m, X, y, cv=cv)
        r2 = r2_score(y, preds)
        r2_scores[tgt] = round(r2, 4)
        log(f"  {tgt:35s}  CV R²={r2:.4f}")

        m.fit(X, y)
        models[tgt] = m

    joblib.dump(models, MODEL_DIR / "health_model.pkl")
    log("  Saved health_model.pkl (dict of 6 regressors)")
    return {"r2_per_dimension": r2_scores, "n_features": len(feature_cols),
            "dimensions": targets}


# --------------------------------------------------------------------------- #
# Model 3: Default Prediction
# --------------------------------------------------------------------------- #
def train_default(feat: pd.DataFrame, feature_cols: list[str]) -> dict:
    log("=" * 60)
    log("Training Model 3: Default Prediction (XGBoost binary) ...")
    # only accounts with loans
    loan_mask = feat["has_loan"].eq(1)
    feat_loan = feat[loan_mask].reset_index(drop=True)
    y = feat_loan["default_flag"].astype(int).to_numpy()
    X = feat_loan[feature_cols].to_numpy()

    pos = y.sum()
    neg = len(y) - pos
    scale_pos = neg / pos if pos > 0 else 1.0
    log(f"  loan accounts={len(y)}, default=1: {pos}, scale_pos_weight={scale_pos:.1f}")

    model = XGBClassifier(
        n_estimators=400, max_depth=4, learning_rate=0.03,
        scale_pos_weight=scale_pos, subsample=0.8, colsample_bytree=0.8,
        reg_alpha=0.5, reg_lambda=2.0, gamma=1.0, min_child_weight=5,
        random_state=SEED, eval_metric="auc", use_label_encoder=False,
    )

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    proba = cross_val_predict(model, X, y, cv=cv, method="predict_proba")[:, 1]
    auc = roc_auc_score(y, proba)
    log(f"  CV AUC-ROC: {auc:.4f}  (target > 0.85, stretch 0.90)")

    model.fit(X, y)
    joblib.dump(model, MODEL_DIR / "default_model.pkl")
    log("  Saved default_model.pkl")
    return {"auc_roc": round(auc, 4), "n_features": len(feature_cols),
            "n_positive": int(pos), "n_loan_accounts": len(y)}


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    log("Loading feature matrix ...")
    feat = pd.read_csv(FEATURES_IN)
    log(f"  shape: {feat.shape}")

    # determine numeric feature columns (exclude labels/metadata/string cols)
    all_cols = set(feat.columns)
    exclude = set(LABEL_COLS) | set(c for c in all_cols
                                    if feat[c].dtype == object)
    feature_cols = sorted(all_cols - exclude)
    log(f"  {len(feature_cols)} feature columns identified")

    # fill any remaining NaN or inf
    feat[feature_cols] = feat[feature_cols].fillna(0).replace(
        [np.inf, -np.inf], 0)

    # Health labels
    health_labels = compute_health_labels(feat)
    # save health labels alongside feature matrix for later SHAP
    health_labels.to_csv(PROC / "health_labels.csv", index=False)

    # Train models
    prop_metrics = train_propensity(feat, feature_cols)
    health_metrics = train_health(feat, feature_cols, health_labels)
    default_metrics = train_default(feat, feature_cols)

    # Save metadata
    metadata = {
        "feature_columns": feature_cols,
        "propensity": prop_metrics,
        "health_score": health_metrics,
        "default": default_metrics,
    }
    meta_path = MODEL_DIR / "model_metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    log(f"\nModel metadata saved to {meta_path.name}")

    # Summary
    log("\n" + "=" * 60)
    log("PHASE 3 SUMMARY")
    log("=" * 60)
    log(f"  Propensity AUC  : {prop_metrics['auc_roc']:.4f}  "
        f"{'✓ PASS' if prop_metrics['auc_roc'] >= 0.85 else '✗ BELOW TARGET'}")
    log(f"  Default AUC     : {default_metrics['auc_roc']:.4f}  "
        f"{'✓ PASS' if default_metrics['auc_roc'] >= 0.85 else '✗ BELOW TARGET'}")
    log(f"  Health R² (avg) : {np.mean(list(health_metrics['r2_per_dimension'].values())):.4f}")
    log("  Health dimensions R²:")
    for dim, r2 in health_metrics["r2_per_dimension"].items():
        log(f"    {dim:35s}  {r2:.4f}")
    log("\nPhase 3 complete.")


if __name__ == "__main__":
    main()
