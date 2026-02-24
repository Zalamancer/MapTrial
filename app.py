"""Flask application — Earth Engine Explorer with Gemini AI."""

import json
import logging
import os
import traceback

from flask import Flask, jsonify, request, render_template, Response

import config
import ee_auth
import ee_service
import gemini_service

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static", template_folder="templates")

# In-memory cache for map tile URLs (layer_id -> map resource name)
_map_cache: dict[str, str] = {}


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    """Serve the main map application page."""
    return render_template("index.html", layers=ee_service.list_layers())


# ---------------------------------------------------------------------------
# Earth Engine API routes
# ---------------------------------------------------------------------------


@app.route("/api/layers")
def api_layers():
    """Return available data layer metadata."""
    return jsonify(ee_service.list_layers())


@app.route("/api/maps/create", methods=["POST"])
def api_create_map():
    """Create an Earth Engine map for a given layer.

    Request body: {"layer_id": "elevation"}
    Response: {"mapName": "projects/.../maps/...", "tileUrlTemplate": "..."}
    """
    body = request.get_json(force=True)
    layer_id = body.get("layer_id")
    if not layer_id:
        return jsonify({"error": "layer_id is required"}), 400

    if layer_id not in ee_service.DATA_LAYERS:
        return jsonify({"error": f"Unknown layer: {layer_id}"}), 404

    try:
        # Check cache first
        if layer_id in _map_cache:
            map_name = _map_cache[layer_id]
            return jsonify(
                {
                    "mapName": map_name,
                    "tileUrlTemplate": (
                        f"/api/tiles/{layer_id}/{{z}}/{{x}}/{{y}}"
                    ),
                }
            )

        ee_map = ee_service.create_map(layer_id)
        map_name = ee_map.get("name", "")
        _map_cache[layer_id] = map_name
        log.info("Created map for layer %s: %s", layer_id, map_name)

        return jsonify(
            {
                "mapName": map_name,
                "tileUrlTemplate": (
                    f"/api/tiles/{layer_id}/{{z}}/{{x}}/{{y}}"
                ),
            }
        )
    except Exception as e:
        log.error("Failed to create map for %s: %s", layer_id, traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/api/tiles/<layer_id>/<int:z>/<int:x>/<int:y>")
def api_tile(layer_id: str, z: int, x: int, y: int):
    """Proxy a tile request to Earth Engine.

    This avoids CORS issues and keeps the auth token server-side.
    """
    map_name = _map_cache.get(layer_id)
    if not map_name:
        return jsonify({"error": "Map not created yet. Call /api/maps/create first."}), 400

    try:
        tile_data = ee_service.fetch_tile(map_name, z, x, y)
        return Response(tile_data, content_type="image/png")
    except Exception as e:
        log.error("Tile error %s/%s/%s/%s: %s", layer_id, z, x, y, e)
        # Return a transparent 1x1 PNG on error
        return Response(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
            b"\r\n\xb4\x00\x00\x00\x00IEND\xaeB`\x82",
            content_type="image/png",
        )


# ---------------------------------------------------------------------------
# Gemini AI chat route
# ---------------------------------------------------------------------------


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Process a natural language query via Gemini AI.

    Request body: {"message": "Show me vegetation in the Amazon"}
    Response: {"response": "...", "suggestedLayers": ["ndvi"]}
    """
    body = request.get_json(force=True)
    message = body.get("message", "")
    history = body.get("history", [])

    if not message:
        return jsonify({"error": "message is required"}), 400

    try:
        response_text = gemini_service.chat(message, history)

        # Extract suggested layers from [layer:xxx] markers
        suggested = []
        import re

        for match in re.finditer(r"\[layer:(\w+)\]", response_text):
            lid = match.group(1)
            if lid in ee_service.DATA_LAYERS:
                suggested.append(lid)

        # Remove the markers from the displayed text
        clean_text = re.sub(r"\[layer:(\w+)\]", "", response_text).strip()

        return jsonify({"response": clean_text, "suggestedLayers": suggested})
    except Exception as e:
        log.error("Chat error: %s", traceback.format_exc())
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
