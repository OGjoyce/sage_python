#!/usr/bin/env python3
"""
CLI for the OpenAI-backed model-building agent -- the "interface" for
this architecture. No web page, no claude.ai artifact: this is the whole
surface, usable by a person at a terminal or by another agent shelling
out to it.

    python3 studio/agent/cli.py start --name "Scrap Sentinel" \\
        --prompt "a small scrap-metal guard robot, boxy, one glowing eye" \\
        --colors "#4a4a4a,#ffb000" --triangles 4000 --scene --lights \\
        --light-preset dramatic --formats obj,uaig

    python3 studio/agent/cli.py continue scrap_sentinel_a1b2c3 \\
        --feedback "the eye isn't glowing -- give it an emission material"

    python3 studio/agent/cli.py show scrap_sentinel_a1b2c3
    python3 studio/agent/cli.py list
"""

import argparse
import sys

from . import config
from .builder_agent import run_session
from .session import Session


def cmd_start(args):
    spec = {
        "name": args.name,
        "prompt": args.prompt,
        "colors": [c.strip() for c in args.colors.split(",")] if args.colors else ["#8a8a8a"],
        "triangleBudget": args.triangles,
        "includeScene": args.scene,
        "includeLights": args.lights,
        "lightPreset": args.light_preset if args.lights else None,
        "outputFormats": [f.strip() for f in args.formats.split(",")] if args.formats else ["obj"],
        "reference_image": args.image,
    }
    session = Session.create(spec)
    print(f"Created session '{session.id}' (status: new)")

    if args.no_run:
        print("Skipping the build run (--no-run passed). Resume with:")
        print(f"  python3 studio/agent/cli.py continue {session.id}")
        return

    _run_and_report(session, args.iterations)


def cmd_continue(args):
    session = Session.load(args.session_id)
    if args.feedback:
        messages = session.conversation
        messages.append({"role": "user", "content": args.feedback})
        session.save_conversation(messages)
        session.append_log(f"[feedback] {args.feedback}")
    _run_and_report(session, args.iterations)


def cmd_show(args):
    session = Session.load(args.session_id)
    meta = session.meta
    spec = session.spec
    print(f"session   {session.id}")
    print(f"status    {meta.get('status')}")
    print(f"iterations {meta.get('iterations')}")
    print(f"created   {meta.get('created_at')}")
    print(f"scene     {session.scene_path}")
    print()
    print("spec:")
    for k, v in spec.items():
        print(f"  {k}: {v}")
    print()
    print(f"log (studio/agent/sessions/{session.id}/log.txt):")
    try:
        with open(session.log_path) as f:
            lines = f.readlines()
        for line in lines[-args.tail:]:
            print("  " + line.rstrip())
    except FileNotFoundError:
        print("  (no log yet)")


def cmd_list(args):
    sessions = Session.list_all()
    if not sessions:
        print(f"No sessions yet under {config.SESSIONS_ROOT}")
        return
    for session in sessions:
        meta = session.meta
        spec = session.spec
        prompt = (spec.get("prompt") or "")[:60]
        print(f"{session.id:32s} {meta.get('status', '?'):10s} iters={meta.get('iterations', 0):<3} {prompt}")


def _run_and_report(session, iterations):
    try:
        result = run_session(session, max_iterations=iterations)
    except RuntimeError as e:
        print(f"Stopped: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\nRan {result['iterations']} iteration(s). finished={result['finished']} success={result['success']}")
    if result["summary"]:
        print(f"Summary: {result['summary']}")
    if not result["finished"]:
        print(f"Did not call finish() within the iteration budget -- resume with:")
        print(f"  python3 studio/agent/cli.py continue {session.id}")
    print(f"\nFull transcript: studio/agent/sessions/{session.id}/log.txt")
    print(f"Scene script:    {session.scene_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    p_start = sub.add_parser("start", help="create a new session and start building")
    p_start.add_argument("--name", required=True)
    p_start.add_argument("--prompt", required=True)
    p_start.add_argument("--image", default=None, help="path to a reference image, relative to studio/")
    p_start.add_argument("--colors", default="", help="comma-separated hex colors, e.g. '#4a4a4a,#ffb000'")
    p_start.add_argument("--triangles", type=int, default=4000)
    p_start.add_argument("--scene", action="store_true", help="include environment/scene")
    p_start.add_argument("--lights", action="store_true", help="include a lighting setup")
    p_start.add_argument("--light-preset", default="studio", choices=["studio", "outdoor", "dramatic"])
    p_start.add_argument("--formats", default="obj", help="comma-separated: obj,uaig")
    p_start.add_argument("--iterations", type=int, default=None, help=f"default {config.MAX_ITERATIONS}")
    p_start.add_argument("--no-run", action="store_true", help="create the session but don't call OpenAI yet")
    p_start.set_defaults(func=cmd_start)

    p_cont = sub.add_parser("continue", help="keep building an existing session")
    p_cont.add_argument("session_id")
    p_cont.add_argument("--feedback", default=None, help="a note to inject before resuming")
    p_cont.add_argument("--iterations", type=int, default=None, help=f"default {config.MAX_ITERATIONS}")
    p_cont.set_defaults(func=cmd_continue)

    p_show = sub.add_parser("show", help="print a session's spec and log")
    p_show.add_argument("session_id")
    p_show.add_argument("--tail", type=int, default=40)
    p_show.set_defaults(func=cmd_show)

    p_list = sub.add_parser("list", help="list all sessions")
    p_list.set_defaults(func=cmd_list)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
