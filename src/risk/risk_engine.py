"""Transparent shared risk bands and overall score."""
def risk_level(value: float, levels=None) -> str:
    levels = levels or {"low": 30, "moderate": 60, "high": 80}
    if value <= levels["low"]: return "LOW"
    if value <= levels["moderate"]: return "MODERATE"
    if value <= levels["high"]: return "HIGH"
    return "VERY HIGH"

def overall_risk(rain_probability: float, dry_probability: float, heavy_probability: float) -> float:
    # Rain can be beneficial; its deviation from a moderate 50% likelihood is risk.
    rain_extremity = abs(rain_probability - 0.5) * 2
    return 100 * (0.20 * rain_extremity + 0.45 * dry_probability + 0.35 * heavy_probability)
