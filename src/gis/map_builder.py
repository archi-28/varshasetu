"""Create interactive block marker maps, with clearly labelled demo locations."""
import folium
import json
from pathlib import Path
from src.config import ROOT, load_config

COLORS = {"LOW": "#2e8b57", "MODERATE": "#e2b93b", "HIGH": "#ed8b25", "VERY HIGH": "#c83e4d"}

def build_map(records, layer="Overall Risk"):
    fmap = folium.Map(location=[28.99, 77.70], zoom_start=10, tiles="OpenStreetMap")
    keys = {"Rainfall Risk": "rain_probability", "Dry Spell Risk": "dry_spell_probability", "Heavy Rain Risk": "heavy_rain_probability", "Overall Risk": "overall_score"}
    from src.risk.risk_engine import risk_level
    key = keys[layer]
    geo_dir = ROOT / load_config()["data"]["geo"]
    boundary_files = sorted([*geo_dir.glob("*.geojson"), *geo_dir.glob("*.json")])
    if boundary_files:
        try:
            geojson = json.loads(boundary_files[0].read_text(encoding="utf-8"))
            by_name = {item["block"]: item for item in records}
            features = geojson.get("features", []) if geojson.get("type") == "FeatureCollection" else [geojson]
            for feature in features:
                props = feature.get("properties") or {}
                name = next((props[k] for k in ("block", "BLOCK", "name", "NAME", "block_name", "BLOCK_NAME") if props.get(k)), None)
                item = by_name.get(str(name))
                if item:
                    val = item[key] * 100 if key != "overall_score" else item[key]
                    risk = risk_level(val)
                    feature["properties"]["_risk_color"] = COLORS[risk]
                    feature["properties"]["_risk_popup"] = f"{name} · {risk} · rain {item['rain_probability']:.0%} · dry {item['dry_spell_probability']:.0%} · heavy {item['heavy_rain_probability']:.0%}"
            folium.GeoJson(geojson, name="Uploaded block boundaries", style_function=lambda f: {"color": (f.get("properties") or {}).get("_risk_color", "#78877e"), "fillColor": (f.get("properties") or {}).get("_risk_color", "#78877e"), "weight": 2, "fillOpacity": .45}, tooltip=folium.GeoJsonTooltip(fields=[next((k for k in ("block", "BLOCK", "name", "NAME", "block_name", "BLOCK_NAME") if any(k in (f.get("properties") or {}) for f in features)), "_risk_popup")]) if features else None, popup=folium.GeoJsonPopup(fields=["_risk_popup"], aliases=["Forecast"]) if any((f.get("properties") or {}).get("_risk_popup") for f in features) else None).add_to(fmap)
            return fmap
        except (OSError, ValueError, TypeError, KeyError):
            # An invalid optional boundary file should never take down the dashboard.
            pass
    for item in records:
        item = dict(item)
        val = item[key] * 100 if key != "overall_score" else item[key]
        risk = risk_level(val)
        popup = f"<b>DEMO location — {item['block']}</b><br>Rain probability: {item['rain_probability']:.0%}<br>Dry spell risk: {item['dry_spell_probability']:.0%}<br>Heavy rain risk: {item['heavy_rain_probability']:.0%}<br>Expected 7-day rainfall: {item['expected_rainfall']:.1f} mm<br>Overall risk: {risk}"
        folium.CircleMarker([item["latitude"], item["longitude"]], radius=11, color=COLORS[risk], fill=True, fill_opacity=.8, tooltip=item["block"], popup=folium.Popup(popup, max_width=300)).add_to(fmap)
    return fmap
