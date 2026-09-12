# Technical report

## Victorian 30-minute electricity-demand forecasting

This report condenses the analytical notebooks into a single reviewer-friendly narrative. It is intended for readers who want to understand the modelling decisions and results without stepping through every notebook.

## 1. Problem definition

The task is to forecast Victorian operational electricity demand (`TOTALDEMAND`) **30 minutes ahead** using five-minute AEMO observations.

The 30-minute horizon was chosen deliberately. At very short horizons, electricity demand changes slowly enough that a persistence forecast can be difficult to beat. At 30 minutes, recent demand is still highly informative, but ramps and calendar effects are large enough that a useful forecasting model needs to infer direction rather than simply copy the current value.

The project therefore asks:

> How much can a leakage-aware model improve on the assumption that Victorian demand 30 minutes from now will equal demand right now?

## 2. Data

### AEMO demand

Monthly AEMO `PRICE_AND_DEMAND` files for region `VIC1` were collected from July 2024 through June 2026 and combined into one chronologically ordered series.

The two-year dataset contains **210,240 five-minute observations**, exactly matching the expected count for 730 continuous days. Automated and notebook validation checks confirm:

- one region (`VIC1`);
- no missing required values;
- no duplicate timestamps; and
- uninterrupted five-minute spacing.

### Melbourne weather

Hourly historical weather for central Melbourne was retrieved from Open-Meteo. Variables include temperature, apparent temperature, humidity, precipitation, and wind speed.

AEMO market timestamps use fixed AEST. Weather was therefore aligned to fixed AEST before merging. A backward as-of join ensures every electricity observation receives only the most recent weather timestamp available at or before forecast issue time. Validation confirmed zero rows using future weather and a maximum weather age of 55 minutes.

Melbourne weather is treated as a proxy for the broader Victorian load region, which is a limitation discussed later.

## 3. Exploratory findings

The demand series shows strong and intuitive temporal structure.

### Intraday shape

Average demand falls overnight, rises sharply into the morning peak, softens through the middle of the day, then reaches a larger evening peak. The exact shape varies by season.

Winter has the highest overall demand and a pronounced morning heating peak. Summer and spring have substantially lower daytime demand, while summer conditions can produce temperature-sensitive afternoon and evening behaviour.

### Short-term autocorrelation

Demand is extremely persistent at short lags. Across the full historical series, approximate correlations with current demand were:

| Lag | Correlation |
| --- | ---: |
| 5 minutes | 0.999 |
| 30 minutes | 0.981 |
| 1 hour | 0.935 |
| 1 day | 0.783 |
| 1 week | 0.696 |

This establishes persistence as a serious benchmark rather than a trivial strawman.

### Calendar context

Earlier baseline analysis also showed that the usefulness of historical demand depends on the calendar. A previous-day forecast performed poorly when crossing behaviourally different day types, particularly Friday-to-Saturday and Sunday-to-Monday transitions.

This motivated explicit calendar features rather than relying on historical lags alone.

## 4. Validation strategy

Random train/test splitting would leak future conditions into model development, so the project uses chronological evaluation throughout.

Four expanding-window validation periods were used during development:

| Fold | Validation period |
| --- | --- |
| 1 | Sep–Oct 2025 |
| 2 | Nov–Dec 2025 |
| 3 | Jan–Feb 2026 |
| 4 | Mar–Apr 2026 |

The final **May–June 2026** period remained untouched while features and models were selected.

Once the specification was frozen, all pre-May observations were returned to the development set, the final model was retrained, and the holdout was evaluated once.

This distinction matters: May–June is a record of first-pass future generalisation, not another tuning window.

## 5. Baselines

Three simple 30-minute forecasts were evaluated first:

- current demand (persistence);
- demand at the same target time yesterday; and
- demand at the same target time one week earlier.

On the March–April validation period:

| Baseline | MAE | RMSE |
| --- | ---: | ---: |
| Persistence | **163.64 MW** | 203.68 MW |
| Same target time yesterday | 400.33 MW | 591.63 MW |
| Same target time last week | 480.69 MW | 696.47 MW |

Persistence was therefore the benchmark the learned models needed to beat.

## 6. Linear model

A linear regression model combined current/recent demand, historical demand at comparable target times, and cyclical calendar features.

Validation performance improved to:

- **MAE: 107.54 MW**
- **RMSE: 139.5 MW**
- **34.3% lower MAE than persistence**

Error diagnostics showed the linear model performed well during stable periods but struggled around stronger ramps and some daytime intervals. This supported testing a nonlinear model rather than adopting XGBoost solely for complexity's sake.

## 7. Gradient boosting

XGBoost was trained using recent demand levels, lags, recent changes, rolling statistics, historical comparable times, and target-calendar context.

On March–April validation data it achieved:

- **MAE: 77.25 MW**
- **RMSE: 107.46 MW**
- **52.8% lower MAE than persistence**

This represented an approximately 28% MAE improvement over the linear model.

### Feature ablation

Ablation testing quantified where the improvement came from:

| Feature set | MAE |
| --- | ---: |
| Current demand only | 162.46 MW |
| Recent demand dynamics | 99.13 MW |
| Recent + historical | 97.44 MW |
| Recent + historical + rolling | 95.44 MW |
| Full model incl. calendar | **77.06 MW** |

The largest first step came from recent demand trajectory. Calendar context then produced another substantial improvement, showing that the same recent ramp can imply different near-future demand depending on when it occurs.

Built-in tree feature importance was dominated by current demand and the five-minute lag. Because these predictors are highly correlated, importance values were not interpreted causally; out-of-time ablation results provide a more defensible basis for conclusions.

## 8. Public-holiday experiment

A Victorian public-holiday indicator was tested because holiday load can differ from ordinary weekdays.

The feature slightly worsened March–April validation performance:

- base XGBoost MAE: 77.25 MW;
- XGBoost + holiday MAE: 77.43 MW.

The holiday flag was therefore rejected rather than retained for narrative plausibility.

## 9. Weather experiment

Adding Melbourne weather improved March–April validation MAE from **77.25 MW to 75.90 MW**, a 1.74% improvement.

The gain was modest, which is reasonable at a 30-minute horizon because much of the immediate effect of weather is already encoded in current electricity demand. The important question was therefore whether weather helped consistently out of time.

### Rolling weather backtest

| Validation period | Base MAE | Weather MAE | Improvement |
| --- | ---: | ---: | ---: |
| Sep–Oct 2025 | 92.92 MW | 91.96 MW | 1.03% |
| Nov–Dec 2025 | 93.23 MW | 92.74 MW | 0.53% |
| Jan–Feb 2026 | 89.05 MW | 83.12 MW | 6.66% |
| Mar–Apr 2026 | 77.25 MW | 75.90 MW | 1.74% |

Weather improved all four folds. Mean MAE fell from **88.11 MW to 85.93 MW**, so weather was retained in the frozen specification.

The much larger Jan–Feb improvement is consistent with weather being especially useful during more temperature-sensitive summer demand conditions.

## 10. Final model

The final XGBoost specification includes:

- current demand;
- 5-, 15-, 30-, 60-, and 120-minute demand lags;
- demand at the same target time yesterday and one week earlier;
- 15-, 30-, and 60-minute demand changes;
- 30- and 60-minute rolling demand means;
- one-hour rolling demand volatility;
- target hour, minute, day of week, month, and weekend status; and
- temperature, apparent temperature, humidity, precipitation, and wind speed.

The model specification and XGBoost hyperparameters were frozen before opening the holdout.

## 11. Final unseen holdout

The final model was retrained on all eligible observations before May 2026 and evaluated on **17,568 forecasts** from May–June 2026.

| Metric | Persistence | Final model |
| --- | ---: | ---: |
| MAE | 179.78 MW | **78.34 MW** |
| RMSE | 222.41 MW | **107.71 MW** |

The final model reduced MAE by **56.43%** relative to persistence.

Absolute-error distribution for the final model:

| Quantile | Absolute error |
| --- | ---: |
| Median | 57.45 MW |
| 75th percentile | 105.20 MW |
| 90th percentile | 173.89 MW |
| 95th percentile | 226.87 MW |
| 99th percentile | 342.52 MW |
| Maximum | 684.16 MW |

The test MAE is close to the final validation MAE, with no obvious validation-to-test collapse.

## 12. Interpretation

Three findings matter most.

First, **recent demand trajectory carries most of the signal**. Electricity demand at a 30-minute horizon is strongly anchored to current conditions, but modelling the direction and speed of recent change is substantially better than persistence.

Second, **calendar context matters materially**. The same demand trajectory can have different implications during a morning ramp, midday, evening peak, weekday, or weekend.

Third, **weather adds smaller but repeatable incremental value**. This is exactly the kind of contribution expected at a short horizon where present demand already reflects much of the prevailing weather.

## 13. Limitations

The project should not be interpreted as a production operational forecast.

Important limitations include:

- Melbourne weather represents only one location within the Victorian load region;
- Open-Meteo historical reanalysis is not equivalent to an archived real-time weather forecast;
- only one forecast horizon is modelled;
- uncertainty intervals are not estimated;
- the final untouched holdout covers two months; and
- structural changes, extreme events, or market regime shifts outside the training period may degrade performance.

A production implementation would require live ingestion, archived forecast-weather data, monitoring, retraining rules, drift detection, failure handling, and probabilistic forecasts.

## 14. Reproducibility

The stable pipeline has been refactored out of the notebooks. To reproduce the final result:

```bash
uv sync --dev
uv run python scripts/build_dataset.py
uv run python scripts/build_weather.py
uv run python scripts/run_final_evaluation.py
```

Automated checks are available through:

```bash
uv run ruff check src scripts tests
uv run pytest
```

The original notebooks remain in the repository to show the analytical progression and unsuccessful experiments, while package code and scripts provide the reproducible path for the frozen result.
