# Instalación y Configuración del Paquete de Guardrails

Este documento describe el procedimiento manual para configurar el sistema de seguridad, hooks de ciclo de vida y servidores MCP en entornos de desarrollo con Antigravity CLI.

> [!WARNING]
> El comando `npx skills add <owner>/<repo>` instala **únicamente** las carpetas de skills (`.agents/skills/`). Por motivos de seguridad y principio de mínimo privilegio, los guardrails del sistema (`AGENTS.md`, hooks de ejecución, reglas y configuración de terminal) **no** se instalan automáticamente mediante `npx skills add`.

---

## 1. Configuración de Hooks de Ciclo de Vida

Los hooks supervisan la ejecución de herramientas, previenen comandos destructivos (`rm -rf`, `sudo`, `git push --force`) y bloquean la exposición de secretos.

1. Copia la plantilla neutral:
   ```bash
   cp docs/guardrails-templates/hooks.json.template .agents/hooks.json
   ```
2. Reemplaza los marcadores de posición con las rutas reales de tu máquina:
   - `<WORKSPACE_DIR>`: Ruta absoluta hacia la raíz del proyecto.
   - `<PYTHON_PATH>`: Ruta absoluta al intérprete de Python (ej. `/usr/bin/python3` o `/opt/homebrew/bin/python3`).

---

## 2. Servidor MCP de Pruebas (`op-sandbox`)

El servidor MCP `op-sandbox` permite a los agentes consultar direcciones de billetera y simular cotizaciones contra un entorno local de Rafiki o la red pública de pruebas (testnet).

1. Copia la plantilla neutral:
   ```bash
   cp docs/guardrails-templates/mcp_config.json.template .agents/mcp_config.json
   ```
2. Reemplaza los marcadores `<WORKSPACE_DIR>`, `<PYTHON_PATH>` y `<NPX_PATH>`.
3. El script está ubicado de forma autocontenida en:
   `.agents/skills/rafiki-local-playground/scripts/mcp-op-sandbox.py`

---

## 3. Evaluación de Empaquetado como Plugin de Antigravity

Según la documentación oficial de Antigravity ([https://antigravity.google/docs/plugins/](https://antigravity.google/docs/plugins/)):
> *"Plugins package reusable skills, background subagents, linting rules, Model Context Protocol (MCP) servers, and lifecycle hooks into a single deployable asset."*

Un plugin nativo de Antigravity permite estructurar en una sola carpeta:
```text
plugins/open-payments-guardrails/
├── plugin.json
├── hooks.json
├── mcp_config.json
├── rules/
│   └── AGENTS.md
└── skills/
```

### Consideraciones de Seguridad:
- **Ejecución de Código:** Los hooks de ciclo de vida (`PreToolUse`, `PostToolUse`, `Stop`) ejecutan comandos de shell locales en la máquina del usuario.
- **Transparencia:** Para proteger la confianza del usuario, ningún script modificará automáticamente `~/.gemini/antigravity-cli/settings.json` sin presentar previamente un diff detallado y requerir aprobación interactiva explícita.
