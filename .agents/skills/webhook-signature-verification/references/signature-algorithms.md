# Algoritmos de Firma y Verificación de Webhooks

Este documento describe la formulación matemática y el código para validar firmas de Rafiki.

## 1. Esquema de Firma HMAC-SHA256
La cabecera `rafiki-signature` envía la estampa de tiempo y el digest en formato:
`t=<timestamp_segundos>,v1=<hex_signature>`

### Algoritmo de Validación:
1. Concatena la estampa de tiempo y el raw body usando un punto como separador:
   `signed_payload = t + "." + raw_body`
2. Calcula el HMAC con algoritmo `sha256` utilizando la clave secreta `RAFIKI_WEBHOOK_SECRET`.
3. Compara en tiempo constante para neutralizar análisis de canales laterales:

```typescript
import { createHmac, timingSafeEqual } from "node:crypto";

export function verifyRafikiSignature(
  rawBody: string,
  signatureHeader: string,
  secret: string
): boolean {
  const parts = Object.fromEntries(
    signatureHeader.split(",").map((p) => p.trim().split("="))
  );
  const timestamp = parts["t"];
  const signature = parts["v1"];

  if (!timestamp || !signature) return false;

  const age = Math.floor(Date.now() / 1000) - parseInt(timestamp, 10);
  if (Math.abs(age) > 300) return false;

  const expectedHmac = createHmac("sha256", secret)
    .update(`${timestamp}.${rawBody}`)
    .digest("hex");

  const expectedBuffer = Buffer.from(expectedHmac, "hex");
  const actualBuffer = Buffer.from(signature, "hex");

  if (expectedBuffer.length !== actualBuffer.length) return false;
  return timingSafeEqual(expectedBuffer, actualBuffer);
}
```
