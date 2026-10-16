#!/usr/bin/env python3
"""Hook PreToolUse: payments-guard.py

Aplica las politicas de seguridad e invariantes para Antigravity CLI.
Contrato: JSON stdin -> JSON stdout con 'decision': 'allow' | 'deny' | 'ask'.
En caso de excepcion, falla de forma segura hacia 'ask'.
"""

import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_PHASE_FILE = os.path.join(REPO_ROOT, ".agents", "state", "phase")


def get_current_phase():
    try:
        if os.path.exists(STATE_PHASE_FILE):
            with open(STATE_PHASE_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content in ("bootstrap", "audit", "execute"):
                    return content
    except Exception:
        pass
    return "execute"


def extract_target_paths(tool_name, args):
    paths = []
    for key in (
        "TargetFile",
        "AbsolutePath",
        "SearchPath",
        "DirectoryPath",
        "SearchDirectory",
    ):
        val = args.get(key)
        if val and isinstance(val, str):
            paths.append(val)
    return paths


def extract_written_content(tool_name, args):
    contents = []
    if "CodeContent" in args and isinstance(args["CodeContent"], str):
        contents.append(args["CodeContent"])
    if "ReplacementContent" in args and isinstance(args["ReplacementContent"], str):
        contents.append(args["ReplacementContent"])
    if "ReplacementChunks" in args and isinstance(args["ReplacementChunks"], list):
        for chunk in args["ReplacementChunks"]:
            if isinstance(chunk, dict) and "ReplacementContent" in chunk:
                contents.append(chunk["ReplacementContent"])
    return "\n".join(contents)


def evaluate_pre_tool_use(payload):
    phase = get_current_phase()
    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    args = tool_call.get("args", {})

    target_paths = extract_target_paths(tool_name, args)
    written_content = extract_written_content(tool_name, args)
    is_write_tool = tool_name in (
        "write_to_file",
        "replace_file_content",
        "multi_replace_file_content",
    )

    # 1. Regla Deny Global: Archivos sensibles por ruta
    for path in target_paths:
        base = os.path.basename(path)
        norm_path = path.replace("\\", "/")

        if (
            base.startswith(".env")
            and base != ".env.example"
            and not base.endswith(".example")
        ):
            return {
                "decision": "deny",
                "reason": f"Acceso denegado a archivo de entorno sensible: {base}",
            }

        if (
            base.startswith("id_rsa")
            or base.endswith(".pem")
            or base.endswith(".p12")
        ):
            return {
                "decision": "deny",
                "reason": f"Acceso denegado a clave privada o certificado: {base}",
            }

        if "/.ssh/" in norm_path or "/.aws/" in norm_path:
            return {
                "decision": "deny",
                "reason": "Acceso denegado a directorio de credenciales (.ssh o .aws).",
            }

    # 2. Reglas para run_command
    if tool_name == "run_command":
        cmd = args.get("CommandLine", "").strip()

        # Deny comandos destructivos / peligrosos
        deny_patterns = [
            (r"\brm\s+-[a-zA-Z]*rf\b", "Uso de 'rm -rf' prohibido."),
            (r"\bsudo\b", "Uso de 'sudo' prohibido."),
            (
                r"(curl|wget)\b.*\|\s*(ba)?sh",
                "Descargas directas hacia shell prohibidas.",
            ),
            (
                r"git\s+push\s+.*(--force|-f\b)",
                "Forzar push (force-push) en git prohibido.",
            ),
            (r"git\s+reset\s+--hard\b", "Reescritura 'git reset --hard' prohibida."),
            (r"git\s+clean\s+.*-f", "Eliminacion forzada 'git clean -f' prohibida."),
            (r"\bdocker\s+run\b", "Uso directo de 'docker run' prohibido."),
            (
                r"docker\b.*--privileged",
                "Ejecucion de contenedores privileged prohibida.",
            ),
            (
                r"docker\b.*docker\.sock",
                "Montaje de socket de docker (/var/run/docker.sock) prohibido.",
            ),
            (
                r"(--net=host|--network=host)\b",
                "Uso de network_mode host prohibido.",
            ),
            (
                r"\bprintenv\b",
                "Impresion masiva de variables de entorno (printenv) prohibida.",
            ),
            (
                r"(cat|less|head|tail|source)\s+.*\.env(?!\.example\b)",
                "Lectura de archivo .env sensible por shell prohibida.",
            ),
            (
                r"docker\s+compose\s+down\s+.*(-v|--volumes)\b",
                "Destruccion de volumenes en docker compose prohibida.",
            ),
            (
                r"docker\s+system\s+prune\b",
                "Uso de 'docker system prune' prohibido.",
            ),
            (r"docker\s+volume\s+rm\b", "Uso de 'docker volume rm' prohibido."),
            (
                r"(npm|pnpm|yarn)\s+publish\b",
                "Publicacion automatica de paquetes prohibida.",
            ),
        ]

        for pattern, reason in deny_patterns:
            if re.search(pattern, cmd, re.IGNORECASE):
                return {"decision": "deny", "reason": f"Comando denegado: {reason}"}

        # Ask comandos sensibles
        ask_patterns = [
            (
                r"git\s+(commit|push)\b",
                "Operacion de Git (commit/push) requiere aprobacion interactiva.",
            ),
            (
                r"(npm|pnpm|yarn)\s+(add|install)\b",
                "Instalacion de dependencias requiere aprobacion interactiva.",
            ),
            (
                r"docker\s+compose\b.*?\b(up|build)\b",
                "Levantamiento/compilacion de Docker Compose requiere aprobacion interactiva.",
            ),
            (
                r"(prisma\s+migrate|db\s+push|drizzle-kit\s+push)\b",
                "Migracion de base de datos requiere aprobacion interactiva.",
            ),
        ]

        for pattern, reason in ask_patterns:
            if re.search(pattern, cmd, re.IGNORECASE):
                return {"decision": "ask", "reason": reason}

        # Restricciones en Fase AUDIT para run_command
        if phase == "audit":
            audit_blocked = [
                r"\b(rm|mv|cp|touch|mkdir|tee)\b",
                r"\bsed\s+-i\b",
                r"git\s+(add|commit|checkout)\b",
                r"\b(npm|pnpm|yarn)\s+(add|install|remove)\b",
                r"docker\s+compose\b.*?\b(up|down|build)\b",
                r"[^2]>>?",  # Redirecciones de salida excepto 2>&1
            ]
            for pattern in audit_blocked:
                if re.search(pattern, cmd, re.IGNORECASE):
                    return {
                        "decision": "deny",
                        "reason": f"Fase de auditoria activa: Comandos con efectos secundarios denegados ({cmd}). Solo se permiten inspecciones de solo lectura.",
                    }

    # 3. Restricciones de Escritura en Rutas Protegidas
    if is_write_tool:
        protected_patterns = [
            r"/\.git/",
            r"/\.agents/hooks/",
            r"/\.agents/hooks\.json",
            r"/\.agents/state/",
            r"/\.agents/mcp_config\.json",
            r"settings\.json$",
        ]

        for path in target_paths:
            norm_path = path.replace("\\", "/")
            is_protected = any(re.search(pat, norm_path) for pat in protected_patterns)

            if is_protected and phase != "bootstrap":
                return {
                    "decision": "deny",
                    "reason": f"Escritura en ruta protegida de agente denegada fuera de fase bootstrap: {path}",
                }

            # Restriccion en Fase AUDIT para escrituras
            if phase == "audit":
                if not ("docs/proposals/" in norm_path):
                    return {
                        "decision": "deny",
                        "reason": f"Fase de auditoria activa: Solo se permite escribir dentro de docs/proposals/. Intento en: {path}",
                    }

    # 4. Inspeccion de Contenido Escrito (Deteccion de Secretos y Reglas de Dominio)
    if is_write_tool and written_content:
        # Claves privadas PEM
        if re.search(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", written_content):
            return {
                "decision": "deny",
                "reason": "Escritura denegada: Se detecto una clave privada en formato PEM.",
            }

        # Tokens AWS / GitHub
        if re.search(r"\bAKIA[0-9A-Z]{16}\b", written_content):
            return {
                "decision": "deny",
                "reason": "Escritura denegada: Se detecto una Access Key ID de AWS.",
            }

        if re.search(r"\bghp_[0-9a-zA-Z]{36}\b", written_content):
            return {
                "decision": "deny",
                "reason": "Escritura denegada: Se detecto un token Personal Access Token de GitHub.",
            }

        # Variables NEXT_PUBLIC_ con terminos sensibles
        if re.search(r"NEXT_PUBLIC_[A-Z0-9_]*(KEY|SECRET|TOKEN|PRIVATE)", written_content):
            return {
                "decision": "deny",
                "reason": "Escritura denegada: NEXT_PUBLIC_ no puede exponer KEY, SECRET, TOKEN o PRIVATE al navegador.",
            }

        # ignoreBuildErrors: true
        if re.search(r"ignoreBuildErrors\s*:\s*true", written_content):
            return {
                "decision": "deny",
                "reason": "Escritura denegada: 'ignoreBuildErrors: true' esta estrictamente prohibido.",
            }

        # 'use client' con @interledger/open-payments
        if '"use client"' in written_content and "@interledger/open-payments" in written_content:
            return {
                "decision": "deny",
                "reason": "Escritura denegada: '@interledger/open-payments' no puede importarse en componentes 'use client'. Debe ser server-only.",
            }

        # compose o Dockerfile con privileged, docker.sock o network_mode host
        if re.search(r"\bprivileged\s*:\s*true\b", written_content) or "docker.sock" in written_content:
            return {
                "decision": "deny",
                "reason": "Escritura denegada: Especificacion de contenedor privileged o docker.sock detectada.",
            }

        if re.search(r"network_mode\s*:\s*['\"]?host['\"]?", written_content):
            return {
                "decision": "deny",
                "reason": "Escritura denegada: 'network_mode: host' detectado.",
            }

        # Asignaciones tipo api_key="..." de >= 24 caracteres
        api_key_match = re.search(r"(?:api[_-]?key|secret[_-]?key)\s*[:=]\s*['\"][A-Za-z0-9_\-]{24,}['\"]", written_content, re.IGNORECASE)
        if api_key_match:
            is_docs_or_example = False
            for path in target_paths:
                norm_p = path.replace("\\", "/")
                if (
                    "docs/" in norm_p
                    or ".agents/skills/" in norm_p
                    or ".agents/rules/" in norm_p
                    or norm_p.endswith(".env.example")
                ):
                    is_docs_or_example = True
                    break

            if is_docs_or_example:
                return {
                    "decision": "ask",
                    "reason": "Asignacion de API key simulada en documentacion/ejemplo detectada. Confirma si es segura.",
                }
            else:
                return {
                    "decision": "deny",
                    "reason": "Escritura denegada: Se detecto una asignacion hardcodeada de API key (>=24 caracteres).",
                }

    return {"decision": "allow"}


def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            sys.stdout.write(json.dumps({"decision": "allow"}) + "\n")
            return

        payload = json.loads(raw_input)
        result = evaluate_pre_tool_use(payload)
        sys.stdout.write(json.dumps(result) + "\n")
    except Exception as e:
        # Falla hacia "ask" por seguridad
        sys.stdout.write(
            json.dumps(
                {
                    "decision": "ask",
                    "reason": f"Fallo de excepcion en payments-guard.py ({e}). Requerida confirmacion humana de seguridad.",
                }
            )
            + "\n"
        )


if __name__ == "__main__":
    main()
