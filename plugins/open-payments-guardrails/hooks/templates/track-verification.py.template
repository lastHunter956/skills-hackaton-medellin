#!/usr/bin/env python3
"""Hook PostToolUse: track-verification.py

Rastrea cambios en codigo y estado de verificacion (tsc y tests) por sesion.
Contrato: JSON stdin -> JSON stdout {}.
"""

import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(REPO_ROOT, ".agents", "state")


def get_session_file(conv_id):
    safe_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", conv_id or "default")
    return os.path.join(STATE_DIR, f"session-{safe_id}.json")


def load_session_state(session_file):
    if os.path.exists(session_file):
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "dirty": False,
        "typecheck_ok": False,
        "tests_ok": False,
        "continues": 0,
    }


def save_session_state(session_file, state):
    try:
        os.makedirs(os.path.dirname(session_file), exist_ok=True)
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


def process_post_tool_use(payload):
    conv_id = payload.get("conversationId", "default")
    session_file = get_session_file(conv_id)
    state = load_session_state(session_file)

    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    args = tool_call.get("args", {})
    error = payload.get("error")

    # 1. Chequear si es herramienta de escritura
    if tool_name in (
        "write_to_file",
        "replace_file_content",
        "multi_replace_file_content",
    ):
        target_file = args.get("TargetFile", "")
        norm_path = target_file.replace("\\", "/")
        dirty_targets = [
            r"\bsrc/",
            r"\bapp/",
            r"\btests/",
            r"\binfra/",
            r"package\.json$",
        ]
        if any(re.search(pat, norm_path) for pat in dirty_targets):
            state["dirty"] = True
            state["typecheck_ok"] = False
            state["tests_ok"] = False
            state["continues"] = 0

    # 2. Chequear run_command exitoso
    elif tool_name == "run_command" and not error:
        cmd = args.get("CommandLine", "")

        # Verificacion de tipado
        if re.search(r"\btsc\s+--noEmit\b", cmd) or re.search(r"\btypecheck\b", cmd):
            state["typecheck_ok"] = True

        # Verificacion de tests
        test_patterns = [
            r"\bvitest\b",
            r"\bjest\b",
            r"\bplaywright\s+test\b",
            r"(npm|pnpm|yarn)\s+test\b",
        ]
        if any(re.search(pat, cmd) for pat in test_patterns):
            state["tests_ok"] = True

    save_session_state(session_file, state)


def main():
    try:
        raw_input = sys.stdin.read()
        if raw_input.strip():
            payload = json.loads(raw_input)
            process_post_tool_use(payload)
    except Exception:
        pass
    finally:
        sys.stdout.write("{}\n")


if __name__ == "__main__":
    main()
