"""Application configuration loading."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]

def load_config():
    with (ROOT / "config.yaml").open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)
