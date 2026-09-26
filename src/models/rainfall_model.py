"""Random forest forecast model bundle."""
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

def build_models(seed: int = 42):
    return {
        "rainfall": RandomForestRegressor(n_estimators=100, min_samples_leaf=3, random_state=seed, n_jobs=-1),
        "significant": RandomForestClassifier(n_estimators=100, min_samples_leaf=3, class_weight="balanced", random_state=seed, n_jobs=-1),
        "dry": RandomForestClassifier(n_estimators=100, min_samples_leaf=3, class_weight="balanced", random_state=seed, n_jobs=-1),
        "heavy": RandomForestClassifier(n_estimators=100, min_samples_leaf=3, class_weight="balanced", random_state=seed, n_jobs=-1),
    }
