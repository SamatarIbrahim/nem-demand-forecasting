# Reports

This directory contains small, version-controlled reporting artifacts rather than raw or processed datasets.

- `final_metrics.json` records the frozen May–June 2026 holdout metrics used in the README and model card.
- Re-running `uv run python scripts/run_final_evaluation.py` regenerates `final_metrics.json` from the processed public-source datasets.

Large demand and weather datasets remain under `data/` and are excluded from Git.
