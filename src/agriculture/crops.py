"""Documented prototype crop preferences; not field prescriptions."""
CROPS = {
    "Rice": {"sowing_window": "Season and method dependent", "rain_preference": "Regular moisture", "dry_spell_tolerance": "Low", "heavy_rain_sensitivity": "Medium", "basic_advisory_rules": "Monitor water and drainage"},
    "Wheat": {"sowing_window": "Typically winter season", "rain_preference": "Moderate; avoid waterlogging", "dry_spell_tolerance": "Medium", "heavy_rain_sensitivity": "High", "basic_advisory_rules": "Check drainage and stage-specific needs"},
    "Maize": {"sowing_window": "Season dependent", "rain_preference": "Moist but drained soil", "dry_spell_tolerance": "Low", "heavy_rain_sensitivity": "Medium", "basic_advisory_rules": "Monitor moisture and lodging"},
    "Sugarcane": {"sowing_window": "Region and planting system dependent", "rain_preference": "Adequate moisture", "dry_spell_tolerance": "Medium", "heavy_rain_sensitivity": "Medium", "basic_advisory_rules": "Monitor soil moisture and drainage"},
    "Cotton": {"sowing_window": "Season dependent", "rain_preference": "Moderate; well drained", "dry_spell_tolerance": "Medium", "heavy_rain_sensitivity": "High", "basic_advisory_rules": "Avoid field operations in saturated soil"},
    "Soybean": {"sowing_window": "Season dependent", "rain_preference": "Moderate; well drained", "dry_spell_tolerance": "Low", "heavy_rain_sensitivity": "High", "basic_advisory_rules": "Monitor drainage and crop condition"},
}
