---
trigger: glob
globs: "*.ts, *.tsx"
description: "Estándares para desarrollo con TypeScript estricto, React y Server Components en Next.js."
---

# Convenciones de TypeScript y Next.js

## 1. Tipado Estricto
- TypeScript debe configurarse con `strict: true`, `noImplicitAny: true` y `exactOptionalPropertyTypes: true`.
- Queda prohibido el uso del tipo `any`. Utiliza tipos discriminados, genéricos acotados o `unknown` con type guards.
- No silencies el compilador con directivas `@ts-ignore` o `@ts-nocheck` sin justificación documentada y aprobada.

## 2. Arquitectura de Next.js (App Router)
- Mantén una clara distinción entre Server Components y Client Components.
- Marca los módulos de infraestructura, llamadas a bases de datos y clientes de pago con el paquete `server-only` para prevenir filtraciones accidentales al cliente web.
- Coloca `"use client"` únicamente en las hojas del árbol de componentes que requieran interactividad del navegador o hooks de estado.
- Maneja errores asíncronos mediante `error.tsx` y estados de espera mediante `loading.tsx`.
