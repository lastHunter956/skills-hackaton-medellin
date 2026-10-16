---
trigger: model_decision
description: "Fuente única de invariantes de negocio para transferencias, Open Payments, Rafiki y estados de pago."
---

# Invariantes del Dominio de Pagos (Open Payments)

Este documento es la **fuente de verdad única** de invariantes financieras del proyecto. Ningún componente puede eludir estas reglas.

## 1. Precisión Numérica y Moneda
- **Cero Floats:** Todo valor monetario debe representarse como entero en su unidad mínima (`value` como integer o bigint).
- **Tupla Monetaria Obligatoria:** Toda entidad de monto debe asociar `value`, `assetCode` (e.g. ISO 4217) y `assetScale`.
- Las conversiones y cálculos intermedios deben realizarse con librerías de precisión arbitraria o tipos enteros, nunca con punto flotante nativo de JavaScript.

## 2. Máquina de Estados de Pagos
- Todo pago debe transitar exclusivamente por los estados formales del ciclo de vida (`PENDING`, `AUTHORIZED`, `PROCESSING`, `COMPLETED`, `FAILED`, `CANCELLED`).
- Cualquier intento de transición ilegal debe arrojar un error de dominio controlado y revertir la operación.
- El estado `COMPLETED` se alcanza **únicamente** tras recibir una confirmación criptográfica o webhook verificado de Rafiki/Open Payments; **nunca** asumas que el pago está completado por el mero hecho de invocar la creación del `outgoing-payment`.

## 3. Idempotencia y Reintentos
- Toda solicitud saliente que mute saldos o inicie pagos debe incluir una `Idempotency-Key` determinista única.
- Prohibido reintentar a ciegas llamadas HTTP fallidas que involucren débitos o autorizaciones sin validar previamente el estado del intento persistido.

## 4. Aislamiento y Consentimiento
- Las claves privadas de firma y las instancias del SDK de Open Payments residen exclusivamente en módulos `server-only` de backend.
- Los callbacks de consentimiento interactivo deben validarse estrictamente contra el intento original en base de datos cotejando `state`, `nonce`, usuario autenticado e identificador de sesión.
- Cada evento y cambio de estado debe persistirse en la tabla `audit_events`. Queda terminantemente prohibido incluir PII, tokens de acceso o claves privadas en logs de auditoría o consola.
