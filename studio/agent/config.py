"""Configuration read from the environment -- never hardcode a key here.

Auth to OpenAI is handled by this container's own egress proxy (a
"Network secret" rule: Header, Authorization, Bearer <key>, matched to
api.openai.com), the same mechanism this environment uses for GH_TOKEN
and the cloud-provider credentials -- the proxy strips whatever
Authorization header the client sends and replaces it with the real one
for requests to the allowed host. There is no OPENAI_API_KEY in
os.environ to read; the SDK just needs *some* non-empty string to put in
that header. If this ever runs somewhere without that proxy, set
OPENAI_API_KEY to a real key and it's used as-is."""

import os

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "proxy-injected")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
MAX_ITERATIONS = int(os.environ.get("AGENT_MAX_ITERATIONS", "6"))
BLENDER_TIMEOUT_SECONDS = int(os.environ.get("AGENT_BLENDER_TIMEOUT", "300"))

# studio/ -- everything this agent touches lives under here.
STUDIO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
SESSIONS_ROOT = os.path.join(os.path.dirname(__file__), "sessions")
SCENES_ROOT = os.path.join(STUDIO_ROOT, "scenes")
RENDERS_ROOT = os.path.join(STUDIO_ROOT, "renders")


def require_api_key():
    """Returns the string to hand the OpenAI SDK as api_key. Not a real
    secret check -- see the module docstring: auth happens in the egress
    proxy, not in this process, so there is nothing here to validate
    beyond "non-empty"."""
    return OPENAI_API_KEY or "proxy-injected"
