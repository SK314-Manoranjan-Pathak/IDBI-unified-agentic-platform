"""
run_pipeline.py — Master script to execute the full IDBI ML pipeline.

Runs all 4 phases sequentially:
  Phase 1: Indianize raw Berka data
  Phase 2: Feature engineering (51-feature matrix)
  Phase 3: Train models (Propensity, Health, Default)
  Phase 4: Generate SHAP explanations

Usage:
  python run_pipeline.py              # run all phases
  python run_pipeline.py --from 2     # resume from Phase 2 onwards
  python run_pipeline.py --only 3     # run only Phase 3
  python run_pipeline.py --validate   # run all phases + validation checklist
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Ensure the project root is on sys.path so scripts can resolve imports
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


PHASES = [
    {"num": 1, "name": "Indianize Data",          "module": "scripts.01_indianize"},
    {"num": 2, "name": "Feature Engineering",     "module": "scripts.02_feature_engineering"},
    {"num": 3, "name": "Train Models",            "module": "scripts.03_train_models"},
    {"num": 4, "name": "Generate SHAP",           "module": "scripts.04_generate_shap"},
]


def run_phase(phase: dict) -> None:
    """Import and execute a pipeline phase by calling its main() function."""
    import importlib
    print(f"\n{'='*70}")
    print(f"  PHASE {phase['num']}: {phase['name']}")
    print(f"  Module: {phase['module']}")
    print(f"{'='*70}\n")

    module = importlib.import_module(phase["module"])
    module.main()


def run_validation() -> None:
    """Run the validation checklist script."""
    import importlib
    print(f"\n{'='*70}")
    print(f"  VALIDATION CHECKLIST")
    print(f"{'='*70}\n")

    module = importlib.import_module("scripts.validate_checklist")
    # validate_checklist.py runs at import (top-level code), so just importing it works.
    # If it has a main(), call it; otherwise the import already executed.
    if hasattr(module, "main"):
        module.main()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the full IDBI ML pipeline (Phases 1-4).")
    parser.add_argument("--from", type=int, dest="from_phase", default=1,
                        choices=[1, 2, 3, 4],
                        help="Start from this phase (default: 1)")
    parser.add_argument("--only", type=int, default=None,
                        choices=[1, 2, 3, 4],
                        help="Run only this specific phase")
    parser.add_argument("--validate", action="store_true",
                        help="Run validation checklist after pipeline completes")
    args = parser.parse_args()

    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║          FinPulse — ML Pipeline Runner (by ShellKode)              ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")

    start_time = time.time()

    if args.only:
        phases_to_run = [p for p in PHASES if p["num"] == args.only]
    else:
        phases_to_run = [p for p in PHASES if p["num"] >= args.from_phase]

    print(f"\nPhases to execute: {[p['num'] for p in phases_to_run]}")

    for phase in phases_to_run:
        phase_start = time.time()
        try:
            run_phase(phase)
        except SystemExit as e:
            if e.code and e.code != 0:
                print(f"\n✗ Phase {phase['num']} ({phase['name']}) FAILED with exit code {e.code}")
                sys.exit(e.code)
        except Exception as e:
            print(f"\n✗ Phase {phase['num']} ({phase['name']}) FAILED with error:")
            print(f"  {type(e).__name__}: {e}")
            sys.exit(1)
        phase_elapsed = time.time() - phase_start
        print(f"\n✓ Phase {phase['num']} completed in {phase_elapsed:.1f}s")

    if args.validate:
        try:
            run_validation()
        except Exception as e:
            print(f"\n✗ Validation failed: {e}")

    total_elapsed = time.time() - start_time
    print(f"\n{'='*70}")
    print(f"  PIPELINE COMPLETE — Total time: {total_elapsed:.1f}s")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
