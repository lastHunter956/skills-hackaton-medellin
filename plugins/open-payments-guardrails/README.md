# Open Payments Guardrails Plugin para Antigravity CLI (AGY)

Plugin nativo para **Antigravity CLI (AGY)** que empaqueta habilidades, reglas de dominio, políticas de seguridad, hooks de ciclo de vida y servidores MCP para el desarrollo seguro de integraciones financieras basadas en **Open Payments**, **Interledger Protocol (ILP)** y **Rafiki**.

> **Aviso de Independencia:** Este proyecto es una iniciativa comunitaria independiente y no está afiliado oficialmente a Google, Anthropic, Interledger Foundation ni Rafiki. Interledger Protocol® e ILP® son marcas registradas de la Interledger Foundation.

---

## 1. Contenido del Plugin

Este plugin contiene una distribución autosuficiente estructurada bajo los estándares del sistema de personalización de Antigravity:

| Componente | Directorio / Archivo | Descripción |
| :--- | :--- | :--- |
| **Manifiesto** | `plugin.json` | Declaración de metadatos, autoría y versión del plugin. |
| **Skills (8)** | `skills/` | Catálogo completo de 8 skills operativas (transferencias, checkouts, verificación de firmas RFC 8785, servidor MCP local, arquitectura Next.js y conceptos ILP). |
| **Rules (4)** | `rules/` | Reglas de dominio financiero (`10-payments-domain.md`), seguridad de credenciales (`20-security.md`), tipado estricto (`30-nextjs-typescript.md`) e infraestructura segura (`40-docker-env.md`). |
| **Hooks** | `hooks.json` & `hooks/` | Hook activo `payments-guard.py` (`PreToolUse`) para la prevención de comandos destructivos y fugas de secretos. |
| **Plantillas Hooks** | `hooks/templates/` | Plantillas opcionales de hooks de sesión y Definition of Done (`done-gate.py.template`, `track-verification.py.template`, `session-start.py.template`). |
| **Servidores MCP** | `mcp_config.json` | Servidor MCP portable `op-sandbox` para resolución de wallet addresses y simulación de webhooks locales. |
| **Plantilla MCP** | `mcp_config.template.json` | Configuración de referencia para conectar servidores externos opcionales (`nextjs-docs`, `postgres-readonly`, `playwright`, `github-readonly`). |

---

## 2. Auditoría de Seguridad y Comandos de Hooks

> [!CAUTION]
> **Revisión de Seguridad Obligatoria:** Los hooks y servidores MCP son código ejecutable local. Revisa minuciosamente su contenido antes de habilitar el plugin en entornos de desarrollo o producción.

### Hook Activo: `payments-guard.py`
- **Evento:** `PreToolUse` (intercepta llamadas antes de ejecutarse: `run_command`, `write_to_file`, etc.).
- **Comandos que ejecuta:** **Ninguno**. El hook evalúa el payload de entrada en memoria a través de `stdin` y emite una decisión en `stdout` (`allow`, `deny`, o `ask`).
- **Comportamiento:**
  - **Bloquea (`deny`):** Comandos destructivos (`rm -rf`, `sudo`, contenedores con privilegios elevados, montajes del socket del daemon de Docker, lectura forzada de archivos `.env`, asignaciones de llaves privadas PEM en código fuente).
  - **Requiere Aprobación (`ask`):** Operaciones críticas de control de versiones (`git commit`, `git push`), instalación de paquetes (`pnpm add`) y mutaciones de esquema (`prisma migrate`).
  - **Fallo Seguro:** Si ocurre cualquier error interno en el hook, falla hacia `"decision": "ask"` para requerir confirmación humana.
  - **Aislamiento de Red:** No realiza ninguna conexión saliente ni transmite datos fuera de tu máquina.

---

## 3. Instalación y Gestión con AGY CLI

### A. Instalación Local
Para instalar el plugin directamente desde el directorio del repositorio clonado:
```bash
agy plugin install ./plugins/open-payments-guardrails
```

### B. Instalación Remota desde GitHub
Antigravity CLI soporta instalación directa desde repositorios:
```bash
agy plugin install https://github.com/lastHunter956/skills-hackaton-medellin
```
> [!NOTE]
> En la versión 1.3.6 de AGY CLI, `agy plugin install` espera encontrar `plugin.json` en la raíz del objetivo. Si se utiliza un repositorio monorepo con el plugin en un subdirectorio, se recomienda clonar e instalar localmente mediante subruta (`./plugins/open-payments-guardrails`), o utilizar un repositorio dedicado exclusivamente al plugin.

### C. Listar Plugins Instalados
```bash
agy plugin list
```

### D. Habilitar y Deshabilitar
Para activar o suspender el plugin completo:
```bash
# Habilitar plugin
agy plugin enable open-payments-guardrails

# Deshabilitar plugin (conserva la instalación sin cargar hooks ni skills)
agy plugin disable open-payments-guardrails
```

### E. Desactivar Servidores MCP o Hooks Individualmente
- **Desactivar Hooks:** En `plugins/open-payments-guardrails/hooks.json`, añade `"enabled": false` dentro del bloque de la regla o elimina la entrada del evento.
- **Desactivar MCP:** En `plugins/open-payments-guardrails/mcp_config.json`, elimina o comenta el bloque `"op-sandbox"`, o desactívalo desde la interfaz gráfica de AGY en **Additional Options (...) > MCP Servers**.

### F. Desinstalación
```bash
agy plugin uninstall open-payments-guardrails
```

---

## 4. Licencia

Distribuido bajo licencia [Apache 2.0](../../LICENSE). Copyright 2026 MD-Genius-Developers.
