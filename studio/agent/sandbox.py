"""Runs one scene script through real Blender and reports back what
happened -- the execution sandbox the builder agent's `run_blender` tool
is built on. No bpy import here; this just shells out to the `blender`
binary, same as a human would from a terminal."""

import glob
import os
import subprocess

from . import config


def run_blender_script(script_path, timeout=None):
    """Runs `blender -b --python script_path`. Returns a dict:
    {ok, returncode, stdout, stderr, timed_out, render_paths} where
    render_paths lists any .png files under studio/renders/ newer than
    the run (best-effort -- scene scripts choose their own filepath, so
    this is a convenience, not a contract)."""
    timeout = timeout or config.BLENDER_TIMEOUT_SECONDS
    before = _renders_mtimes()

    try:
        proc = subprocess.run(
            ["blender", "-b", "--python", script_path],
            capture_output=True, text=True, timeout=timeout,
            cwd=config.STUDIO_ROOT,
        )
        timed_out = False
        returncode = proc.returncode
        stdout, stderr = proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        timed_out = True
        returncode = None
        stdout = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = (e.stderr or b"").decode("utf-8", "replace") if isinstance(e.stderr, bytes) else (e.stderr or "")

    new_renders = [p for p, mtime in _renders_mtimes().items() if before.get(p, 0) != mtime]

    return {
        "ok": (not timed_out) and returncode == 0,
        "returncode": returncode,
        "timed_out": timed_out,
        "stdout": stdout,
        "stderr": stderr,
        "render_paths": sorted(new_renders),
    }


def _renders_mtimes():
    paths = glob.glob(os.path.join(config.RENDERS_ROOT, "**", "*.png"), recursive=True)
    return {p: os.path.getmtime(p) for p in paths if os.path.exists(p)}
