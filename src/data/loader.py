"""Local and demo weather data loading."""
from pathlib import Path
import pandas as pd
from src.config import ROOT, load_config
from src.data.validator import validate_weather_frame

def load_weather_data() -> tuple[pd.DataFrame, str]:
    cfg = load_config()
    # The public prototype always boots from its bundled/generated demo data.
    # External refreshes are intentionally kept out of the normal app flow.
    sample = ROOT / cfg["data"]["sample"]
    expected_blocks = set(cfg["blocks"])
    refresh_sample = not sample.exists()
    if sample.exists():
        try:
            refresh_sample = set(pd.read_csv(sample, usecols=["block"])["block"].unique()) != expected_blocks
        except (OSError, ValueError, KeyError, pd.errors.ParserError):
            refresh_sample = True
    if refresh_sample:
        from scripts.generate_demo_data import generate
        generate(sample)
    return pd.read_csv(sample), "Demo Data"
