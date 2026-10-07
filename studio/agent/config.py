"""Configuration read from the environment -- never hardcode a key here."""

import os

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
MAX_ITERATIONS = int(os.environ.get("AGENT_MAX_ITERATIONS", "6"))
BLENDER_TIMEOUT_SECONDS = int(os.environ.get("AGENT_BLENDER_TIMEOUT", "300"))

# studio/ -- everything this agent touches lives under here.
STUDIO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
SESSIONS_ROOT = os.path.join(os.path.dirname(__file__), "sessions")
SCENES_ROOT = os.path.join(STUDIO_ROOT, "scenes")
RENDERS_ROOT = os.path.join(STUDIO_ROOT, "renders")


def require_api_key():
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it in the environment's settings "
            "(cloud environment menu -> Edit -> Network secrets / environment "
            "variables) as OPENAI_API_KEY, then start a new session -- never "
            "paste it into a prompt or a file in this repo."
        )
    return OPENAI_API_KEY
