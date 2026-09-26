"""Data cleaning and chronological feature preparation."""
import pandas as pd
from src.features.engineering import build_features
from src.config import load_config

def preprocess(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data = data.dropna(subset=["date", "block", "rainfall_mm"]).sort_values(["block", "date"])
    thresholds = load_config()["thresholds"]
    return build_features(data,
        significant_threshold=thresholds["significant_rain_7day_mm"],
        heavy_threshold=thresholds["heavy_rain_day_mm"],
        dry_threshold=thresholds["dry_day_mm"],
        dry_days=thresholds["dry_spell_days"],
    ).dropna().reset_index(drop=True)
