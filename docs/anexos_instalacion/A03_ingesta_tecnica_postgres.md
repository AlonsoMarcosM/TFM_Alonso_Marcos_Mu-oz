# A03 - Conectar PostgreSQL e ingesta tecnica en OpenMetadata

## PostgreSQL dummy

La base se levanta en Kubernetes (`postgres-demo`) y se inicializa con:
- `sql/opendata_demo_init.sql`

Credenciales:
- Host (desde Kubernetes local): `postgres-demo.default.svc.cluster.local`
- Port: `5432`
- Database: `opendata_demo`
- User: `om_demo`
- Password: `om_demo`

## Alta de servicio en OpenMetadata (UI)

1. `Settings -> Services -> Databases -> Add New Service`
2. Tipo: `Postgres`
3. Completar conexion con los datos anteriores
4. Guardar

## Ejecutar ingesta tecnica

1. Crear `Ingestion Pipeline` sobre el servicio
2. Ejecutar pipeline manualmente

## Opcion automatizada (recomendada)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\ingest_postgres.ps1
```

Este script deja evidencia en consola de:
- Creacion/verificacion del `DatabaseService`
- Ejecucion de ingesta con pod temporal `om-postgres-ingest`
- Resumen de tablas detectadas

## Resultado esperado

- Service de base de datos creado
- Database `opendata_demo`
- Schemas: `bronze`, `silver`, `gold`
- Tables/Columns segun `sql/opendata_demo_init.sql`
