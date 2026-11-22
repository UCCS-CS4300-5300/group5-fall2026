"""
The purpose for this AI chef is for it to create an interaction between 
the user and the current application through a chatbot interface. The Chatbot
should be able to give the user 3 recipes from what they have in their pantry
at the moment that call is made. If there is no items in the pantry, the AI
chatbot should be able to say that. The chatbot should ideally be free but fast,
although that might prove to be a hard to find model, although gemini offers AI models
for this purpose which I will use for the time being.
"""

import logging
import os
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# Free tier model: (There are two options with gemini: "gemini-3.8-flash" or "gemini-3.5-flash-lite")
DEFAULT_CHEF_MODEL = os.getenv("AI_CHEF_MODEL", "gemini-3.5-flash-lite")

API_KEY_ENV_VAR = "GEMINI_API_KEY"
CHEF_API_KEY = ""

FALLBACK_MESSAGE_1 = "The Chef is cleaning the kitchen, come back later..."
FALLBACK_MESSAGE_2 = "The Chef is busy right now, come back later..."

CHEF_SYSTEM_PROMPT = """
You are a helpful, practical AI kitchen chef inside a pantry organizer app.
- When given a list of pantry items, recommend a clear top 3 list of recipes using what the user already has.
- If the pantry is empty or has no usable items, clearly tell the user their pantry is currently empty, and optionally ask what ingredients they plan to add.
- Prioritize items that are "Expiring Soon" when it makes culinary sense, and avoid suggesting "Expired" items as safe ingredients.
- Briefly note any basic pantry staples (like water, oil, salt, or pepper) if needed, and keep instructions concise and easy to follow and read in a sidebar chat.
- For follow-up questions, stay in character as a helpful chef and give clear,  practical answers.
- If there is any swearing or anything deemed inappropriate, dismiss it and stay in character as well.
""".strip()


# This function is in charge of making pantry items readable for the AI model.
def pantry_item_lookup(pantry_items):
    # Convert to a list so we can safely check if the pantry has anything at all
    items_list = list(pantry_items or [])
    if not items_list:
        return "The pantry is currently empty."

    usable_items = [
        item for item in items_list
        if getattr(item, "expiration_status", None) != "Expired"
    ]

    if not usable_items:
        return "No non-expired items are currently available in the pantry."

    lines = []
    for item in usable_items:
        name = getattr(item, "display_name", None) or "Unnamed item"
        qty = getattr(item, "quantity", 1)
        # Read the "location" attribute by name and default to "PANTRY"
        location = getattr(item, "location", "PANTRY")
        status = getattr(item, "expiration_status", "Unknown")
        lines.append(f"- {name} (qty: {qty}, location: {location}, status: {status})")

    return "\n".join(lines)


# This function is in charge of turning contents into the initial greeting call with 
# the top three recipes based on what the user has on the pantry
def build_content(pantry_summary, user_message=None, history=None):
    if not user_message:
        return (
            "Here is what I currently have available in my kitchen:\n"
            f"{pantry_summary}\n\n"
            "Greet me briefly as the AI Chef and give me your Top 3 recipes I can make "
            "with these ingredients (or let me know if my pantry is empty)."
        )
    parts = [f"Current kitchen inventory: \n {pantry_summary}\n"]
    if history:
        # Slice the last 6 turns so we keep recent context without going out of bounds
        for turn in history[-6:]:
            role = "Chef" if turn.get("role") == "assistant" else "User"
            text = (turn.get("text") or "").strip()
            if text:
                parts.append(f"{role}: {text}")
    parts.append(f"User: {user_message.strip()}")
    return "\n".join(parts)


# This function is in charge of sending the prompt to Gemini and handling fallbacks if anything goes wrong
def ask_chef(pantry_items, user_message=None, history=None, fallback_message=FALLBACK_MESSAGE_1):
    # Look up the GEMINI_API_KEY environment variable directly
    api_key = (CHEF_API_KEY or os.getenv(API_KEY_ENV_VAR, "")).strip()
    if not api_key:
        logger.warning("AI Chef fallback triggered: GEMINI_API_KEY is not set.")
        return {"ok": False, "reply": fallback_message, "fallback": True}

    pantry_summary = pantry_item_lookup(pantry_items)
    prompt = build_content(pantry_summary, user_message=user_message, history=history)

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=DEFAULT_CHEF_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=CHEF_SYSTEM_PROMPT,
                temperature=0.7,
            ),
        )
        reply_text = (response.text or "").strip()
        if not reply_text:
            return {"ok": False, "reply": FALLBACK_MESSAGE_2, "fallback": True}
        return {"ok": True, "reply": reply_text, "fallback": False}
    except Exception as exc:
        logger.exception("AI Chef request failed: %s", exc)
        return {"ok": False, "reply": fallback_message, "fallback": True}