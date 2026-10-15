# Propuesta de Skill: Webhook Signature Verification

## 1. Identificador y Propósito
- **Nombre:** `webhook-signature-verification`
- **Ubicación destino (al pasar a execute):** `.agents/skills/webhook-signature-verification/`
- **Descripción:** Procedimiento para verificar firmas HMAC y HTTP signatures en webhooks entrantes de Rafiki y Open Payments. Usar al implementar endpoints de notificación y confirmación verificable de pagos. NO usar para transferencias salientes ni para peticiones directas de usuarios.

## 2. Cumplimiento de Invariantes de Negocio (Rule 10)
- **Confirmación Verificable:** La regla `.agents/rules/10-payments-domain.md` establece que el estado `COMPLETED` solo puede alcanzarse tras recibir una confirmación criptográfica o webhook verificado. Esta skill implementa el estándar técnico para satisfacer dicha regla.

## 3. Especificación de Archivos a Crear

### A. `SKILL.md` (≤ 200 líneas)
- **Frontmatter:** `name: webhook-signature-verification`, `description` ≤ 400 caracteres.
- **Flujo en 5 Pasos:**
  1. Captura de `rawBody` sin parseo previo (`await req.text()`).
  2. Extracción de cabeceras de firma y marca temporal (`rafiki-signature`, `t=...`).
  3. Cálculo criptográfico HMAC-SHA256 y comparación en tiempo constante (`crypto.timingSafeEqual`).
  4. Mapeo del evento (`incoming_payment.completed`, `outgoing_payment.completed`).
  5. Transición atómica de estado a `COMPLETED` e inserción en `audit_events`.

### B. `references/signature-algorithms.md`
- Detalle de implementación con `node:crypto` para HMAC-SHA256 y RFC 9421 (HTTP Message Signatures).
- Prevención de ataques de temporización (timing attacks) y repetición (replay attacks con ventana ≤ 300s).

### C. `references/webhook-event-types.md`
- Catálogo de tipos de eventos emitidos por Rafiki y su mapeo hacia la máquina de estados local.

## 4. Estado Actual del Entorno
- La fase activa en `.agents/state/phase` es **`audit`**.
- El hook `payments-guard.py` bloquea escrituras fuera de `docs/proposals/`.
- Para materializar esta skill en `.agents/skills/`, se requiere que el usuario cambie la fase a **`execute`** o **`bootstrap`**.
