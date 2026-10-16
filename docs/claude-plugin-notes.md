# Notas de Arquitectura y Portabilidad: Plugin de Claude Code

Este repositorio cuenta con un diseño de compatibilidad dual: opera simultáneamente como **plugin nativo para Claude Code** y como **paquete modular de skills** distribuible mediante `npx skills add` o utilizable en Antigravity CLI.

---

## 1. Componentes Portables (Incluidos en el Plugin)

Los siguientes componentes forman parte del plugin distribuible y funcionan de manera estándar en Claude Code:

| Componente | Ubicación | Descripción y Portabilidad |
| :--- | :--- | :--- |
| **Manifiesto de Plugin** | `.claude-plugin/plugin.json` | Metadatos estándar de Claude Code (nombre, versión, autor, licencia y declaración explícita del catálogo de skills). |
| **Skills Canónicas** | `skills/*/SKILL.md` | Las 8 skills operativas de pagos, cada una autosuficiente con su frontmatter YAML, referencias (`references/`) y scripts (`scripts/`). |
| **Configuración MCP** | `.mcp.json` | Declaración portable del servidor `op-sandbox` usando `${CLAUDE_PLUGIN_ROOT}` y la biblioteca estándar de Python sin rutas absolutas. |
| **Documentación Técnica** | `docs/` y `README.md` | Guías de integración, arquitectura, notas de licencias y manuales de instalación. |

---

## 2. Componentes Excluidos del Plugin (Específicos de Antigravity)

Determinados componentes residen en `.agents/` y son específicos del entorno de ejecución de Antigravity CLI (AGY). No se incluyen en `.claude-plugin/plugin.json` por las siguientes razones técnicas:

### A. Hooks de Ciclo de Vida (`.agents/hooks/` y `.agents/hooks.json`)
- **Archivos:** `payments-guard.py`, `track-verification.py`.
- **Razón de exclusión:** Estos hooks se integran en el pipeline de eventos de bajo nivel de Antigravity CLI (`PreToolUse`, `PostToolUse`, `Stop`) para bloquear comandos destructivos (`rm -rf`, `sudo`, `git push`) e inspeccionar variables de entorno. Claude Code no implementa este protocolo de hooks de ciclo de vida en plugins estándar.

### B. Reglas de Inyección Dinámica (`.agents/rules/` y `AGENTS.md`)
- **Archivos:** `10-payments-domain.md`, `20-security.md`, `30-nextjs-typescript.md`, `40-docker-env.md`.
- **Razón de exclusión:** Antigravity utiliza un mecanismo propio de presupuestos de tokens y reglas condicionales con disparadores (`trigger: always_on` o contextuales). Para que las directivas críticas de negocio apliquen en Claude Code, las invariantes clave se compilan directamente en `references/invariants.md` dentro de cada skill que las requiere (gestionadas por `scripts/sync-shared.py`).

### C. Configuración Local de MCP (`.agents/mcp_config.json`)
- **Razón de exclusión:** Contiene rutas absolutas locales del entorno del desarrollador (`/usr/local/bin/...`, paths absolutos locales). Para Claude Code se provee el archivo estándar `.mcp.json` en la raíz, que utiliza `${CLAUDE_PLUGIN_ROOT}` y garantiza portabilidad en cualquier máquina.

---

## 3. Coexistencia y Fuente Única de Verdad

Para evitar la duplicación de archivos Markdown (lo cual violaría los límites de duplicación y presupuesto de contexto de `context-lint.py`):
1. La raíz `skills/` contiene las carpetas reales de las 8 skills.
2. `.agents/skills` se configura como un symlink relativo hacia `../skills`.
3. Tanto `npx skills add` como Antigravity CLI y Claude Code reconocen `skills/` en la raíz de forma nativa.
