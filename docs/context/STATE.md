# Estado del Proyecto - Guardrails Antigravity

- **Fase Actual:** Compatibilidad dual completada: Plugin Claude Code y Skills Antigravity.
- **Entorno:** macOS ARM64 | Sandbox activo | Settings protegidos contra tampering.
- **Decisiones Vigentes:**
  - Skills activas (8/8) en `skills/` canónico con symlink relativo en `.agents/skills`.
  - Capa Claude Code: `.claude-plugin/plugin.json` y `.mcp.json` validados con `--strict`.
  - Verificación: `claude plugin validate`, `validate-skill.py` y `context-lint.py` verdes.
- **Siguiente Paso:** Presentación final de cambios y espera de aprobación para commit.
