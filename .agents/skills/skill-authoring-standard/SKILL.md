---
name: skill-authoring-standard
description: "Procedimiento estándar para crear, documentar y validar skills en este proyecto. Usar al crear nuevas skills operativas. NO usar para directivas globales de código (usar rules) ni para tareas sin flujo procedimental paso a paso."
---

# Estándar de Creación de Skills en Antigravity CLI

Esta skill define el procedimiento uniforme para diseñar, documentar y verificar cualquier skill de este repositorio.

## Principios Rectores

1. **Progressive Disclosure:** El archivo principal `SKILL.md` debe mantenerse por debajo de las 200 líneas. Los manuales exhaustivos, especificaciones de payloads o esquemas deben delegarse en la carpeta `references/`.
2. **Invariantes Financieras:** Nunca dupliques invariantes de pagos dentro de una skill. Enlaza siempre a la fuente única: [.agents/rules/10-payments-domain.md](../../rules/10-payments-domain.md).
3. **Scripts Seguros:** Cualquier comando auxiliar en `scripts/` debe aceptar el flag `--help`, retornar código de salida 0 y justificar su consumo de tokens.
4. **Cero Carpetas Vacías:** Solo crea `scripts/`, `examples/` o `resources/` si contienen archivos necesarios.

---

## Procedimiento de Creación Paso a Paso

### 1. Definición y Delimitación
- Elige un identificador en minúsculas y con guiones (ej. `open-payments-transfers`).
- Redacta una descripción en tercera persona de máximo 400 caracteres que exponga explícitamente cuándo usar y cuándo NO usar la skill.

### 2. Estructuración del Directorio
Crea la jerarquía bajo `.agents/skills/<nombre>/`:
```text
.agents/skills/<nombre>/
├── SKILL.md
└── references/
    └── <guia-detallada>.md
```

### 3. Redacción del Contenido
- Aplica la plantilla oficial de [references/skill-template.md](./references/skill-template.md).
- Sigue las reglas de redacción técnica de [references/prompting-rules.md](./references/prompting-rules.md).
- Audita todos los criterios de [references/quality-checklist.md](./references/quality-checklist.md).

### 4. Verificación y Presupuesto
Tras escribir la skill, ejecuta obligatoriamente:
1. `python3 scripts/validate-skill.py .agents/skills/<nombre>`
2. `python3 scripts/context-lint.py .`
