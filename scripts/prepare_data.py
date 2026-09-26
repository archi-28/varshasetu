"""Validate and produce the feature dataset."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import ROOT, load_config
from src.data.loader import load_weather_data
from src.data.validator import validate_weather_frame
from src.data.preprocessing import preprocess

if __name__ == "__main__":
    frame, mode = load_weather_data()
    errors = validate_weather_frame(frame)
    if errors: raise SystemExit("Invalid input: " + "; ".join(errors))
    output = ROOT / load_config()["data"]["processed"]; output.parent.mkdir(parents=True, exist_ok=True)
    processed = preprocess(frame); processed.to_csv(output, index=False)
    print(f"{mode}: wrote {len(processed):,} feature rows to {output}")
