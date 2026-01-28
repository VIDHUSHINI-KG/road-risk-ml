from flask import Flask, request, jsonify
import joblib
import numpy as np
import requests
from datetime import datetime
import pandas as pd
import os

app = Flask(__name__)

# ---------------- LOAD ML MODEL ----------------
model = joblib.load("risk_model.pkl")

# ---------------- WEATHER CONFIG ----------------
WEATHER_API_KEY = "45bca904bd4406671a0e34799eacb729"

# ---------------- LOAD HOTSPOT DATA ONCE ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "accidents.csv")

try:
    hotspots_df = pd.read_csv(
        DATA_PATH,
        usecols=["Start_Lat", "Start_Lng", "Severity"]
    ).dropna().sample(n=5000, random_state=42)
    print("✅ Hotspot data loaded")
except Exception as e:
    print("⚠️ Hotspot data load failed:", e)
    hotspots_df = pd.DataFrame(columns=["Start_Lat", "Start_Lng", "Severity"])


# ---------------- WEATHER FETCH ----------------
def get_weather(lat, lon):
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": WEATHER_API_KEY,
            "units": "metric"
        }
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        weather_main = data.get("weather", [{}])[0].get("main", "Clear")
        visibility = data.get("visibility", 10000) / 1000  # meters → km
        rain = data.get("rain", {}).get("1h", 0)

        return weather_main, visibility, rain

    except Exception as e:
        print("⚠️ Weather API error:", e)
        return "Clear", 10, 0


# ---------------- RISK ADJUSTMENT ----------------
def adjust_risk(base_risk, hour, weather, visibility, rain):
    risk_levels = ["LOW", "MODERATE", "HIGH"]
    risk_index = risk_levels.index(base_risk)

    # Time-based risk
    if hour >= 19 or hour <= 6:
        risk_index += 1
    if hour >= 23 or hour <= 4:
        risk_index += 1

    # Weather-based risk
    if weather in ["Rain", "Fog", "Thunderstorm"]:
        risk_index += 1
    if visibility < 2:
        risk_index += 1
    if rain > 0:
        risk_index += 1

    return risk_levels[min(risk_index, 2)]


# ---------------- HOME ----------------
@app.route("/")
def home():
    return "🚦 Road Risk ML API with Time, Weather & Hotspot Intelligence"


# ---------------- PREDICTION API ----------------
@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()

        lat = float(data["lat"])
        lng = float(data["lng"])

        # ML prediction
        features = np.array([[lat, lng, 28, 10, 0]])
        base_risk = model.predict(features)[0]

        # Time
        hour = datetime.now().hour

        # Weather
        weather, visibility, rain = get_weather(lat, lng)

        # Final risk
        final_risk = adjust_risk(
            base_risk,
            hour,
            weather,
            visibility,
            rain
        )

        return jsonify({
            "base_risk": base_risk,
            "final_risk": final_risk,
            "time_hour": hour,
            "weather": weather,
            "visibility_km": visibility,
            "rain_mm": rain
        })

    except Exception as e:
        print("❌ Prediction error:", e)
        return jsonify({"error": "Prediction failed"}), 500


# ---------------- HOTSPOT HEATMAP API ----------------
@app.route("/hotspots", methods=["GET"])
def hotspots():
    try:
        points = hotspots_df.apply(
            lambda row: [
                row["Start_Lat"],
                row["Start_Lng"],
                row["Severity"]
            ],
            axis=1
        ).tolist()

        return jsonify(points)

    except Exception as e:
        print("❌ Hotspot error:", e)
        return jsonify([])


# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(debug=True)



