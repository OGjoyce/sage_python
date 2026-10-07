"""The OpenAI-backed tool-calling loop: write a scene script, run it
through real Blender, read back what happened, repeat. Three tools only
-- write_scene_script, run_blender, finish -- so the model's blast radius
is exactly "one scene script, run through Blender," never an open shell.
"""

import json
import os

from . import config, sandbox
from .system_prompt import SYSTEM_PROMPT

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "write_scene_script",
            "description": (
                "Write (or overwrite) the full Blender scene script for this "
                "session. This does not run it -- call run_blender next."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Complete contents of the Python scene script."},
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_blender",
            "description": (
                "Run the current scene script headlessly through real Blender. "
                "Returns returncode, stdout/stderr tails, and any new render "
                "file paths."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": (
                "Call once the scene script runs with no errors and matches "
                "the request. No further tool calls after this."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "summary": {
                        "type": "string",
                        "description": "What was built, the triangle count achieved, "
                                       "and anything the requester should double-check visually.",
                    },
                },
                "required": ["success", "summary"],
            },
        },
    },
]


def _build_initial_messages(session):
    spec = session.spec
    user_msg = "Build a Blender scene script for this request:\n" + json.dumps(spec, indent=2)
    if spec.get("reference_image"):
        user_msg += (
            f"\n\nA reference image was provided, at this path (relative to "
            f"studio/): {spec['reference_image']}"
        )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]


def _dispatch_tool(session, name, args, on_event):
    iteration = session.meta.get("iterations", 0)

    if name == "write_scene_script":
        code = args.get("code", "")
        session.save_scene_script(code)
        session.append_log(f"[iter {iteration}] write_scene_script ({len(code)} bytes)")
        if on_event:
            on_event("write_scene_script", {"bytes": len(code)})
        return {"ok": True, "path": os.path.relpath(session.scene_path, config.STUDIO_ROOT)}

    if name == "run_blender":
        result = sandbox.run_blender_script(session.scene_path)
        session.append_log(
            f"[iter {iteration}] run_blender ok={result['ok']} "
            f"returncode={result['returncode']} timed_out={result['timed_out']} "
            f"renders={result['render_paths']}"
        )
        if on_event:
            on_event("run_blender", result)
        return {
            "ok": result["ok"],
            "returncode": result["returncode"],
            "timed_out": result["timed_out"],
            "stdout_tail": result["stdout"][-4000:],
            "stderr_tail": result["stderr"][-4000:],
            "render_paths": [os.path.relpath(p, config.STUDIO_ROOT) for p in result["render_paths"]],
            "export_paths": [os.path.relpath(p, config.STUDIO_ROOT) for p in result["export_paths"]],
            "warning": result["warning"],
        }

    if name == "finish":
        session.append_log(f"[iter {iteration}] finish success={args.get('success')}: {args.get('summary', '')}")
        if on_event:
            on_event("finish", args)
        return {"ok": True}

    return {"ok": False, "error": f"unknown tool '{name}'"}


def run_session(session, max_iterations=None, on_event=None):
    """Drives up to `max_iterations` rounds of model-turn -> tool-call(s)
    -> result, persisting the conversation after every round so a crashed
    or interrupted run can be resumed with the same session id. Returns
    {finished, success, summary, iterations}."""
    api_key = config.require_api_key()  # proxy-injected auth -- see config.py
    from openai import OpenAI

    max_iterations = max_iterations or config.MAX_ITERATIONS
    client = OpenAI(api_key=api_key)

    messages = session.conversation
    if not messages:
        messages = _build_initial_messages(session)

    finished = False
    success = False
    summary = None

    for _ in range(max_iterations):
        session.bump_iterations()
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        msg = response.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            messages.append({
                "role": "user",
                "content": "Use one of your tools (write_scene_script, run_blender, finish) to continue.",
            })
            session.save_conversation(messages)
            continue

        stop = False
        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            result = _dispatch_tool(session, name, args, on_event)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)[:8000],
            })
            if name == "finish":
                finished = True
                success = bool(args.get("success"))
                summary = args.get("summary")
                stop = True

        session.save_conversation(messages)
        if stop:
            break

    session.set_status("done" if finished else "incomplete")
    return {
        "finished": finished,
        "success": success,
        "summary": summary,
        "iterations": session.meta["iterations"],
    }
