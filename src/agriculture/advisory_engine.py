"""Crop-aware, cautious advisory generation in English and Hindi."""
from src.risk.risk_engine import risk_level

TEXT = {
 "en": {"dry": "Dry Spell Risk", "heavy": "Heavy Rainfall Risk", "favorable": "Favorable Moisture Outlook", "dry_summary": "A prolonged dry period is possible in this outlook.", "heavy_summary": "Heavy rainfall is possible during the forecast window.", "favorable_summary": "Rainfall conditions appear favorable for planned agricultural operations.", "dry_actions": ["Consider delaying rain-dependent sowing where agronomically appropriate.", "Prepare supplementary irrigation and monitor soil moisture."], "heavy_actions": ["Check field drainage and monitor waterlogging or lodging.", "Avoid unnecessary irrigation before expected rainfall."], "good_actions": ["Continue monitoring local conditions before field decisions."], "false": "A possible false-onset pattern is flagged by a simple prototype heuristic."},
 "hi": {"dry": "शुष्क अवधि का जोखिम", "heavy": "अधिक वर्षा का जोखिम", "favorable": "अनुकूल नमी का अनुमान", "dry_summary": "इस पूर्वानुमान अवधि में लंबी शुष्क अवधि संभव है।", "heavy_summary": "पूर्वानुमान अवधि में भारी वर्षा संभव है।", "favorable_summary": "वर्षा की स्थिति नियोजित कृषि कार्यों के लिए अनुकूल दिखती है।", "dry_actions": ["उपयुक्त होने पर वर्षा-आधारित बुवाई टालने पर विचार करें।", "पूरक सिंचाई तैयार रखें और मिट्टी की नमी देखें।"], "heavy_actions": ["खेत की जल निकासी जाँचें और जलभराव पर निगरानी रखें।", "संभावित वर्षा से पहले अनावश्यक सिंचाई से बचें।"], "good_actions": ["खेत संबंधी निर्णय से पहले स्थानीय स्थिति पर नज़र रखें।"], "false": "सरल प्रोटोटाइप नियम ने संभावित झूठे मानसून आगमन का संकेत दिया है।"}}

def generate_advisory(crop, rain_probability, dry_spell_probability, heavy_rain_probability, expected_rainfall, onset_status="No onset", false_onset_risk=False, language="en"):
    t = TEXT["hi" if language.lower().startswith("hi") else "en"]
    if heavy_rain_probability >= .6:
        headline, summary, actions = t["heavy"], t["heavy_summary"], t["heavy_actions"]
    elif dry_spell_probability >= .6 or (false_onset_risk and rain_probability < .5):
        headline, summary, actions = t["dry"], t["dry_summary"], t["dry_actions"]
    else:
        headline, summary, actions = t["favorable"], t["favorable_summary"], t["good_actions"]
    warnings = [t["false"]] if false_onset_risk else []
    return {"headline": headline, "summary": f"{crop}: {summary} ({expected_rainfall:.0f} mm estimated).", "recommended_actions": actions, "warnings": warnings, "onset_status": onset_status}
