"""Runs one scene script through real Blender and reports back what
happened -- the execution sandbox the builder agent's `run_blender` tool
is built on. No bpy import here; this just shells out to the `blender`
binary, same as a human would from a terminal."""

import glob
import os
import subprocess

from . import config

WATCHED_DIRS = {
    "render_paths": config.RENDERS_ROOT,
    "export_paths": os.path.join(config.STUDIO_ROOT, "exports"),
}


def run_blender_script(script_path, timeout=None):
    """Runs `blender -b --python script_path`. Returns a dict:
    {ok, returncode, stdout, stderr, timed_out, render_paths, export_paths,
    warning}. render_paths/export_paths list files newer than the run
    under studio/renders/ and studio/exports/ -- the only two places this
    harness looks, so a script that writes anywhere else (an absolute
    path, a path outside studio/) silently "succeeds" with nothing to
    show for it; `warning` calls that out explicitly rather than letting
    ok=True read as "done"."""
    timeout = timeout or config.BLENDER_TIMEOUT_SECONDS
    before = {key: _mtimes(path) for key, path in WATCHED_DIRS.items()}

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

    new_files = {}
    for key, path in WATCHED_DIRS.items():
        after = _mtimes(path)
        new_files[key] = sorted(p for p, mtime in after.items() if before[key].get(p) != mtime)

    ok = (not timed_out) and returncode == 0
    warning = None
    if ok and not new_files["render_paths"] and not new_files["export_paths"]:
        warning = (
            "run_blender succeeded (no error) but no new file appeared under "
            "studio/renders/ or studio/exports/ -- this script wrote its output "
            "somewhere else, or didn't write it at all. Scene scripts in this "
            "pipeline always build paths as "
            "os.path.join(os.path.dirname(__file__), '..', 'renders'/'exports', <name>) "
            "-- never an absolute path like /output/... or /tmp/.... "
            "Fix the output path and run again before calling finish()."
        )

    return {
        "ok": ok,
        "returncode": returncode,
        "timed_out": timed_out,
        "stdout": stdout,
        "stderr": stderr,
        "render_paths": new_files["render_paths"],
        "export_paths": new_files["export_paths"],
        "warning": warning,
    }


def _mtimes(root):
    paths = glob.glob(os.path.join(root, "**", "*"), recursive=True)
    return {p: os.path.getmtime(p) for p in paths if os.path.isfile(p)}
