# Victorian NEM Demand Forecasting

Forecasting Victorian operational electricity demand 30 minutes ahead using AEMO market data, historical Melbourne weather, and machine-learning models.

## Headline result

On a fully held-out May–June 2026 test period, the final XGBoost + weather model achieved:

- **MAE: 78.34 MW**
- **RMSE: 107.71 MW**
- **56.43% lower MAE than a persistence forecast** (179.78 MW)
- Median absolute error: **57.4 MW**
- 90% of forecasts within **173.9 MW**

The final holdout period was not used during feature or model selection.

## Why this project

Short-term electricity demand is highly autocorrelated, but forecast difficulty changes across the day and season. This project tests whether recent demand dynamics, calendar context, historical demand, and weather can improve on a strong persistence benchmark while avoiding look-ahead leakage.

## Data

- **AEMO** monthly `PRICE_AND_DEMAND` files for Victoria (`VIC1`), July 2024–June 2026
- **Open-Meteo** historical hourly weather for Melbourne

Raw and processed data are intentionally excluded from Git. Reproduction scripts are included.

## Modelling approach

The project progresses from simple baselines to a final nonlinear model:

1. Persistence forecast
2. Same-time yesterday / last-week baselines
3. Linear regression
4. XGBoost using recent demand, lagged demand, rolling statistics, and calendar features
5. XGBoost + weather

Ablation analysis showed that recent demand dynamics drive most of the initial gain, while calendar variables add substantial additional signal. Weather improved MAE in all four rolling historical validation folds and was therefore retained in the final model.

## Validation design

Because this is a time-series problem, the data are never randomly shuffled.

- Development data: July 2024–April 2026
- Rolling validation folds: Sep–Oct 2025, Nov–Dec 2025, Jan–Feb 2026, Mar–Apr 2026
- Final untouched holdout: May–June 2026

Weather is merged with a backward as-of join so each demand observation receives only weather information available at or before forecast issue time.

## Repository structure

```text
.
├── notebooks/                  # Exploration, modelling, backtesting, final evaluation
├── scripts/                    # Reproducible dataset builders
├── src/nem_demand_forecasting/
│   ├── data.py                 # AEMO download / load helpers
│   ├── features.py             # Forecast feature engineering
│   └── weather.py              # Weather acquisition helpers
├── tests/                      # Unit tests
├── pyproject.toml
└── uv.lock
```

## Notebooks

- `01_explore_demand.ipynb` — initial one-month exploration
- `02_validate_historical_data.ipynb` — two-year structural validation
- `03_historical_patterns.ipynb` — seasonal and intraday patterns
- `04_baseline_models.ipynb` — persistence and historical baselines
- `05_linear_model.ipynb` — linear-regression benchmark
- `06_gradient_boosting.ipynb` — XGBoost, ablation, and diagnostics
- `07_weather_model.ipynb` — weather integration and rolling backtests
- `08_final_evaluation.ipynb` — frozen model evaluated on unseen holdout data

## Reproduce locally

Requires Python 3.11+ and [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
uv run python scripts/build_dataset.py
uv run python scripts/build_weather.py
```

Then open the notebooks in order. The processed parquet files are created under `data/processed/` and remain untracked.

Run quality checks with:

```bash
uv run ruff check src scripts tests
uv run pytest
```

## Key limitations

- Melbourne weather is used as a proxy for broader Victorian conditions.
- Historical reanalysis weather is used for retrospective modelling; a production system should use operational observations and/or genuine weather forecasts.
- The current project focuses on a 30-minute horizon and does not yet estimate prediction intervals.
- Model performance is demonstrated on one two-month final holdout period; further out-of-time evaluation would strengthen deployment claims.

## Next steps

Planned extensions include SHAP-based explainability, prediction intervals, a deployable inference pipeline, and an interactive Streamlit demo.
