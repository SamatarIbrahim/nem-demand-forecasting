"""Reproduce the frozen final holdout evaluation from processed project data."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from nem_demand_forecasting.features import FINAL_FEATURES, add_forecast_features, merge_weather_backward
from nem_demand_forecasting.modeling import (
    evaluate_predictions,
    make_final_model,
    split_development_test,
)


DEMAND_PATH = Path("data/processed/vic_demand_2024-07_to_2026-06.parquet")
WEATHER_PATH = Path("data/processed/melbourne_weather_2024-07_to_2026-06.parquet")
OUTPUT_PATH = Path("reports/final_metrics.json")


def main() -> None:
    demand = pd.read_parquet(DEMAND_PATH)
    weather = pd.read_parquet(WEATHER_PATH)

    demand = demand[demand["SETTLEMENTDATE"] < pd.Timestamp("2026-07-01")].copy()
    merged = merge_weather_backward(demand, weather)
    featured = add_forecast_features(merged)

    model_df = featured.dropna(subset=FINAL_FEATURES + ["target_30m"]).copy()
    development, test = split_development_test(model_df)

    model = make_final_model()
    model.fit(development[FINAL_FEATURES], development["target_30m"])

    final_forecast = model.predict(test[FINAL_FEATURES])
    persistence_forecast = test["demand_current"].to_numpy()

    final_metrics = evaluate_predictions(test["target_30m"], final_forecast)
    persistence_metrics = evaluate_predictions(test["target_30m"], persistence_forecast)

    improvement = (
        (persistence_metrics["mae_mw"] - final_metrics["mae_mw"])
        / persistence_metrics["mae_mw"]
        * 100
    )

    results = {
        "forecast_horizon_minutes": 30,
        "holdout_start": "2026-05-01",
        "holdout_end": "2026-07-01",
        "test_rows": len(test),
        "persistence": persistence_metrics,
        "final_model": final_metrics,
        "mae_improvement_percent": improvement,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

    print("FINAL HOLDOUT TEST RESULTS")
    print("--------------------------")
    print(f"Persistence MAE: {persistence_metrics['mae_mw']:.2f} MW")
    print(f"Final model MAE: {final_metrics['mae_mw']:.2f} MW")
    print(f"Improvement over persistence: {improvement:.2f}%")
    print(f"Saved metrics: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
