# Data dictionary

## AEMO demand data

The project uses monthly AEMO `PRICE_AND_DEMAND` CSV files for Victoria (`VIC1`).

| Column | Meaning | Use |
| --- | --- | --- |
| `REGION` | NEM region identifier | structural validation |
| `SETTLEMENTDATE` | five-minute market timestamp in fixed AEST | ordering, lags, joins, forecast issue time |
| `TOTALDEMAND` | Victorian operational demand in MW | forecast target and demand features |
| `RRP` | regional reference price | retained in source data; not used by final demand model |
| `PERIODTYPE` | AEMO period classification | structural validation |

## Weather data

Hourly Open-Meteo historical weather is retrieved for central Melbourne and converted to fixed AEST before merging.

| Column | Meaning | Final model? |
| --- | --- | --- |
| `temperature_2m` | near-surface air temperature | yes |
| `apparent_temperature` | apparent/feels-like temperature | yes |
| `relative_humidity_2m` | near-surface relative humidity | yes |
| `precipitation` | hourly precipitation | yes |
| `wind_speed_10m` | near-surface wind speed | yes |
| `WEATHER_TIME` | weather observation timestamp after AEST alignment | join/audit column |

Weather is attached using `pandas.merge_asof(..., direction="backward")`, ensuring no demand row is assigned a weather timestamp after the forecast issue time.

## Engineered forecast fields

The reusable feature pipeline in `src/nem_demand_forecasting/features.py` creates:

- `FORECAST_TIME`: issue timestamp plus 30 minutes;
- `target_30m`: demand six five-minute intervals ahead;
- recent demand lags from 5 minutes to 2 hours;
- same-target-time demand from yesterday and one week earlier;
- 15-, 30-, and 60-minute demand changes;
- rolling demand means and one-hour standard deviation; and
- target-time calendar fields such as hour, day of week, month, and weekend status.

The final feature names are defined centrally in `FINAL_FEATURES`.
