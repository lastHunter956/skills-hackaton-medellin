---
name: webhook-signature-verification
description: "Procedimiento para verificar firmas HMAC y HTTP signatures en webhooks entrantes de Rafiki y Open Payments. Usar al implementar endpoints de notificación y confirmación verificable de pagos. NO usar para transferencias salientes ni para peticiones directas de usuarios."
---

# Verificación Criptográfica de Webhooks de Rafiki

Este documento define el procedimiento para autenticar y validar la integridad de las notificaciones de eventos emitidas por instancias de Rafiki hacia nuestra aplicación.

> [!IMPORTANT]
> **Invariante de Confirmación Verificable:** La regla [.agents/rules/10-payments-domain.md](../../rules/10-payments-domain.md) estipula que un pago solo puede transitar al estado `COMPLETED` tras validar formalmente la firma del evento de webhook o prueba criptográfica.

---

## 1. Propósito
Garantizar que todo evento que altere la máquina de estados de un pago provenga genuinamente del servidor de Rafiki configurado y no haya sido manipulado ni reenviado.

## 2. Cuándo Activar
- Al construir o modificar el Route Handler `/api/webhooks/rafiki`.
- Al procesar eventos de finalización de pagos entrantes (`incoming_payment.completed`) o salientes (`outgoing_payment.completed`).

## 3. Cuándo NO Activar
- Para transferencias salientes o negociación GNAP (usar `open-payments-transfers`).
- Para validar peticiones originadas directamente por clientes o navegadores web.

## 4. Entradas Requeridas
- `rawBody`: Contenido de la petición en su representación exacta de bytes o string crudo.
- Cabecera `rafiki-signature` (o `Signature` según RFC 9421).
- Variable de entorno `RAFIKI_WEBHOOK_SECRET` con la clave simétrica compartida.

---

## 5. Procedimiento Paso a Paso

### Paso 1: Obtención del Raw Body
1. En el Route Handler de Next.js (`app/api/webhooks/rafiki/route.ts`), lee el cuerpo mediante `await req.text()`.
2. **PROHIBIDO** invocar `await req.json()` antes de calcular la firma, ya que la serialización de JSON puede alterar el espaciado y romper el digest criptográfico.

### Paso 2: Extracción y Validación de Cabeceras
1. Obtén la cabecera de firma y la marca temporal (`t=...`).
2. Verifica que la marca temporal esté dentro del rango de tolerancia (máximo 300 segundos respecto a la hora actual) para neutralizar ataques de repetición.

### Paso 3: Cálculo y Comparación Criptográfica
1. Calcula el HMAC-SHA256 del contenido crudo concatenado con el timestamp usando la clave compartida.
2. Compara el digest generado contra la firma recibida empleando comparación en tiempo constante (`crypto.timingSafeEqual`).
3. Para implementaciones de algoritmos y librerías nativas, consulta [references/signature-algorithms.md](./references/signature-algorithms.md).

### Paso 4: Deserialización y Mapeo de Evento
1. Una vez validada la firma, parsea el cuerpo con `JSON.parse`.
2. Identifica el tipo de evento (`type`) contra el catálogo oficial documentado en [references/webhook-event-types.md](./references/webhook-event-types.md).

### Paso 5: Transición Atómica y Auditoría
1. Extrae el identificador del pago (`data.id`) y el estado reportado.
2. Ejecuta una transacción de base de datos para actualizar la orden a `COMPLETED` o `FAILED`.
3. Inserta una fila en `audit_events` registrando la verificación criptográfica exitosa sin almacenar tokens ni claves privadas.

---

## 6. Salidas Esperadas
- Código HTTP 200/204 devuelto al emisor del webhook.
- Actualización atómica en la base de datos local hacia el estado final del pago.
- Registro auditable inmutable.

## 7. Checklist de Verificación
- [ ] Cuerpo de la petición procesado sin alteraciones en su formato crudo.
- [ ] Ventana de tiempo validada para mitigar replay attacks.
- [ ] Comparación de hashes realizada con `timingSafeEqual`.
- [ ] Transición a `COMPLETED` ejecutada únicamente si la firma fue exitosa.

## 8. Casos de Error y Condiciones de Parada
- Si la firma no coincide: responde inmediatamente con HTTP 401 Unauthorized y no ejecutes ninguna mutación.
- Si la marca temporal expiró (> 300s): responde con HTTP 400 Bad Request.
- Si el evento contiene un estado ilegal para la máquina de estados: registra la anomalía y aborta la transacción.

## 9. Fuentes Oficiales y Fecha de Revisión
- Documentación oficial de Webhooks de Rafiki: https://rafiki.dev/integration/webhook-events/
- Fecha de revisión: 2026-10-15
