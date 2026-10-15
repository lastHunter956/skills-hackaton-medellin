---
trigger: glob
globs: "infra/**, Dockerfile*, *.yml, *.yaml"
description: "Políticas de infraestructura, contenedores Docker, Rafiki local y variables de entorno."
---

# Políticas de Infraestructura y Contenedores

## 1. Seguridad en Contenedores Docker
- Prohibido ejecutar contenedores en modo `--privileged` o exponer el socket `/var/run/docker.sock`.
- Todo contenedor debe ejecutar bajo un usuario sin privilegios de root (`USER appuser`).
- Fija siempre los tags de imagen base a versiones inmutables (evita `latest`).

## 2. Orquestación Local con Rafiki
- La infraestructura local de Docker Compose se reserva para servicios auxiliares (PostgreSQL, Redis, Rafiki Mock / Testnet).
- Las configuraciones de red entre contenedores deben estar aisladas mediante redes puente definidas explícitamente.

## 3. Manejo de Variables de Infraestructura
- Todo archivo `docker-compose.yml` debe leer variables sensibles desde variables de entorno de host o archivos no versionados.
- Proporciona siempre un archivo `env.example` en la carpeta `infra/` con valores seguros para pruebas locales.
