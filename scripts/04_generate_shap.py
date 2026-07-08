"""
04_generate_shap.py  —  Phase 4 of the IDBI ML pipeline.

Generates SHAP explanations for all three models (Propensity, Health, Default).

For each model:
  - Global feature importance (mean |SHAP| bar chart saved as PNG)
  - Per-customer SHAP values saved alongside predictions for API serving

INPUTS:
  data/processed/feature_matrix.csv
  data/models/propensity_model.pkl
  data/models/health_model.pkl
  data/models/default_model.pkl
  data/models/model_metadata.json

OUTPUTS:
  data/models/shap_propensity.csv         per-account SHAP values + prediction
  data/models/shap_default.csv            per-account SHAP values + prediction
  data/models/shap_health_<dim>.csv       per-account SHAP values (6 files)
  data/models/shap_global_importance.json  top-20 features per model
  data/models/plots/shap_propensity_global.png
  data/models/plots/shap_default_global.png
  data/models/plots/shap_health_<dim>_global.png

Idempotent: fixed seed, outputs overwritten.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

SEED = 42
ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
MODEL_DIR = ROOT / "data" / "models"
PLOTS_DIR = MODEL_DIR / "plots"

FEATURES_IN = PROC / "feature_matrix.csv"
META_IN = MODEL_DIR / "model_metadata.json"


def log(msg: str) -> None:
    print(f"[04_shap] {msg}", flush=True)


def save_global_bar(shap_values: np.ndarray, feature_names: list[str],
                    title: str, path: Path, top_n: int = 20) -> list[dict]:
    """Save a global SHAP importance bar chart and return top-N feature list."""
    mean_abs = np.abs(shap_values).mean(axis=0)
    idx = np.argsort(mean_abs)[::-1][:top_n]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(range(top_n), mean_abs[idx][::-1], color="#1f77b4")
    ax.set_yticks(range(top_n))
    ax.set_yticklabels([feature_names[i] for i in idx][::-1], fontsize=8)
    ax.set_xlabel("Mean |SHAP value|")
    ax.set_title(title)
    plt.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)

    return [{"feature": feature_names[i], "importance": round(float(mean_abs[i]), 6)}
            for i in idx]


# --------------------------------------------------------------------------- #
# SHAP for classification models (Propensity / Default)
# --------------------------------------------------------------------------- #
def shap_classification(model, X: np.ndarray, feature_names: list[str],
                        account_ids: np.ndarray, model_name: str) -> list[dict]:
    log(f"Computing SHAP for {model_name} ...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    # For binary classifier, shap_values may be a list [class0, class1] or 2D array
    if isinstance(shap_values, list):
        shap_values = shap_values[1]  # positive class

    # predictions
    proba = model.predict_proba(X)[:, 1]

    # save per-customer SHAP
    df = pd.DataFrame(shap_values, columns=[f"shap_{c}" for c in feature_names])
    df.insert(0, "account_id", account_ids)
    df.insert(1, "prediction", proba.round(4))
    out_path = MODEL_DIR / f"shap_{model_name}.csv"
    df.to_csv(out_path, index=False)
    log(f"  Saved {out_path.name} ({df.shape[0]} rows x {df.shape[1]} cols)")

    # global importance plot
    plot_path = PLOTS_DIR / f"shap_{model_name}_global.png"
    top_features = save_global_bar(
        shap_values, feature_names,
        f"SHAP Global Importance — {model_name.title()}", plot_path)
    log(f"  Saved {plot_path.name}")
    return top_features


# --------------------------------------------------------------------------- #
# SHAP for health score (6 regressors)
# --------------------------------------------------------------------------- #
def shap_health(models_dict: dict, X: np.ndarray, feature_names: list[str],
                account_ids: np.ndarray) -> dict[str, list[dict]]:
    log("Computing SHAP for Health Score (6 dimensions) ...")
    all_top = {}
    for dim, model in models_dict.items():
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)

        preds = model.predict(X)

        df = pd.DataFrame(shap_values, columns=[f"shap_{c}" for c in feature_names])
        df.insert(0, "account_id", account_ids)
        df.insert(1, "prediction", preds.round(2))
        out_path = MODEL_DIR / f"shap_health_{dim}.csv"
        df.to_csv(out_path, index=False)

        plot_path = PLOTS_DIR / f"shap_health_{dim}_global.png"
        top_features = save_global_bar(
            shap_values, feature_names,
            f"SHAP — Health: {dim.replace('_', ' ').title()}", plot_path)
        all_top[dim] = top_features
        log(f"  {dim}: saved CSV + plot")
    return all_top


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    log("Loading feature matrix and models ...")
    feat = pd.read_csv(FEATURES_IN)
    meta = json.loads(META_IN.read_text(encoding="utf-8"))
    feature_cols = meta["feature_columns"]

    X = feat[feature_cols].fillna(0).replace([np.inf, -np.inf], 0).to_numpy()
    account_ids = feat["account_id"].to_numpy()

    propensity_model = joblib.load(MODEL_DIR / "propensity_model.pkl")
    health_models = joblib.load(MODEL_DIR / "health_model.pkl")
    default_model = joblib.load(MODEL_DIR / "default_model.pkl")

    # --- Propensity ---
    prop_top = shap_classification(
        propensity_model, X, feature_cols, account_ids, "propensity")

    # --- Default (only loan accounts, but SHAP on full for API serving) ---
    default_top = shap_classification(
        default_model, X, feature_cols, account_ids, "default")

    # --- Health ---
    health_top = shap_health(health_models, X, feature_cols, account_ids)

    # Save global importance JSON
    global_imp = {
        "propensity": prop_top,
        "default": default_top,
        "health": health_top,
    }
    imp_path = MODEL_DIR / "shap_global_importance.json"
    imp_path.write_text(json.dumps(global_imp, indent=2), encoding="utf-8")
    log(f"\nSaved {imp_path.name}")

    # Summary
    log("\n" + "=" * 60)
    log("PHASE 4 SUMMARY")
    log("=" * 60)
    log("  Propensity — top 5 features:")
    for f in prop_top[:5]:
        log(f"    {f['feature']:35s}  importance={f['importance']:.4f}")
    log("  Default — top 5 features:")
    for f in default_top[:5]:
        log(f"    {f['feature']:35s}  importance={f['importance']:.4f}")
    log("  Health — top feature per dimension:")
    for dim, feats in health_top.items():
        log(f"    {dim:35s}  → {feats[0]['feature']}")
    log("\nPhase 4 complete.")


if __name__ == "__main__":
    main()
