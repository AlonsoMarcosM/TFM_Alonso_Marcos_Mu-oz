# Fuente dummy: PostgreSQL (bronze/silver/gold) + datos inventados

Objetivo: una fuente tecnica gratuita y demo-friendly para que OpenMetadata cree entidades tecnicas automaticamente.

## Arranque con Docker Compose (recomendado)

Desde la raiz del repo:

```powershell
docker compose up -d
```

Parametros por defecto (ver `docker-compose.yml`):
- Host: `localhost`
- Puerto: `5432`
- DB: `opendata_demo`
- Usuario: `om_demo`
- Password: `om_demo`

La inicializacion (DDL + inserts) esta en `sql/opendata_demo_init.sql` y se ejecuta automaticamente en el primer arranque del contenedor.

## Conectividad desde OpenMetadata en Kubernetes

Si OpenMetadata corre en Kubernetes local (Docker Desktop), una opcion simple es conectar a Postgres usando:
- Host: `host.docker.internal`
- Puerto: `5432`

Si esto no resolviera en tu instalacion, alternativa: desplegar Postgres tambien dentro del cluster (trabajo futuro / opcional).

