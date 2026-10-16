---
trigger: always_on
description: "Directivas permanentes de seguridad, manejo de secretos, permisos y sanitización."
---

# Reglas Permanentes de Seguridad

1. **Gestión de Secretos:**
   - Nunca escribas credenciales, certificados ni API keys en el código fuente.
   - Todo secreto se inyecta por variables de entorno y se excluye vía `.gitignore`.

2. **Permisos y Comandos:**
   - No ejecutes utilidades con privilegios elevados (`sudo`, binarios `suid`).
   - Evita comandos que modifiquen masivamente el árbol de archivos sin confirmación.

3. **Validación de Entradas:**
   - Valida y sanea toda entrada externa en la frontera HTTP usando esquemas estrictos (`zod`).
   - Rechaza payloads maliciosos, inyecciones SQL y serializaciones no confiables.

4. **Principio de Mínimo Privilegio:**
   - Las operaciones de base de datos deben utilizar roles con permisos delimitados.
   - El agente debe solicitar autorización interactiva antes de cualquier operación de mutación crítica.
