"""Generate block-level probabilistic outlooks from trained classifiers."""
import numpy as np
import pandas as pd
from src.features.engineering import BASE

def predict_block(models: dict, row: pd.Series, horizon: int = 7) -> dict:
    x = row[BASE].to_frame().T
    rain_mm = max(0.0, float(models["rainfall"].predict(x)[0]))
    probs = {k: float(models[k].predict_proba(x)[0, 1]) for k in ("significant", "dry", "heavy")}
    # Persistence evidence raises dry-spell risk after notably dry conditions.
    # This is an explicit prototype blend, not a calibrated classifier output.
    prior_week_rain = max(0.0, float(row["rolling_rainfall_7"]))
    dry_persistence = 0.9 * max(0.0, 1.0 - prior_week_rain / 17.5)
    probs["dry"] = max(probs["dry"], dry_persistence)
    rain_probability = probs["significant"]
    # Disaggregate the seven-day model total into a deterministic daily profile.
    weights = np.array([1.15, 1.1, 1.0, .95, .9, .85, .8])
    weights = weights[:min(horizon, 7)] / weights[:min(horizon, 7)].sum()
    extended_factor = 1.0 if horizon <= 7 else (horizon / 7) ** .68
    daily = (rain_mm * extended_factor * weights).tolist()
    return {"expected_rainfall": rain_mm * extended_factor, "rain_probability": rain_probability, "dry_spell_probability": probs["dry"], "heavy_rain_probability": probs["heavy"], "daily_rainfall": daily, "horizon": horizon, "model_label": "7-Day: Model forecast" if horizon == 7 else ("14-Day: Extended horizon" if horizon == 14 else "30-Day: Experimental horizon")}
