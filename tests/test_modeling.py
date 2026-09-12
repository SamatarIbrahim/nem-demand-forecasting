import numpy as np
import pandas as pd
import pytest

from nem_demand_forecasting.modeling import evaluate_predictions, split_development_test


def test_split_development_test_uses_forecast_time() -> None:
    frame = pd.DataFrame(
        {
            "FORECAST_TIME": pd.to_datetime(
                [
                    "2026-04-30 23:55:00",
                    "2026-05-01 00:00:00",
                    "2026-06-30 23:55:00",
                    "2026-07-01 00:00:00",
                ]
            ),
            "value": [1, 2, 3, 4],
        }
    )

    development, test = split_development_test(frame)

    assert development["value"].tolist() == [1]
    assert test["value"].tolist() == [2, 3]


def test_evaluate_predictions_returns_expected_metrics() -> None:
    actual = np.array([100.0, 200.0, 300.0, 400.0])
    predicted = np.array([90.0, 220.0, 270.0, 440.0])

    metrics = evaluate_predictions(actual, predicted)

    assert metrics["mae_mw"] == pytest.approx(25.0)
    assert metrics["rmse_mw"] == pytest.approx(np.sqrt(750.0))
    assert metrics["median_absolute_error_mw"] == pytest.approx(25.0)
    assert metrics["p90_absolute_error_mw"] == pytest.approx(37.0)


def test_evaluate_predictions_rejects_mismatched_shapes() -> None:
    with pytest.raises(ValueError, match="same shape"):
        evaluate_predictions(np.array([1.0, 2.0]), np.array([1.0]))
