#!/usr/bin/env python3
"""Hook Stop: done-gate.py

Gating del Definition of Done (DoD) antes de permitir que el agente concluya.
Contrato: JSON stdin -> JSON stdout con 'decision': 'continue' | 'allow' | 'ask'.
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


def evaluate_stop(payload):
    conv_id = payload.get("conversationId", "default")
    session_file = get_session_file(conv_id)
    state = load_session_state(session_file)

    term_reason = payload.get("terminationReason", "")
    fully_idle = payload.get("fullyIdle", False)

    # Solo intervenimos si el modelo intento detenerse voluntariamente y no hay tareas en background
    is_normal_stop = term_reason in ("model_stop", "NO_TOOL_CALL")

    if is_normal_stop and fully_idle and state.get("dirty", False):
        missing = []
        if not state.get("typecheck_ok", False):
            missing.append("verificación de tipos ('tsc --noEmit')")
        if not state.get("tests_ok", False):
            missing.append("suite de pruebas ('npm test' o 'playwright test')")

        if missing:
            continues = state.get("continues", 0)
            if continues < 2:
                state["continues"] = continues + 1
                save_session_state(session_file, state)
                missing_str = " y ".join(missing)
                return {
                    "decision": "continue",
                    "reason": (
                        f"Definition of Done incompleto tras cambios en código: falta {missing_str}. "
                        "Por favor ejecuta los comandos de verificación antes de finalizar."
                    ),
                }

    return {"decision": "allow"}


def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            sys.stdout.write(json.dumps({"decision": "allow"}) + "\n")
            return

        payload = json.loads(raw_input)
        result = evaluate_stop(payload)
        sys.stdout.write(json.dumps(result) + "\n")
    except Exception as e:
        sys.stdout.write(
            json.dumps(
                {
                    "decision": "ask",
                    "reason": f"Fallo de excepcion en done-gate.py ({e}). Requerida confirmacion de finalizacion.",
                }
            )
            + "\n"
        )


if __name__ == "__main__":
    main()
