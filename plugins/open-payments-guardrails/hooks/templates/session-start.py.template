#!/usr/bin/env python3
"""Hook SessionStart: session-start.py

Inyecta contexto al inicio de sesion (fase actual y hasta 15 lineas de STATE.md).
Contrato: JSON stdin -> JSON stdout con 'injectSteps'.
Maximo 16 lineas inyectadas en systemMessage.
"""

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_PHASE_FILE = os.path.join(REPO_ROOT, ".agents", "state", "phase")
CONTEXT_STATE_FILE = os.path.join(REPO_ROOT, "docs", "context", "STATE.md")


def get_current_phase():
    try:
        if os.path.exists(STATE_PHASE_FILE):
            with open(STATE_PHASE_FILE, "r", encoding="utf-8") as f:
                return f.read().strip() or "execute"
    except Exception:
        pass
    return "execute"


def get_context_state_lines():
    lines = []
    try:
        if os.path.exists(CONTEXT_STATE_FILE):
            with open(CONTEXT_STATE_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    lines.append(line.rstrip())
                    if len(lines) >= 15:
                        break
    except Exception:
        pass
    return lines


def build_session_start_message():
    phase = get_current_phase()
    state_lines = get_context_state_lines()

    msg_lines = [f"[Antigravity Guardrails] Fase activa: {phase}"]
    for line in state_lines:
        msg_lines.append(line)
        if len(msg_lines) >= 16:
            break

    system_text = "\n".join(msg_lines)
    return {
        "injectSteps": [
            {
                "systemMessage": {
                    "systemMessage": system_text
                }
            }
        ]
    }


def main():
    try:
        # Consumir stdin si existe
        _ = sys.stdin.read()
        res = build_session_start_message()
        sys.stdout.write(json.dumps(res) + "\n")
    except Exception:
        sys.stdout.write(json.dumps({"injectSteps": []}) + "\n")


if __name__ == "__main__":
    main()
