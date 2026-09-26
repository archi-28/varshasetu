"""Leakage-aware lag, rolling, and forward rainfall target features."""
import numpy as np
import pandas as pd

BASE = ["rainfall_lag_1", "rainfall_lag_3", "rainfall_lag_7", "rainfall_lag_14", "rolling_rainfall_3", "rolling_rainfall_7", "rolling_rainfall_14", "temperature_rolling_7", "humidity_rolling_7", "enso_lag", "iod_lag", "mjo_phase_sin", "mjo_phase_cos", "mjo_amplitude", "month", "day_of_year", "monsoon_month"]

def build_features(frame: pd.DataFrame, significant_threshold: float = 25.0,
                   heavy_threshold: float = 64.5, dry_threshold: float = 2.5,
                   dry_days: int = 4) -> pd.DataFrame:
    data = frame.sort_values(["block", "date"]).copy()
    groups = data.groupby("block", sort=False)
    rain = groups["rainfall_mm"]
    for lag in (1, 3, 7, 14): data[f"rainfall_lag_{lag}"] = rain.shift(lag)
    for window in (3, 7, 14):
        data[f"rolling_rainfall_{window}"] = groups["rainfall_mm"].transform(lambda x: x.shift(1).rolling(window, min_periods=window).sum())
    for col in ("temperature_c", "humidity_pct"):
        data[f"{col.split('_')[0]}_rolling_7"] = data.groupby("block")[col].transform(lambda x: x.shift(1).rolling(7, min_periods=7).mean())
    for col in ("enso", "iod"): data[f"{col}_lag"] = groups[col].shift(1)
    phase = 2 * np.pi * data["mjo_phase"] / 8
    data["mjo_phase_sin"], data["mjo_phase_cos"] = np.sin(phase), np.cos(phase)
    dates = pd.to_datetime(data["date"])
    data["month"], data["day_of_year"] = dates.dt.month, dates.dt.dayofyear
    data["monsoon_month"] = dates.dt.month.isin([6, 7, 8, 9]).astype(int)
    # Future rainfall is a target only; no future values enter BASE features.
    data["future_7day_rainfall_mm"] = groups["rainfall_mm"].transform(lambda x: x.shift(-1).rolling(7, min_periods=7).sum().shift(-6))
    # Correct forward window by explicit per-block shifted sums.
    data["future_7day_rainfall_mm"] = data.groupby("block")["rainfall_mm"].transform(lambda x: sum(x.shift(-i) for i in range(1, 8)))
    def has_dry_run(rain_series):
        upcoming = pd.concat([rain_series.shift(-i).le(dry_threshold) for i in range(1, 8)], axis=1).astype(int)
        # Transpose to roll along forecast days, then identify rows with a full run.
        return upcoming.T.rolling(dry_days, min_periods=dry_days).sum().T.eq(dry_days).any(axis=1).astype(int)
    data["dry_spell_target"] = data.groupby("block")["rainfall_mm"].transform(has_dry_run)
    data["heavy_rain_target"] = data.groupby("block")["rainfall_mm"].transform(lambda x: pd.concat([x.shift(-i) for i in range(1, 8)], axis=1).ge(heavy_threshold).any(axis=1)).astype(int)
    data["significant_rain_target"] = (data["future_7day_rainfall_mm"] >= significant_threshold).astype(int)
    return data
