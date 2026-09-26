"""Transparent prototype onset / false-onset rules."""
import pandas as pd

def detect_onset(rainfall, threshold=2.5, consecutive=3) -> dict:
    series = pd.Series(rainfall).dropna().reset_index(drop=True)
    wet = series.ge(threshold)
    streak = wet.rolling(consecutive, min_periods=consecutive).sum().eq(consecutive)
    found = bool(streak.any())
    start = int(streak[streak].index[0]) if found else None
    # rolling streak's index is its final day; inspect the following seven days.
    post_onset = series.iloc[start + 1:start + 8] if found else pd.Series(dtype=float)
    false = bool(found and post_onset.lt(threshold).sum() >= 5)
    return {"status": "Onset detected" if found and not false else ("Possible onset" if found else "No onset"), "false_onset_risk": false}
