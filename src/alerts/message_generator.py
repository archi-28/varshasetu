"""SMS and WhatsApp style alert messages."""
def generate_message(district, block, crop, forecast, language="en", style="sms"):
    rain = round(forecast["rain_probability"] * 100)
    dry = round(forecast["dry_spell_probability"] * 100)
    heavy = round(forecast["heavy_rain_probability"] * 100)
    if language.lower().startswith("hi"):
        return f"📍 {district} — {block}\n🌧️ VarshaSetu चेतावनी\nअगले {forecast['horizon']} दिनों में वर्षा संभावना: {rain}% | शुष्क अवधि जोखिम: {dry}% | भारी वर्षा जोखिम: {heavy}%\n🌾 फसल: {crop}\nखेत की जल निकासी जाँचें और स्थानीय कृषि सलाह का पालन करें।\n— VarshaSetu"
    return f"📍 {district} — {block}\n🌧️ VarshaSetu Alert\nNext {forecast['horizon']} days: Rain probability {rain}% | Dry spell risk {dry}% | Heavy rain risk {heavy}%\n🌾 Crop: {crop}\nCheck drainage and follow local agricultural guidance.\n— VarshaSetu"
