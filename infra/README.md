# Infraestructura Local

Este directorio contiene las definiciones de Docker Compose y Dockerfile para desarrollo local.

## Modos de Ejecución

### Modo A: Aplicación Next.js + PostgreSQL
Orquesta la aplicación web y su base de datos relacional local:
```bash
docker compose -f infra/docker-compose.app.yml --env-file infra/.env.example config
```

### Modo B: Rafiki Local (Servicios Auxiliares)
Orquesta PostgreSQL y Redis para la infraestructura de Open Payments y Rafiki:
```bash
docker compose -f infra/docker-compose.rafiki.yml --env-file infra/.env.example config
```

## Políticas de Seguridad Aplicadas
- **Usuario no root:** En `Dockerfile.app` mediante usuario `appuser`.
- **Aislamiento de red:** Redes bridge dedicadas (`app-net`, `rafiki-net`). Sin `network_mode: host`.
- **Binding de puertos:** Estrictamente vinculados a `127.0.0.1`.
- **Sin privilegios:** Sin `--privileged` y sin montaje de `/var/run/docker.sock`.
- **Variables de entorno:** Parametrizadas desde `.env` con plantilla en `infra/.env.example`.
