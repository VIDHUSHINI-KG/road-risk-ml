import streamlit as st
import requests
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("🚦SafeX - AI Road Risk Analysis")



# ---------- Geocoding ----------
def geocode(place):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": place, "format": "json", "limit": 1}
    headers = {"User-Agent": "road-risk-ml"}
    res = requests.get(url, params=params, headers=headers)

    if res.status_code != 200:
        return None, None

    data = res.json()
    if not data:
        return None, None

    return float(data[0]["lat"]), float(data[0]["lon"])


# ---------- USER INPUT ----------
source = st.text_input("📍 Source", "Velachery, Chennai")
destination = st.text_input("🏁 Destination", "Thoraipakkam, Chennai")

road_safety = st.toggle("🛡️ Road Safety Mode", True)
show_heatmap = st.checkbox("🔥 Show Accident Hotspots", value=True)

if st.button("🗺️ Start Navigation"):

    # ---------- GEOCODE ----------
    src_lat, src_lng = geocode(source)
    dst_lat, dst_lng = geocode(destination)

    if src_lat is None or dst_lat is None:
        st.error("❌ Invalid location name")
        st.stop()

    # ---------- BACKEND: RISK ----------
    response = requests.post(
        "http://127.0.0.1:5000/predict",
        json={"lat": src_lat, "lng": src_lng}
    )

    if response.status_code != 200:
        st.error("❌ Backend error. Please try again.")
        st.stop()

    data = response.json()
    risk = data["final_risk"]

    # ---------- ALERTS ----------
    if risk == "LOW":
        st.success("✅ Road is SAFE to travel now")
    elif risk == "MODERATE":
        st.warning(f"⚠️ Moderate risk due to {data['weather']} conditions")
    else:
        st.error(
            f"🚨 HIGH RISK detected at {data['time_hour']} hrs due to "
            f"{data['weather']} & low visibility"
        )

    st.info(
        f"🕒 Time: {data['time_hour']} hrs | "
        f"🌦️ Weather: {data['weather']} | "
        f"👁️ Visibility: {data['visibility_km']} km"
    )

    # ---------- BACKEND: HOTSPOTS ----------
    hotspot_data = []
    if show_heatmap:
        hotspot_response = requests.get("http://127.0.0.1:5000/hotspots")
        if hotspot_response.status_code == 200:
            hotspot_data = hotspot_response.json()

    # ---------- MAP ----------
    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8"/>
        <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
        <link rel="stylesheet" href="https://unpkg.com/leaflet-routing-machine/dist/leaflet-routing-machine.css"/>
        <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
        <script src="https://unpkg.com/leaflet-routing-machine/dist/leaflet-routing-machine.js"></script>
        <script src="https://unpkg.com/leaflet.heat/dist/leaflet-heat.js"></script>
        <style>
            #map {{ height: 600px; }}
        </style>
    </head>
    <body>
        <div id="map"></div>

        <script>
            var map = L.map('map').setView([{src_lat}, {src_lng}], 13);

            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap'
            }}).addTo(map);

            // ROUTE
            L.Routing.control({{
                waypoints: [
                    L.latLng({src_lat}, {src_lng}),
                    L.latLng({dst_lat}, {dst_lng})
                ],
                showAlternatives: {str(risk == "HIGH").lower()},
                lineOptions: {{
                    styles: [{{ color: "{'red' if risk=='HIGH' else 'green'}", weight: 5 }}]
                }}
            }}).addTo(map);

            // HEATMAP
            var heatPoints = {hotspot_data};
            if (heatPoints.length > 0) {{
                L.heatLayer(heatPoints, {{
                    radius: 25,
                    blur: 18,
                    maxZoom: 13
                }}).addTo(map);
            }}
        </script>
    </body>
    </html>
    """

    components.html(map_html, height=620)


