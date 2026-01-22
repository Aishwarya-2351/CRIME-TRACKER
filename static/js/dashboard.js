// Initialize map (Bangalore default)
const map = L.map("map").setView([12.9716, 77.5946], 12);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors"
}).addTo(map);

let heatLayer = null;
let heatVisible = true;

let markersLayer = L.layerGroup().addTo(map);

// Load heatmap
async function loadHeatmap() {
  const res = await fetch("/api/heatmap");
  const points = await res.json();

  heatLayer = L.heatLayer(points, {
    radius: 25,
    blur: 18,
    maxZoom: 17
  }).addTo(map);
}

// Toggle heatmap
function toggleHeatmap() {
  if (!heatLayer) return;

  if (heatVisible) {
    map.removeLayer(heatLayer);
    heatVisible = false;
  } else {
    heatLayer.addTo(map);
    heatVisible = true;
  }
}

// Load station crimes markers
async function loadStationCrimes() {
  markersLayer.clearLayers();

  const station = document.getElementById("station").value;
  const res = await fetch(`/api/crimes?station=${encodeURIComponent(station)}`);
  const crimes = await res.json();

  crimes.forEach(c => {
    const marker = L.marker([c.latitude, c.longitude]);
    marker.bindPopup(`
      <b>${station}</b><br>
      <b>Place:</b> ${c.place}<br>
      <b>Date:</b> ${c.date}<br>
      <b>Time:</b> ${c.time}
    `);
    markersLayer.addLayer(marker);
  });

  if (crimes.length > 0) {
    map.setView([crimes[0].latitude, crimes[0].longitude], 13);
  }
}

// Predict risk
async function predictRisk() {
  const police_station = document.getElementById("station").value;
  const date = document.getElementById("date").value;
  const time = document.getElementById("time").value;

  if (!date || !time) {
    alert("Please select date and time!");
    return;
  }

  const res = await fetch("/api/predict_risk", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ police_station, date, time })
  });

  const data = await res.json();

  const riskEl = document.getElementById("riskResult");

  if (data.error) {
    riskEl.innerText = "Error!";
    return;
  }

  riskEl.innerText = data.risk;

  // Risk color
  if (data.risk === "LOW") riskEl.style.color = "#22c55e";
  if (data.risk === "MEDIUM") riskEl.style.color = "#facc15";
  if (data.risk === "HIGH") riskEl.style.color = "#ef4444";
}

// Initial load
loadHeatmap();
loadStationCrimes();
function showTab(tabName){
  document.getElementById("predictionTab").style.display = "none";
  document.getElementById("heatmapTab").style.display = "none";
  document.getElementById("safetyTab").style.display = "none";

  if(tabName === "prediction") document.getElementById("predictionTab").style.display = "block";
  if(tabName === "heatmap") document.getElementById("heatmapTab").style.display = "block";
  if(tabName === "safety") document.getElementById("safetyTab").style.display = "block";
}
