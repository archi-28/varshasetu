import pandas as pd
from scripts.download_data import monthly_index, daily_mjo, polygon_centroid

def test_parse_monthly_climate_indices():
    text = "1870 2026\n2020 1 2 3 4 5 6 7 8 9 10 11 12\n"
    data = monthly_index(text, "enso")
    assert len(data) == 12
    assert data.iloc[0].enso == 1
    assert data.iloc[-1].date == pd.Timestamp("2020-12-01")

def test_parse_bom_daily_mjo():
    text = "year month day RMM1 RMM2 phase amplitude\n2024 6 1 1.0 0.5 4 1.1\n"
    data = daily_mjo(text)
    assert data.iloc[0].mjo_phase == 4
    assert data.iloc[0].mjo_amplitude == 1.1

def test_geojson_polygon_centroid():
    geometry = {"type":"Polygon", "coordinates":[[[77,28],[79,28],[79,30],[77,30],[77,28]]]}
    lat, lon = polygon_centroid(geometry)
    assert (lat, lon) == (29.0, 78.0)
