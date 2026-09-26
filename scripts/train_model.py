"""Chronologically train rainfall regression and risk classifiers."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import joblib
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, f1_score, precision_score, recall_score, roc_auc_score
from src.config import ROOT, load_config
from src.data.loader import load_weather_data
from src.data.preprocessing import preprocess
from src.features.engineering import BASE
from src.models.rainfall_model import build_models

def train():
    frame, data_mode = load_weather_data(); df = preprocess(frame)
    # Split by calendar time across all blocks so no block is assigned wholly
    # to train or test merely because rows are grouped by block.
    cutoff = df["date"].quantile(.8)
    train, test = df[df.date <= cutoff], df[df.date > cutoff]
    x, xt = train[BASE], test[BASE]; bundle = build_models()
    targets = {"rainfall": "future_7day_rainfall_mm", "significant": "significant_rain_target", "dry": "dry_spell_target", "heavy": "heavy_rain_target"}
    metrics = {}
    for key, target in targets.items():
        bundle[key].fit(x, train[target])
        if key == "rainfall":
            pred = bundle[key].predict(xt); actual = test[target]
            metrics.update(mae=float(mean_absolute_error(actual, pred)), rmse=float(mean_squared_error(actual, pred)**.5), r2=float(r2_score(actual, pred)))
        else:
            predicted = bundle[key].predict(xt)
            scores = bundle[key].predict_proba(xt)[:, 1]
            metrics[f"{key}_f1"] = float(f1_score(test[target], predicted, zero_division=0))
            metrics[f"{key}_precision"] = float(precision_score(test[target], predicted, zero_division=0))
            metrics[f"{key}_recall"] = float(recall_score(test[target], predicted, zero_division=0))
            metrics[f"{key}_roc_auc"] = float(roc_auc_score(test[target], scores)) if test[target].nunique() == 2 else float("nan")
    bundle["metrics"] = metrics; bundle["feature_names"] = BASE; bundle["data_mode"] = data_mode
    output = ROOT / load_config()["data"]["model"]; output.parent.mkdir(parents=True, exist_ok=True); joblib.dump(bundle, output)
    print(f"Saved model to {output}\nMetrics: {metrics}")
    return bundle

if __name__ == "__main__": train()
