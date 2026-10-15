# Estado del Proyecto - Guardrails Antigravity

- **Fase Actual:** Guardrails auditados en sandbox y settings reforzados.
- **Entorno:** macOS ARM64 | Sandbox activo | Settings protegidos contra tampering.
- **Decisiones Vigentes:**
  - Permissions: Settings.json actualizado con Deny > Ask > Allow y rutas absolutas.
  - Sandbox: enableTerminalSandbox: true y toolPermission: proceed-in-sandbox.
  - Auditoría FASE 3: 7/8 vectores bloqueados (1 fallo identificado en pnpm add).
  - Context Linter: scripts/context-lint.py validado ("OK: dentro de presupuesto").
  - Invariantes: Server-only en Open Payments y bloqueo privileged validados.
- **Siguiente Paso:** Scaffolding de aplicación o ajuste fino según aprobación.
