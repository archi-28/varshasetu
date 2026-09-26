"""Download Meerut block boundaries and ERA5-Land / climate-index history.

Network access is required. Weather is gridded reanalysis at block centroids,
not station observations. Existing demo CSVs remain untouched.
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import requests

from src.config import ROOT, load_config

BOUNDARY_QUERY = (
    "https://bharatnetprogress.nic.in/nicclouddb/rest/services/NCR/"
    "NCR_Geo_Portal_23_01_2025/MapServer/5/query"
)
NINO_URL = "https://psl.noaa.gov/data/timeseries/month/data/nino34.long.anom.data"
DMI_URL = "https://psl.noaa.gov/data/timeseries/month/data/dmi.had.long.data"
MJO_URL = "https://www.bom.gov.au/climate/mjo/graphics/rmm.74toRealtime.txt"
WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
WEATHER_VARS = ["temperature_2m", "relative_humidity_2m", "precipitation",
                "wind_speed_10m", "pressure_msl", "soil_moisture_0_to_7cm"]


def fetch_text(url: str) -> str:
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    return response.text


def monthly_index(text: str, column: str) -> pd.DataFrame:
    rows = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) != 13 or not parts[0].isdigit():
            continue
        year = int(parts[0])
        if year < 1800:
            continue
        for month, raw_value in enumerate(parts[1:], 1):
            value = float(raw_value)
            if value <= -90 or abs(value) > 1e10:
                continue
            rows.append({"date": pd.Timestamp(year=year, month=month, day=1), column: value})
    if not rows:
        raise ValueError(f"Could not parse monthly index: {column}")
    return pd.DataFrame(rows)


def daily_mjo(text: str) -> pd.DataFrame:
    rows = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 7 or not all(re.fullmatch(r"\d+", x) for x in parts[:3]):
            continue
        try:
            year, month, day = map(int, parts[:3])
            phase, amplitude = int(float(parts[5])), float(parts[6])
            if phase in range(1, 9) and 0 <= amplitude < 1e10:
                rows.append({"date": pd.Timestamp(year, month, day),
                             "mjo_phase": phase, "mjo_amplitude": amplitude})
        except (ValueError, OverflowError):
            continue
    if not rows:
        raise ValueError("Could not parse daily BOM RMM/MJO index")
    return pd.DataFrame(rows).drop_duplicates("date", keep="last")


def normalize_name(value: str) -> str:
    name = re.sub(r"[^a-z]", "", str(value).lower())
    return {"jani": "jaani", "machara": "machra", "machra": "machra"}.get(name, name)


def polygon_centroid(geometry: dict) -> tuple[float, float]:
    """Area-weighted polygon centroid; returns (latitude, longitude)."""
    polygons = geometry.get("coordinates", [])
    if geometry.get("type") == "Polygon":
        polygons = [polygons]
    area_sum = cx_sum = cy_sum = 0.0
    for polygon in polygons:
        if not polygon:
            continue
        ring = polygon[0]
        cross_sum = x_sum = y_sum = 0.0
        for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
            cross = x1 * y2 - x2 * y1
            cross_sum += cross
            x_sum += (x1 + x2) * cross
            y_sum += (y1 + y2) * cross
        area = abs(cross_sum) / 2
        if area:
            cx_sum += (x_sum / (3 * cross_sum)) * area
            cy_sum += (y_sum / (3 * cross_sum)) * area
            area_sum += area
    if not area_sum:
        raise ValueError("Boundary polygon has no usable outer ring")
    return cy_sum / area_sum, cx_sum / area_sum


def download_boundaries() -> dict | None:
    cfg = load_config()
    params = {"where": "1=1", "outFields": "*", "outSR": "4326",
              "returnGeometry": "true", "f": "geojson"}
    try:
        response = requests.get(BOUNDARY_QUERY, params=params, timeout=(10, 30))
        response.raise_for_status()
    except requests.RequestException as exc:
        # The NIC service is sometimes unreachable. Keep the weather refresh useful
        # using the configured block-center coordinates; don't invent polygons.
        print(f"Warning: NIC boundaries unavailable ({exc}). Continuing with configured block-center coordinates; map polygons were not updated.")
        return None
    geo = response.json()
    if "features" not in geo:
        raise ValueError(f"Boundary service response is not GeoJSON: {str(geo)[:300]}")
    expected = {normalize_name(block): block for block in cfg["blocks"]}
    selected = []
    seen = set()
    for feature in geo["features"]:
        props = feature.get("properties") or {}
        district = str(props.get("district", props.get("DISTRICT", ""))).strip().lower()
        state = str(props.get("state", props.get("STATE", ""))).strip().lower()
        block_raw = props.get("block_name", props.get("BLOCK_NAME", props.get("block", "")))
        block = expected.get(normalize_name(block_raw))
        if block and "meerut" in district and ("uttar" in state or "up" == state):
            feature["properties"]["block_name"] = block
            selected.append(feature)
            seen.add(block)
    missing = sorted(set(cfg["blocks"]) - seen)
    if missing:
        raise ValueError("Official boundary query did not return all configured Meerut blocks. Missing: " + ", ".join(missing))
    result = {"type": "FeatureCollection", "name": "Meerut CD Blocks",
              "source": "NIC Bharat Maps NCR Blocks layer (2023)", "features": selected}
    path = ROOT / "data" / "geo" / "meerut_blocks.geojson"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(selected)} NIC block polygons to {path}")
    return result


def download_weather(boundaries: dict | None, start_date: str, end_date: str) -> pd.DataFrame:
    cfg = load_config()
    coords = dict(cfg["blocks"])
    if boundaries is not None:
        for feature in boundaries["features"]:
            props = feature["properties"]
            coords[props["block_name"]] = polygon_centroid(feature["geometry"])
    names = list(cfg["blocks"])
    latitudes = [coords[n][0] for n in names]
    longitudes = [coords[n][1] for n in names]
    params = {"latitude": ",".join(map(str, latitudes)),
              "longitude": ",".join(map(str, longitudes)),
              "start_date": start_date, "end_date": end_date,
              "hourly": ",".join(WEATHER_VARS), "timezone": "Asia/Kolkata",
              "models": "era5_land", "wind_speed_unit": "kmh", "precipitation_unit": "mm"}
    response = requests.get(WEATHER_URL, params=params, timeout=180)
    response.raise_for_status()
    payload = response.json()
    locations = payload if isinstance(payload, list) else [payload]
    if len(locations) != len(names):
        raise ValueError(f"Weather API returned {len(locations)} locations for {len(names)} blocks")
    daily_frames = []
    for name, location in zip(names, locations):
        hourly = location.get("hourly", {})
        weather = pd.DataFrame(hourly)
        if weather.empty or "time" not in weather:
            raise ValueError(f"Weather API returned no hourly data for {name}")
        weather["date"] = pd.to_datetime(weather.pop("time")).dt.normalize()
        daily = weather.groupby("date", as_index=False).agg(
            rainfall_mm=("precipitation", "sum"), temperature_c=("temperature_2m", "mean"),
            humidity_pct=("relative_humidity_2m", "mean"), wind_speed_kmh=("wind_speed_10m", "mean"),
            pressure_hpa=("pressure_msl", "mean"), soil_moisture=("soil_moisture_0_to_7cm", "mean"))
        lat, lon = coords[name]
        daily["district"], daily["block"] = "Meerut", name
        daily["latitude"], daily["longitude"] = lat, lon
        daily_frames.append(daily)
    return pd.concat(daily_frames, ignore_index=True)


def download_real_data(start_date: str = "2020-01-01") -> Path:
    end_date = (date.today() - timedelta(days=6)).isoformat()
    boundaries = download_boundaries()
    weather = download_weather(boundaries, start_date, end_date)
    weather_dates = pd.DatetimeIndex(pd.to_datetime(weather["date"]).unique()).sort_values()
    enso = monthly_index(fetch_text(NINO_URL), "enso")
    iod = monthly_index(fetch_text(DMI_URL), "iod")
    climate = pd.DataFrame({"date": weather_dates})
    for monthly in (enso, iod):
        monthly["month"] = monthly["date"].dt.to_period("M")
        climate["month"] = climate["date"].dt.to_period("M")
        climate = climate.merge(monthly.drop(columns="date"), on="month", how="left")
        climate = climate.drop(columns="month")
    mjo = daily_mjo(fetch_text(MJO_URL))
    climate = climate.merge(mjo, on="date", how="left").sort_values("date")
    climate[["mjo_phase", "mjo_amplitude"]] = climate[["mjo_phase", "mjo_amplitude"]].ffill().bfill()
    result = weather.merge(climate, on="date", how="left")
    if result.isna().any().any():
        cols = result.columns[result.isna().any()].tolist()
        raise ValueError("Real data has missing values in " + ", ".join(cols))
    stamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    output = ROOT / "data" / "raw" / f"meerut_era5land_daily_{stamp}.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False)
    print(f"Saved {len(result):,} ERA5-Land/reanalysis daily rows to {output}")
    print("Climate inputs: NOAA PSL Niño 3.4 and DMI; BOM RMM daily series.")
    if boundaries is None:
        print("Map geometry was not updated. Weather locations: configured approximate block centers (config.yaml).")
    else:
        print("Map geometry: NIC Bharat Maps block layer. Weather locations: block-polygon centroids.")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", default="2020-01-01")
    args = parser.parse_args()
    try:
        download_real_data(args.start_date)
    except (requests.RequestException, ValueError, KeyError) as exc:
        raise SystemExit(f"Real data refresh failed; demo files were left untouched. Details: {exc}") from exc
