from src.gis.map_builder import build_map

def test_map_builds():
    html=build_map([{"block":"Test","latitude":28.9,"longitude":77.7,"rain_probability":.5,"dry_spell_probability":.2,"heavy_rain_probability":.1,"expected_rainfall":20,"overall_score":30}]).get_root().render()
    assert "Test" in html
