from src.agriculture.advisory_engine import generate_advisory
from src.alerts.message_generator import generate_message

def test_advisory_conditions_and_hindi():
    assert "Heavy" in generate_advisory("Rice",.5,.1,.8,40)["headline"]
    assert "शुष्क" in generate_advisory("Rice",.2,.8,.1,4,language="hi")["headline"]

def test_message_languages():
    f={"rain_probability":.82,"dry_spell_probability":.18,"heavy_rain_probability":.6,"horizon":7}
    assert "Alert" in generate_message("Meerut","Block","Rice",f)
    assert "चेतावनी" in generate_message("मेरठ","ब्लॉक","धान",f,"hi")
