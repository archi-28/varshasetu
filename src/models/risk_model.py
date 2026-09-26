"""Risk classifier probability helper."""
def positive_probability(model, values):
    return model.predict_proba(values)[:, 1]
