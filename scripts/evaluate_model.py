"""Print held-out metrics from a fresh chronological training run."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.train_model import train
if __name__ == "__main__": print(train()["metrics"])
