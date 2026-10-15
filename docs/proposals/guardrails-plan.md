# Plan de Guardrails para Antigravity CLI (`agy`)

## 1. Detección del Entorno Actual (Solo Lectura)

A través de la inspección no invasiva del sistema y del espacio de trabajo, se detectaron las siguientes condiciones:

| Parámetro | Valor Detectado | Implicación Técnica |
| :--- | :--- | :--- |
| **Sistema Operativo** | macOS Darwin 25.6.0 (ARM64 / Apple Silicon) | El sandbox de terminal se ejecuta mediante Seatbelt profiles (`sandbox-exec` / SBPL). |
| **Intérprete Python** | `/opt/homebrew/bin/python3` (Python 3.14.7) | El binario `python` **no existe**; los scripts y comandos en hooks deben invocar explícitamente `python3`. |
| **Ruta del Workspace** | `/Volumes/ADATA SD620/Programacion 7.0/hackaton-medellin` | Ubicado en un volumen de almacenamiento externo montado en `/Volumes/`. |
| **Control de Versiones (`git`)** | **No es un repositorio Git** (`fatal: not a git repository`) | No hay directorio `.git` ni rama activa. Cualquier guardrail que dependa de `git status`, `git diff` o githooks fallará si no se maneja condicionalmente. |
| **Confianza del Workspace** | **CONFIABLE** (`trustedWorkspaces`) | La ruta exacta está registrada en la lista `trustedWorkspaces` de `~/.gemini/antigravity-cli/settings.json`. Los hooks locales en `.agents/hooks.json` **sí se ejecutarán** (no serán ignorados). |
| **Archivos de Agente en Workspace** | `AGENTS.md`: **No existe**<br>`.agents/`: **No existe** | El workspace se encuentra en un estado totalmente limpio y sin artefactos previos. |
| **Clave `permissions` en `settings.json`** | Contiene únicamente:<br>`"allow": ["command(./.venv/bin/python scratch/build_sprite_sheets.py)"]` | No hay listas de `deny` ni `ask` configuradas globalmente. No hay restricciones personalizadas activas en este momento. |

---

## 2. Especificación Técnica de Guardrails en Antigravity

Basado en la documentación oficial de Antigravity:

### A. Lifecycle Hooks (`hooks.json`)
* **Ubicación:** `.agents/hooks.json` (workspace) o en plugins.
* **Mapeo y Ejecución:**
  * Soporta únicamente `"type": "command"`.
  * Comandos ejecutados mediante `sh -c` (macOS/Linux) o `cmd /c` (Windows) en el directorio donde reside `hooks.json`.
  * Timeout configurable por handler (`timeout`, por defecto 30 segundos).
  * Son **síncronos y bloqueantes**.
* **Herramientas Objetadas (`matcher`):**
  * Se evalúan en eventos `PreToolUse` y `PostToolUse`.
  * Coincidencia vía regex sobre el nombre de herramienta normalizado (e.g., `run_command`, `write_to_file`, `replace_file_content`, `read_url_content`, `call_mcp_tool`, `manage_task`, `browser_.*`).
  * Patrones: `*` (todas), `run_command` (exacta), `run_command|write_to_file` (alternancia).
* **Contrato JSON I/O (protojson en `camelCase`):**
  * **Metadatos comunes en `stdin`:** `conversationId`, `workspacePaths`, `transcriptPath`, `artifactDirectoryPath`, `modelName`.
  * **`SessionStart`:** Entrada: metadatos comunes. Salida: `{"injectSteps": [{"systemMessage": {"systemMessage": "..."}}, {"userMessage": "..."}, {"ephemeralMessage": "..."}]}`.
  * **`PreToolUse`:**
    * Entrada: metadatos + `toolCall: {"name": string, "args": object}`, `stepIdx: int`.
    * Salida:
      * `decision`: `"allow"` | `"deny"` | `"ask"` | `"force_ask"`.
      * `reason`: (string opcional).
      * `permissionOverrides`: (array de strings opcional, e.g., `["command(npm test)"]`).
      * `overwrite`: (objeto opcional; reemplazo superficial (*shallow merge*) de argumentos de la herramienta antes de su ejecución).
  * **`PostToolUse`:**
    * Entrada: metadatos + `toolCall`, `stepIdx`, `error` (si falló).
    * Salida: Objeto JSON vacío `{}`.
  * **`PreInvocation`:**
    * Entrada: metadatos + `invocationNum: int`, `initialNumSteps: int`.
    * Salida: `{"injectSteps": [...]}` (`systemMessage`, `userMessage`, o `ephemeralMessage`).
  * **`PostInvocation`:**
    * Entrada: idéntico a `PreInvocation`.
    * Salida: `{"injectSteps": [...], "terminationBehavior": "force_continue" | "terminate" | ""}`.
  * **`Stop`:**
    * Entrada: metadatos + `executionNum: int`, `terminationReason: string` (e.g. `NO_TOOL_CALL`, `MAX_INVOCATIONS`, `ERROR`, `USER_CANCELED`), `error: string`, `fullyIdle: bool`.
    * Salida: `{"decision": "continue", "reason": "..."}` para forzar reingreso al loop, o cualquier otro valor para permitir la detención.

### B. Sistema de Permisos de Antigravity CLI
* **Configuración:** `~/.gemini/antigravity-cli/settings.json` bajo la clave `"permissions"`.
* **Listas de Acceso:** `"deny"`, `"ask"`, `"allow"`.
* **Precedencia Estricta:** `Deny > Ask > Allow`.
* **Sintaxis de Recursos:** `action(target)`
  * `read_file(/path)` / `read_file(*)`
  * `write_file(/path)` / `write_file(*)` (*write implica read; deny read niega write*).
  * `read_url(domain)` / `read_url(*)` (coincidencia de hostnames/subdominios).
  * `execute_url(domain)` / `execute_url(*)`
  * `command(prefix)` / `command(regex:pattern)` / `command(*)`
  * `unsandboxed(prefix)` / `unsandboxed(regex:pattern)` / `unsandboxed(*)`
  * `mcp(server/tool)` / `mcp(server/*)` / `mcp(*)`
* **Comportamiento por Defecto:**
  * Archivos del workspace: Auto-permitidos para lectura y escritura.
  * Web (`read_url`, `execute_url`): Por defecto `Ask`.
  * Comandos (`command`), `mcp` y rutas fuera del workspace: Por defecto `Ask`.

### C. Sandbox de Terminal
* **Motor en macOS:** Perfiles Seatbelt (`sandbox-exec` / SBPL).
* **Activación en CLI:** `"enableTerminalSandbox": true` y `"toolPermission": "proceed-in-sandbox"`.
* **Límites:** El sandbox aísla el sistema operativo, bloquea archivos sensibles (`~/.ssh`, `.env`), restringe sockets/red a dominios permitidos bajo `read_url`, y confina escrituras al workspace y directorios temporales.
* **Escape:** Comandos que coincidan con reglas `unsandboxed(...)` se ejecutan fuera del contenedor previa autorización o según regla `allow`.

### D. Reglas de Workspace (`AGENTS.md` / `.agents/rules/`)
* **Ubicaciones:** `AGENTS.md` (siempre activo para su directorio) o `.agents/rules/*.md`.
* **Triggers soportados en Frontmatter YAML:**
  * `model_decision` (requiere `description`)
  * `always_on`
  * `glob` (requiere `globs` o `glob`)
  * `manual` (solo mediante mención explícita con `@`)
* **Límites de Tamaño y Token Budget:**
  * **Límite por archivo:** 24 KB (24,000 bytes). Se trunca en límites de línea si se excede.
  * **Presupuesto agregado:** 20,000 tokens para reglas `always_on` y globales. Si se supera, se degradan automáticamente a punteros (`- <path>: <description>`).

---

## 3. Conflictos Potenciales con Nuevos Componentes

1. **Inexistencia de Repositorio Git:**
   * Cualquier hook o verificación de calidad orientada a inspeccionar `git diff`, ramas o archivos staged fallará de inmediato. Se debe definir si el workspace será versionado con git antes de implementar scripts dependientes de VCS.
2. **Invocación de Intérprete Python:**
   * En este sistema el ejecutable `python` no existe. Si un hook o regla especifica `python scripts/guard.py`, la ejecución fallará con un error del sistema operativo. La sintaxis debe ser estrictamente `python3`.
3. **Almacenamiento en Volumen Externo (`/Volumes/ADATA SD620/...`):**
   * Algunos sistemas de archivos externos no soportan flags de ejecución POSIX (`chmod +x`). Los scripts en hooks deben invocarse llamando explícitamente al intérprete (`sh ./script.sh` o `python3 ./script.py`) y no como ejecutables directos (`./script.sh`).
4. **Precedencia de Permisos (`Deny` estricto):**
   * Si se añaden patrones `deny` agresivos (por ejemplo `command(rm *)`), estos anulan cualquier regla `allow` y no podrán ser puenteados interactivamente sin modificar la configuración.

---

## 4. Riesgos Identificados

1. **Bloqueo del Agente por Malformación de JSON (Deadlock):**
   * Debido a que los hooks se comunican por `stdin`/`stdout` y son bloqueantes, si un script imprime logs informativos o trazas de error en `stdout` en lugar de emitir exclusivamente JSON válido, Antigravity no podrá interpretar la respuesta y la acción fallará.
2. **Degradación de Rendimiento por Timeout:**
   * Cada hook bloquea el ciclo del agente. Scripts lentos o con llamadas de red externas aumentarán la latencia de cada llamada a herramienta. Deben configurarse tiempos de timeout estrictos (≤ 5s para validaciones locales).
3. **Comportamiento del Sandbox sobre Volúmenes Externos:**
   * Si se habilita `enableTerminalSandbox`, el perfil SBPL de macOS debe reconocer la ruta `/Volumes/ADATA SD620/...` como ruta de trabajo permitida para lectura/escritura; de lo contrario, cualquier comando de compilación o test podría ser denegado por el kernel de macOS.

---

## 5. Orden de Trabajo Propuesto

El despliegue debe realizarse en fases incrementales, verificables y reversibles:

```
[Fase 1: Preparación del Entorno]
   ├── Definir si se inicializa Git (git init)
   └── Crear estructura base: .agents/rules/, .agents/hooks/, .agents/scripts/
           ↓
[Fase 2: Reglas Declarativas (Bajo Riesgo)]
   ├── Crear AGENTS.md con directivas de codificación y seguridad (always_on)
   └── Añadir reglas modulares en .agents/rules/ con triggers específicos (glob, model_decision)
           ↓
[Fase 3: Configuración de Permisos Base]
   └── Proponer adiciones a settings.json ("permissions") con listas de Deny (destructivos) y Ask
           ↓
[Fase 4: Desarrollo de Scripts de Hooks]
   ├── Implementar script Python 3 para validación de entrada/salida JSON estricta
   └── Escribir tests unitarios locales para verificar decisiones ("allow", "deny", "ask", "force_ask")
           ↓
[Fase 5: Activación de .agents/hooks.json]
   ├── Activar hook PreToolUse para run_command
   └── Validar que el agente responda correctamente ante bloqueos e interacciones
```

---

## 6. Lista de Dudas que Requieren Decisión del Usuario

1. **¿Deseas inicializar un repositorio Git en este directorio (`git init`)?**
   * *Impacto:* Permite crear guardrails que inspeccionen `git diff`, cambios pendientes y prevengan commits accidentales.
2. **¿Qué política de seguridad deseas aplicar para comandos potencialmente destructivos (`rm -rf`, `sudo`, `curl | bash`, modificación de `.env` o credenciales)?**
   * *Opción A (Bloqueo Duro):* Incluir en la lista `deny` de `settings.json` o que el hook responda `"deny"` directamente.
   * *Opción B (Confirmación Obligatoria):* Incluir en la lista `ask` o responder `"force_ask"` desde el hook para que siempre te pregunte antes de ejecutar.
3. **¿Deseas habilitar el Sandbox de Terminal (`enableTerminalSandbox`) en macOS para este proyecto?**
   * *Impacto:* Añade aislamiento a nivel de kernel mediante perfiles Seatbelt (`sandbox-exec`), pero requiere probar la compatibilidad de escritura sobre el disco externo `/Volumes/`.
4. **¿Cuáles son los eventos de hook prioritarios para tu flujo?**
   * ¿`PreToolUse` (gating de comandos de terminal antes de ejecutarse)?
   * ¿`PostToolUse` (análisis y linters post-ejecución)?
   * ¿`PreInvocation` / `SessionStart` (inyección de directivas de seguridad al modelo)?

---

## 7. Decisiones Aprobadas por el Usuario

1. **Control de Versiones (Git):**
   * **Aprobado.** Acciones autorizadas:
     * Creación de `.gitignore` con exclusiones de entornos, secretos, dependencias, artefactos de SO y estado de agentes.
     * Ejecución de `git init`.
     * Ejecución de `git status --short` y auditoría de archivos grandes (>5 MB) y secretos.
     * **Restricción estricta:** NO ejecutar `git add` ni commits sin autorización explícita.
2. **Política de Seguridad:**
   * **Deny Duro (bloqueo inmediato sin consulta):** `rm -rf`, `sudo`, `curl | sh` (o pipes a shell), acceso a `.env*` y claves privadas (`*.pem`, `*.key`), `git push --force` (force-push), sockets de Docker (`docker.sock`) y flags `--privileged`.
   * **Ask (confirmación interactiva):** `git commit`, `git push`, instalación de dependencias de paquetes, `docker compose up` / `docker compose build`, y ejecución de migraciones de base de datos.
   * **Diferencia Técnica Oficial (`ask` vs `force_ask`):**
     * `"ask"`: Solicita aprobación interactiva al usuario pero respeta la caché de permisos de la sesión ("Always Allow"), permitiendo auto-aprobar ejecuciones subsecuentes si el usuario ya las autorizó previamente.
     * `"force_ask"`: Fuerza la aparición del diálogo interactivo de confirmación en el 100% de los casos, ignorando y puenteando cualquier regla previa en caché de "Always Allow".
3. **Sandbox de Terminal:**
   * **Aprobado:** Configuración objetivo `"enableTerminalSandbox": true` y `"toolPermission": "proceed-in-sandbox"`.
   * **Prerrequisito de Seguridad:** Antes de aplicarlo, se debe diseñar una prueba con un archivo temporal para verificar que `sandbox-exec` en macOS permite escrituras sobre el workspace en la unidad externa montada en `/Volumes/...`. Si la prueba falla, se debe reportar inmediatamente sin intentar arreglos automáticos.
4. **Orden de Implementación de Hooks:**
   * Prioridad 1: `PreToolUse` (guardrail preventivo y filtrado de herramientas).
   * Prioridad 2: `PostToolUse` + `Stop` (verificación post-ejecución y validación de parada).
   * Prioridad 3: `SessionStart` (inyección mínima de contexto al iniciar sesión).
   * **Prohibición explícita:** NO utilizar `PreInvocation`.
5. **Restricciones de Entorno Obligatorias:**
   * Binario Python: Siempre invocar `/opt/homebrew/bin/python3` con ruta absoluta.
   * Manejo de rutas con espacios: En `hooks.json`, cada comando debe declarar rutas absolutas con comillas escapadas tanto para el intérprete como para el script, e.g.:
     `"\"/opt/homebrew/bin/python3\" \"/Volumes/ADATA SD620/Programacion 7.0/hackaton-medellin/.agents/hooks/<nombre>.py\""`
     Verificar con un hook de prueba para evitar errores `exit 127`.
   * Permisos de ejecución: No asumir flags `+x`; invocar siempre pasando el script como argumento al binario.
   * Configuración de usuario: Preservar intacta la regla `allow` existente de `./.venv/bin/python` y el listado de `trustedWorkspaces` en `~/.gemini/antigravity-cli/settings.json`.
