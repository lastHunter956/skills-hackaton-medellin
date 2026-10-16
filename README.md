# Open Payments & Rafiki Agentic Skills Toolkit

Conjunto modular de habilidades agénticas (Agent Skills) y herramientas de desarrollo para la integración, prueba y despliegue de soluciones financieras basadas en el estándar **Open Payments** y el conector **Rafiki**.

> Proyecto independiente, no afiliado ni respaldado por Interledger Foundation. Interledger Protocol® e ILP® son marcas registradas de la Interledger Foundation.

---

## 1. Instalación y Uso según Ecosistema

Este repositorio ofrece compatibilidad dual como plugin para **Claude Code** y como paquete de habilidades para agentes vía **`npx skills add`** / **Antigravity CLI**.

### A. Claude Code (Plugin Nativo)

El repositorio incluye el manifiesto `.claude-plugin/plugin.json` y el archivo de herramientas `.mcp.json`.

**Instalación:**
```bash
# Instalación remota desde repositorio
claude plugin install <owner>/<repo>

# O inicialización en desarrollo local apuntando al directorio
claude plugin install .
```

**Validación del Plugin:**
```bash
# Validación estándar del manifiesto y catálogo de skills
claude plugin validate .

# Modo estricto para pipelines de CI/CD
claude plugin validate --strict .
```

> [!NOTE]
> Para detalles sobre componentes portables y exclusión de hooks propietarios de Antigravity, consulta [docs/claude-plugin-notes.md](./docs/claude-plugin-notes.md).

---

### B. Antigravity CLI / Gestor `skills-cli`

Puedes instalar el paquete completo o importar únicamente las habilidades que requiere tu aplicación.

**Instalación Completa:**
```bash
npx skills add <owner>/<repo>
```

**Instalación Modular (Skills Específicas):**
```bash
# Ejemplo: Solo transferencias y verificación de firmas
npx skills add <owner>/<repo> --skill open-payments-transfers --skill webhook-signature-verification

# Ejemplo: Solo arquitectura Next.js y cobros
npx skills add <owner>/<repo> --skill nextjs-typescript-application-architect --skill incoming-payments-checkout
```

**Nota para Usuarios de Windows:**
En entornos donde los enlaces simbólicos requieran permisos elevados, añade `--copy`:
```bash
npx skills add <owner>/<repo> --copy
```

**Fijar Versión Específica (Version Pinning):**
Para anclar la instalación a un release específico, utiliza el sufijo `#tag`:
```bash
npx skills add <owner>/<repo>#v1.0.0
```

**Validación de Skills y Presupuesto de Contexto:**
```bash
# Valida formato, metadatos y scripts de cada skill
python3 scripts/validate-skill.py skills

# Audita límites de contexto, triggers y duplicados
python3 scripts/context-lint.py .
```

---

## 2. Advertencia de Seguridad

> [!CAUTION]
> **Permisos de Ejecución:** Las habilidades instaladas pueden contener scripts auxiliares y servidores MCP (`skills/rafiki-local-playground/scripts/mcp-op-sandbox.py`) que se ejecutan localmente con los permisos del agente de codificación. Revisa el código fuente antes de su activación en entornos de producción.
>
> Los guardrails de seguridad y hooks de ciclo de vida del sistema no se instalan vía `npx skills add`. Consulta [docs/INSTALL-GUARDRAILS.md](./docs/INSTALL-GUARDRAILS.md) para configurarlos de forma controlada.

---

## 3. Catálogo de Skills Disponibles

| Skill | Descripción y Alcance |
| :--- | :--- |
| `incoming-payments-checkout` | Procedimiento para crear Incoming Payments en Open Payments, gestionar expiración, enlaces de cobro y conciliar órdenes de checkout. Usar al implementar flujos de cobro, facturación o recepción de fondos para comercios. NO usar para transferencias salientes (outgoing payments), mutaciones directas de base de datos ni firmas de webhooks. |
| `interledger-protocol-fundamentals` | Manual conceptual de Interledger Protocol (ILP): modelo en capas, paquetes Prepare/Fulfill/Reject, transporte STREAM y relación con Rafiki y Open Payments. Usar al diseñar modelos contables y comprender enrutamiento ILP. NO usar para implementar flujos de Open Payments (usar open-payments-transfers). |
| `nextjs-typescript-application-architect` | Procedimiento de arquitectura en Next.js App Router con TypeScript estricto, variables de entorno validadas, Route Handlers y esquemas Zod en frontera. Usar para estructurar endpoints de pago seguros y validar tipos. NO usar para instanciar el cliente Open Payments (server-only-payments-client) ni verificar firmas (webhook-signature-verification). |
| `open-payments-transfers` | Flujo procedimental para resolver Wallet Addresses, crear Incoming Payments, negociar Grants GNAP y emitir Outgoing Payments con Open Payments y Rafiki. Usar al implementar transferencias o cobros. NO usar para mutaciones directas de base de datos ni para estilos visuales de frontend. |
| `rafiki-local-playground` | Procedimiento para interactuar con la instancia local de Rafiki mediante su API GraphQL Admin (creación de cuentas, gestión de assets, peers ILP y webhooks de prueba). Usar para depuración, testing e inicialización de entornos locales de liquidación y wallets. NO usar en entornos productivos, transferencias salientes de usuario ni transacciones reales. |
| `server-only-payments-client` | Procedimiento para estructurar el cliente de Open Payments en aplicaciones Next.js usando App Router, Server Actions y Route Handlers aislados con 'server-only'. Usar al implementar llamadas seguras al SDK de Open Payments y firmar peticiones HTTP. NO usar en frontend del navegador, páginas públicas ni componentes interactivos de cliente. |
| `skill-authoring-standard` | Procedimiento estándar para crear, documentar y validar skills en este proyecto. Usar al crear nuevas skills operativas. NO usar para directivas globales de código (usar rules) ni para tareas sin flujo procedimental paso a paso. |
| `webhook-signature-verification` | Procedimiento para verificar firmas HMAC y HTTP signatures en webhooks entrantes de Rafiki y Open Payments. Usar al implementar endpoints de notificación y confirmación verificable de pagos. NO usar para transferencias salientes ni para peticiones directas de usuarios. |

Cada afirmación técnica y procedimiento cuenta con su respaldo documental y fecha de consulta en el archivo `references/sources.md` de la skill respectiva.

---

## 4. Licencia

Este proyecto está distribuido bajo la licencia [Apache 2.0](LICENSE).  
Copyright 2026 MD-Genius-Developers. Consulta [NOTICE](NOTICE) para más detalles.
