"""Load the trained model bundle."""
import joblib
from src.config import ROOT, load_config

def load_models():
    return joblib.load(ROOT / load_config()["data"]["model"])
