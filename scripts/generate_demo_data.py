"""Generate deterministic five-year synthetic daily Meerut weather data."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from src.config import ROOT, load_config

def generate(path=None, years=5, seed=24):
    cfg = load_config()
    path = Path(path) if path else ROOT / cfg["data"]["sample"]
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    dates = pd.date_range(end=pd.Timestamp.today().normalize() - pd.Timedelta(days=8), periods=365 * years, freq="D")
    blocks = cfg["blocks"]
    rows = []
    for bi, (block, (lat, lon)) in enumerate(blocks.items()):
        rain = np.zeros(len(dates))
        for i, d in enumerate(dates):
            seasonal = d.month in (6, 7, 8, 9)
            wet_prob = .34 if seasonal else .06
            if 1500 <= i % 1825 <= 1530: wet_prob = .72 # deterministic onset-like pulse
            if 1560 <= i % 1825 <= 1575: wet_prob = .015 # break period
            wet = rng.random() < wet_prob
            rain[i] = max(0, rng.gamma(2.2, 8 + bi * .7)) if wet else 0
            # Stable presentation scenario in recent dates flows through generated observations/features/model.
            offset = i >= len(dates) - 18
            if offset and block == "Mawana": rain[i] = rng.gamma(3, 23) if rng.random() < .78 else 0
            if offset and block == "Kharkhoda": rain[i] = 0 if rng.random() < .9 else rng.gamma(1.5, 5)
            if offset and block == "Meerut": rain[i] = rng.gamma(2, 11) if rng.random() < .40 else 0
        for i, d in enumerate(dates):
            monsoon = d.month in (6, 7, 8, 9)
            rows.append({"date": d, "district": "Meerut", "block": block, "latitude": lat + rng.normal(0, .006), "longitude": lon + rng.normal(0, .006), "rainfall_mm": round(rain[i], 2), "temperature_c": round((30 if monsoon else 22) + 5 * np.sin(2*np.pi*(d.dayofyear-100)/365) + rng.normal(0, 2), 1), "humidity_pct": round(np.clip((76 if monsoon else 52) + (12 if rain[i] > 0 else 0) + rng.normal(0, 9), 20, 100), 1), "wind_speed_kmh": round(np.clip(rng.gamma(2, 5) + (5 if monsoon else 0), 0, 60), 1), "pressure_hpa": round(1008 + rng.normal(0, 5) - (4 if monsoon else 0), 1), "soil_moisture": round(np.clip(.18 + min(sum(rain[max(0,i-6):i+1]), 120)/180 + rng.normal(0,.04), .05,.65), 3), "enso": round(np.sin(2*np.pi*(d.year-2016)/4.2) + rng.normal(0,.12), 2), "iod": round(np.sin(2*np.pi*(d.year-2018)/3.3) + rng.normal(0,.12), 2), "mjo_phase": int(rng.integers(1,9)), "mjo_amplitude": round(float(np.clip(rng.gamma(2, .45), 0, 3)), 2)})
    frame = pd.DataFrame(rows)
    frame.to_csv(path, index=False)
    print(f"Wrote {len(frame):,} synthetic rows to {path}")
    return frame

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path); parser.add_argument("--years", type=int, default=5)
    args = parser.parse_args(); generate(args.output, args.years)
