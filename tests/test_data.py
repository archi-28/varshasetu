import pandas as pd
from src.data.validator import validate_weather_frame, REQUIRED

def test_required_column_validation():
    assert any("Missing required column" in e for e in validate_weather_frame(pd.DataFrame()))

def test_generated_data_valid():
    frame = pd.DataFrame([{c: ("2024-01-01" if c == "date" else "Meerut" if c == "district" else "Block" if c == "block" else 1) for c in REQUIRED}])
    assert validate_weather_frame(frame) == []
