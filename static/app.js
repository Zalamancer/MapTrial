// ---------------------------------------------------------------------------
// Earth Engine Explorer — Frontend
// ---------------------------------------------------------------------------

(function () {
  "use strict";

  // ---- Map init ----
  const map = L.map("map", {
    center: [20, 0],
    zoom: 3,
    zoomControl: true,
  });

  // Base layer: OpenStreetMap
  const osmBase = L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
      attribution: "&copy; OpenStreetMap contributors",
      maxZoom: 18,
    }
  ).addTo(map);

  // Dark base layer option
  const darkBase = L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    {
      attribution: "&copy; CARTO",
      maxZoom: 19,
    }
  );

  // Satellite base layer option
  const satelliteBase = L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    {
      attribution: "&copy; Esri",
      maxZoom: 18,
    }
  );

  L.control
    .layers(
      { OpenStreetMap: osmBase, Dark: darkBase, Satellite: satelliteBase },
      null,
      { position: "topright" }
    )
    .addTo(map);

  // ---- State ----
  const activeLayers = {}; // layer_id -> L.TileLayer
  let currentOpacity = 0.7;

  // ---- Coordinate display ----
  const coordsEl = document.getElementById("coords");
  const zoomEl = document.getElementById("zoom-level");

  map.on("mousemove", function (e) {
    coordsEl.textContent =
      "Lat: " + e.latlng.lat.toFixed(4) + ", Lng: " + e.latlng.lng.toFixed(4);
  });

  map.on("zoomend", function () {
    zoomEl.textContent = "Zoom: " + map.getZoom();
  });

  // ---- Opacity slider ----
  const opacitySlider = document.getElementById("opacity-slider");
  const opacityValue = document.getElementById("opacity-value");

  opacitySlider.addEventListener("input", function () {
    currentOpacity = parseFloat(this.value);
    opacityValue.textContent = Math.round(currentOpacity * 100) + "%";
    Object.values(activeLayers).forEach(function (tl) {
      tl.setOpacity(currentOpacity);
    });
  });

  // ---- Layer toggle ----
  document.querySelectorAll('input[data-layer]').forEach(function (cb) {
    cb.addEventListener("change", function () {
      const layerId = this.dataset.layer;
      if (this.checked) {
        enableLayer(layerId);
      } else {
        disableLayer(layerId);
      }
    });
  });

  function enableLayer(layerId) {
    if (activeLayers[layerId]) return;

    const loadingEl = document.getElementById("loading-" + layerId);
    if (loadingEl) loadingEl.style.display = "block";

    fetch("/api/maps/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ layer_id: layerId }),
    })
      .then(function (r) {
        if (!r.ok) throw new Error("Failed to create map: " + r.status);
        return r.json();
      })
      .then(function (data) {
        const tileUrl = data.tileUrlTemplate
          .replace("{z}", "{z}")
          .replace("{x}", "{x}")
          .replace("{y}", "{y}");

        const tileLayer = L.tileLayer(tileUrl, {
          opacity: currentOpacity,
          maxZoom: 18,
          attribution: "Google Earth Engine",
        });

        tileLayer.addTo(map);
        activeLayers[layerId] = tileLayer;

        if (loadingEl) loadingEl.style.display = "none";
      })
      .catch(function (err) {
        console.error("Error enabling layer", layerId, err);
        if (loadingEl) {
          loadingEl.textContent = "Error loading layer.";
          loadingEl.style.color = "#ff6b6b";
        }
        // Uncheck the checkbox
        const cb = document.querySelector(
          'input[data-layer="' + layerId + '"]'
        );
        if (cb) cb.checked = false;
      });
  }

  function disableLayer(layerId) {
    const tileLayer = activeLayers[layerId];
    if (tileLayer) {
      map.removeLayer(tileLayer);
      delete activeLayers[layerId];
    }
  }

  // ---- AI Chat ----
  const chatMessages = document.getElementById("chat-messages");
  const chatInput = document.getElementById("chat-input");
  const chatSend = document.getElementById("chat-send");
  const chatHistory = [];

  function appendMessage(role, text) {
    const div = document.createElement("div");
    div.className = "chat-msg " + role;
    div.textContent = text;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function sendChat() {
    const message = chatInput.value.trim();
    if (!message) return;

    appendMessage("user", message);
    chatInput.value = "";

    chatHistory.push({ role: "user", parts: [message] });

    fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: message, history: chatHistory }),
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        if (data.error) {
          appendMessage("ai", "Error: " + data.error);
          return;
        }
        appendMessage("ai", data.response);
        chatHistory.push({ role: "model", parts: [data.response] });

        // Auto-activate suggested layers
        if (data.suggestedLayers && data.suggestedLayers.length > 0) {
          data.suggestedLayers.forEach(function (lid) {
            const cb = document.querySelector(
              'input[data-layer="' + lid + '"]'
            );
            if (cb && !cb.checked) {
              cb.checked = true;
              enableLayer(lid);
            }
          });
        }
      })
      .catch(function (err) {
        appendMessage("ai", "Request failed: " + err.message);
      });
  }

  chatSend.addEventListener("click", sendChat);
  chatInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") sendChat();
  });

  // Welcome message
  appendMessage(
    "ai",
    "Welcome! I can help you explore Earth Engine data. Try asking about elevation, vegetation, temperature, or land cover."
  );
})();
