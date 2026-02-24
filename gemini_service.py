"""Gemini AI integration for natural language Earth Engine queries."""

import json

import google.generativeai as genai

import config
import ee_service

# Layer descriptions for the AI context
_LAYER_CONTEXT = """You are an assistant for a Google Earth Engine map application.
You help users explore geospatial data layers.

Available data layers:
{layers}

When the user asks about geographic features, environmental data, or wants to
visualize something on the map, suggest the most appropriate layer(s) and
explain what the data shows.

When asked to analyze or compare, describe what the data layers reveal about
the requested area or topic.

Respond in concise, informative paragraphs. If suggesting a layer, include its
ID in your response wrapped like this: [layer:layer_id] so the frontend can
auto-activate it.
"""


def _get_model():
    """Initialize and return the Gemini model."""
    genai.configure(api_key=config.GEMINI_API_KEY)
    return genai.GenerativeModel("gemini-2.0-flash")


def build_system_prompt() -> str:
    """Build the system prompt with current layer information."""
    layers_text = ""
    for layer in ee_service.list_layers():
        layers_text += (
            f"- {layer['id']}: {layer['name']} — {layer['description']} "
            f"(dataset: {layer['dataset']})\n"
        )
    return _LAYER_CONTEXT.format(layers=layers_text)


def chat(user_message: str, history: list[dict] | None = None) -> str:
    """Send a message to Gemini and return the response.

    Args:
        user_message: The user's natural language query.
        history: Optional list of previous messages as
                 [{"role": "user"|"model", "parts": ["text"]}, ...].
    Returns:
        The model's text response.
    """
    if not config.GEMINI_API_KEY:
        return (
            "Gemini API key is not configured. Set the GEMINI_API_KEY "
            "environment variable to enable AI-powered queries."
        )

    model = _get_model()
    chat_history = history or []
    convo = model.start_chat(history=chat_history)
    response = convo.send_message(
        f"[System context]\n{build_system_prompt()}\n\n[User]\n{user_message}"
    )
    return response.text
