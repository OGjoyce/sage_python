"""A session is a plain directory on disk -- no hosted page, no hidden
database. Everything about one model-build attempt (the request, the
running conversation with the OpenAI agent, every scene script it wrote,
and a human-readable log) lives under studio/agent/sessions/<id>/ where
it can be read with a normal text editor."""

import json
import os
import re
import time
import uuid

from . import config


def _slugify(name):
    s = "".join(c if c.isalnum() else "_" for c in name.strip().lower())
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_") or "model"


class Session:
    def __init__(self, session_id):
        self.id = session_id
        self.dir = os.path.join(config.SESSIONS_ROOT, session_id)

    # ---------------------------------------------------------- lifecycle --
    @classmethod
    def create(cls, spec):
        """spec: {name, prompt, colors, triangleBudget, includeScene,
        includeLights, lightPreset, outputFormats, reference_image (path
        or None)}. Returns a new Session with a fresh id/slug."""
        slug = _slugify(spec.get("name") or spec.get("prompt", "model")[:24])
        session_id = f"{slug}_{uuid.uuid4().hex[:6]}"
        session = cls(session_id)
        os.makedirs(session.dir, exist_ok=True)

        meta = {
            "id": session_id,
            "slug": slug,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "new",
            "iterations": 0,
        }
        session._write_json("meta.json", meta)
        session._write_json("spec.json", spec)
        session._write_json("conversation.json", [])
        open(session.log_path, "a").close()
        return session

    @classmethod
    def load(cls, session_id):
        session = cls(session_id)
        if not os.path.isdir(session.dir):
            raise FileNotFoundError(f"no session '{session_id}' under {config.SESSIONS_ROOT}")
        return session

    @classmethod
    def list_all(cls):
        if not os.path.isdir(config.SESSIONS_ROOT):
            return []
        out = []
        for name in sorted(os.listdir(config.SESSIONS_ROOT)):
            if os.path.isdir(os.path.join(config.SESSIONS_ROOT, name)):
                try:
                    out.append(cls.load(name))
                except FileNotFoundError:
                    continue
        return out

    # ------------------------------------------------------------- paths --
    @property
    def log_path(self):
        return os.path.join(self.dir, "log.txt")

    @property
    def scene_path(self):
        """Where this session's scene script lives for real, under
        studio/scenes/ -- the same place a hand-written scene script
        would go, so blender's own sys.path.insert(..'..') trick resolves
        claude_studio correctly."""
        return os.path.join(config.SCENES_ROOT, f"{self.slug}_scene.py")

    @property
    def slug(self):
        return self.meta["slug"]

    # -------------------------------------------------------------- data --
    @property
    def meta(self):
        return self._read_json("meta.json")

    @property
    def spec(self):
        return self._read_json("spec.json")

    @property
    def conversation(self):
        return self._read_json("conversation.json")

    def set_status(self, status):
        meta = self.meta
        meta["status"] = status
        self._write_json("meta.json", meta)

    def bump_iterations(self):
        meta = self.meta
        meta["iterations"] = meta.get("iterations", 0) + 1
        self._write_json("meta.json", meta)
        return meta["iterations"]

    def save_conversation(self, messages):
        self._write_json("conversation.json", messages)

    def save_scene_script(self, code):
        os.makedirs(os.path.dirname(self.scene_path), exist_ok=True)
        with open(self.scene_path, "w") as f:
            f.write(code)
        # also keep a copy inside the session dir, so the session is a
        # complete, self-contained record even if studio/scenes/ changes later
        with open(os.path.join(self.dir, "scene.py"), "w") as f:
            f.write(code)

    def append_log(self, text):
        with open(self.log_path, "a") as f:
            f.write(text.rstrip("\n") + "\n")

    # ------------------------------------------------------------- helpers --
    def _read_json(self, name):
        with open(os.path.join(self.dir, name)) as f:
            return json.load(f)

    def _write_json(self, name, data):
        with open(os.path.join(self.dir, name), "w") as f:
            json.dump(data, f, indent=2)
