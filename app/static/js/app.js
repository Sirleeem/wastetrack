/* Shared helpers for WasteTrack maps and UI */

function initReportPickerMap(mapId, latInputId, lngInputId, defaultLat, defaultLng, zoom) {
  const el = document.getElementById(mapId);
  if (!el || typeof L === "undefined") return null;

  const latInput = document.getElementById(latInputId);
  const lngInput = document.getElementById(lngInputId);
  let lat = parseFloat(latInput && latInput.value) || defaultLat || 10.3158;
  let lng = parseFloat(lngInput && lngInput.value) || defaultLng || 9.8442;
  zoom = zoom || 13;

  const map = L.map(mapId).setView([lat, lng], zoom);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap",
  }).addTo(map);

  let marker = L.marker([lat, lng], { draggable: true }).addTo(map);

  function sync(ll) {
    if (latInput) latInput.value = ll.lat.toFixed(6);
    if (lngInput) lngInput.value = ll.lng.toFixed(6);
  }

  sync(marker.getLatLng());
  marker.on("dragend", function () {
    sync(marker.getLatLng());
  });
  map.on("click", function (e) {
    marker.setLatLng(e.latlng);
    sync(e.latlng);
  });

  const geoBtn = document.getElementById("use-my-location");
  if (geoBtn && navigator.geolocation) {
    geoBtn.addEventListener("click", function () {
      geoBtn.disabled = true;
      geoBtn.textContent = "Locating…";
      navigator.geolocation.getCurrentPosition(
        function (pos) {
          const ll = { lat: pos.coords.latitude, lng: pos.coords.longitude };
          map.setView(ll, 16);
          marker.setLatLng(ll);
          sync(ll);
          geoBtn.disabled = false;
          geoBtn.innerHTML = '<i class="bi bi-geo-alt"></i> Use my location';
        },
        function () {
          alert("Could not get your location. Click the map instead.");
          geoBtn.disabled = false;
          geoBtn.innerHTML = '<i class="bi bi-geo-alt"></i> Use my location';
        }
      );
    });
  }

  setTimeout(function () {
    map.invalidateSize();
  }, 200);
  return map;
}

function initViewMap(mapId, lat, lng, popupText, zoom) {
  const el = document.getElementById(mapId);
  if (!el || typeof L === "undefined") return null;
  zoom = zoom || 15;
  const map = L.map(mapId).setView([lat, lng], zoom);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap",
  }).addTo(map);
  const m = L.marker([lat, lng]).addTo(map);
  if (popupText) m.bindPopup(popupText).openPopup();
  setTimeout(function () {
    map.invalidateSize();
  }, 200);
  return map;
}

function initMultiMarkerMap(mapId, points, drawOrder) {
  const el = document.getElementById(mapId);
  if (!el || typeof L === "undefined" || !points || !points.length) return null;

  const map = L.map(mapId);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap",
  }).addTo(map);

  const bounds = [];
  const latlngs = [];
  points.forEach(function (p, idx) {
    const ll = [p.lat, p.lng];
    bounds.push(ll);
    latlngs.push(ll);
    const label = p.order != null ? String(p.order) : String(idx + 1);
    const icon = L.divIcon({
      className: "",
      html:
        '<div style="background:#0f766e;color:#fff;width:28px;height:28px;border-radius:50%;' +
        "display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;" +
        'border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.3)">' +
        label +
        "</div>",
      iconSize: [28, 28],
      iconAnchor: [14, 14],
    });
    L.marker(ll, { icon: icon })
      .addTo(map)
      .bindPopup(p.popup || label);
  });

  if (drawOrder && latlngs.length > 1) {
    L.polyline(latlngs, { color: "#0f766e", weight: 3, opacity: 0.8 }).addTo(map);
  }

  map.fitBounds(bounds, { padding: [40, 40] });
  setTimeout(function () {
    map.invalidateSize();
  }, 200);
  return map;
}
