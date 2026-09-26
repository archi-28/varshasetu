import pandas as pd
import numpy as np
from src.features.engineering import build_features, BASE

def sample():
    n=40
    return pd.DataFrame({"date":pd.date_range("2020-01-01", periods=n),"block":"A","rainfall_mm":np.arange(n,dtype=float),"temperature_c":25.,"humidity_pct":60.,"enso":.2,"iod":-.1,"mjo_phase":2,"mjo_amplitude":1.})

def test_lags_and_mjo():
    f=build_features(sample()); assert f.loc[14,"rainfall_lag_14"] == 0
    assert np.isclose(f.loc[0,"mjo_phase_sin"], np.sin(np.pi/2))
    assert set(BASE).issubset(f.columns)

def test_target_is_future_and_features_do_not_leak():
    f=build_features(sample()); assert f.loc[0,"future_7day_rainfall_mm"] == sum(range(1,8))
    assert "future_7day_rainfall_mm" not in BASE
