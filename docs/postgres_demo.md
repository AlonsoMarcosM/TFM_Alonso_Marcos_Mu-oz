# Fuente dummy: PostgreSQL (bronze/silver/gold) + datos inventados

Objetivo: una fuente tecnica gratuita y demo-friendly para que OpenMetadata cree entidades tecnicas automaticamente.

## Arranque en Kubernetes (recomendado)

Desde la raiz del repo:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\deploy_postgres_k8s.ps1
```

Parametros por defecto:
- Host: `postgres-demo.default.svc.cluster.local`
- Puerto: `5432`
- DB: `opendata_demo`
- Usuario: `om_demo`
- Password: `om_demo`

La inicializacion (DDL + inserts) esta en `sql/opendata_demo_init.sql` y se aplica via ConfigMap al arrancar `postgres-demo`.
