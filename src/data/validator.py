"""Validation helpers for weather data frames."""
import pandas as pd

REQUIRED = ["date", "district", "block", "latitude", "longitude", "rainfall_mm", "temperature_c", "humidity_pct", "wind_speed_kmh", "pressure_hpa", "soil_moisture", "enso", "iod", "mjo_phase", "mjo_amplitude"]
NUMERIC = [c for c in REQUIRED if c not in {"date", "district", "block"}]

def validate_weather_frame(frame: pd.DataFrame) -> list[str]:
    errors = [f"Missing required column: {c}" for c in REQUIRED if c not in frame.columns]
    if errors:
        return errors
    dates = pd.to_datetime(frame["date"], errors="coerce")
    if dates.isna().any(): errors.append("date contains invalid values")
    if frame.duplicated(["date", "block"]).any(): errors.append("Duplicate date/block records found")
    for col in NUMERIC:
        if pd.to_numeric(frame[col], errors="coerce").isna().any(): errors.append(f"{col} contains missing or non-numeric values")
    if not frame["mjo_phase"].between(1, 8).all(): errors.append("mjo_phase must be an integer from 1 through 8")
    return errors
