const map = L.map('map').setView([12.9716, 77.5946], 13);

// OpenStreetMap layer
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
}).addTo(map);

navigator.geolocation.watchPosition(pos => {
    const lat = pos.coords.latitude;
    const lng = pos.coords.longitude;

    fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            lat: lat,
            lng: lng,
            temperature: 28,
            visibility: 10,
            precipitation: 0
        })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("riskBox").innerHTML =
            "Risk Level: " + data.risk_level;
    });
});
