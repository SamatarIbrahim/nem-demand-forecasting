# Model card — Victorian 30-minute demand forecast

## Summary

This project forecasts Victorian operational electricity demand 30 minutes ahead using recent AEMO demand observations, calendar context, historical lags, rolling statistics, and Melbourne weather. The final model is an XGBoost regressor selected through chronological validation and evaluated once on a held-out May–June 2026 period.

## Intended use

The model is a portfolio and research implementation demonstrating leakage-aware short-horizon time-series forecasting. It is suitable for methodological experimentation and retrospective analysis.

It is **not** an operational AEMO dispatch, trading, reliability, or investment system. Production use would require live data engineering, operational weather feeds, monitoring, retraining policy, uncertainty estimates, and substantially broader validation.

## Forecast target

- Region: Victoria (`VIC1`)
- Target: `TOTALDEMAND`
- Horizon: 30 minutes ahead
- Native demand frequency: 5 minutes

## Data

### Demand

AEMO monthly `PRICE_AND_DEMAND` files covering July 2024 through June 2026.

### Weather

Hourly Open-Meteo historical weather for central Melbourne, converted to fixed AEST to align with AEMO market timestamps. Weather is merged with a backward as-of join so the model never receives a weather observation timestamped after forecast issue time.

## Features

The final specification includes:

- current demand and 5-, 15-, 30-, 60-, and 120-minute lags;
- demand at the same target time yesterday and one week earlier;
- recent 15-, 30-, and 60-minute demand changes;
- rolling 30- and 60-minute demand level and one-hour volatility;
- target hour, minute, day of week, month, and weekend status; and
- temperature, apparent temperature, humidity, precipitation, and wind speed.

A Victorian public-holiday flag was tested and rejected because it slightly worsened validation MAE.

## Validation design

Random train/test splitting is not used.

Model development used expanding historical data with validation windows at:

- Sep–Oct 2025;
- Nov–Dec 2025;
- Jan–Feb 2026; and
- Mar–Apr 2026.

The final May–June 2026 holdout was not used for feature selection or model selection. Once the specification was frozen, the model was retrained on all available pre-May data and evaluated on the holdout once.

## Final holdout performance

| Metric | Persistence | Final XGBoost + weather |
| --- | ---: | ---: |
| MAE | 179.78 MW | **78.34 MW** |
| RMSE | 222.41 MW | **107.71 MW** |

The final model reduced MAE by **56.43%** relative to persistence.

For the final model, median absolute error was 57.45 MW, the 90th percentile was 173.89 MW, the 95th percentile was 226.87 MW, and the 99th percentile was 342.52 MW.

## Robustness checks

Weather improved MAE in all four rolling validation folds, with an average improvement of approximately 2.49% over the otherwise identical demand/calendar XGBoost model.

Feature ablation showed that recent demand dynamics provide most of the gain over persistence, while calendar context provides a substantial additional improvement.

## Important limitations

- Melbourne weather is a proxy for conditions across the broader Victorian load region.
- Historical reanalysis weather is used retrospectively. A live system should use operational observations and/or archived genuine forecasts consistent with information available at prediction time.
- The project evaluates one forecast horizon only.
- The model provides point forecasts rather than calibrated prediction intervals.
- The final holdout covers two months; more years and multiple fully untouched holdouts would strengthen deployment claims.
- Extreme events and structural market changes may not be represented adequately in the training period.

## Reproducibility

Build the processed datasets first, then run the final evaluation script:

```bash
uv sync --dev
uv run python scripts/build_dataset.py
uv run python scripts/build_weather.py
uv run python scripts/run_final_evaluation.py
```

The script recreates the frozen feature set and writes current metrics to `reports/final_metrics.json`.
