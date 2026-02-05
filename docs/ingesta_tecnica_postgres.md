# Ingesta tecnica: conectar PostgreSQL a OpenMetadata

Objetivo: que el conector oficial cree/actualice automaticamente:
`DatabaseService -> Database -> Schemas -> Tables -> Columns`.

## Opcion recomendada (automatizada desde raiz del repo)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\ingest_postgres.ps1
```

El script:
1) Genera JWT temporal de OpenMetadata.
2) Verifica/crea el servicio `postgres_demo_service`.
3) Ejecuta la ingesta tecnica con un pod temporal `om-postgres-ingest`.
4) Muestra resumen de tablas detectadas y elimina el pod temporal.

Nota: puede aparecer un warning de `pg_stat_statements` en logs. Para esta PoC no bloquea la ingesta de metadatos tecnicos.

## Opcion manual (UI de OpenMetadata)

1) Ir a `Settings -> Services -> Databases -> Add New Service`.
2) Elegir `Postgres`.
3) Rellenar la conexion:
   - Host: `postgres-demo.default.svc.cluster.local`
   - Port: `5432`
   - Username: `om_demo`
   - Password: `om_demo`
   - Database: `opendata_demo`
4) Guardar el servicio.
5) Crear una `Ingestion Pipeline` para ese servicio y ejecutarla.

## Resultado esperado

Tras la ejecucion:
- Aparecen los schemas `bronze`, `silver`, `gold`.
- Aparecen las tablas y columnas definidas en `sql/opendata_demo_init.sql`.
