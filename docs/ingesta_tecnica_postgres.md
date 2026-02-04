# Ingesta tecnica: conectar PostgreSQL a OpenMetadata

Objetivo: que el conector oficial cree/actualice automaticamente:
`DatabaseService -> Database -> Schemas -> Tables -> Columns`.

## Pasos (UI de OpenMetadata)

1) Ir a `Settings -> Services -> Databases -> Add New Service`.
2) Elegir `Postgres`.
3) Rellenar la conexion (ejemplo para Docker Compose):
   - Host: `host.docker.internal` (o `localhost` si OpenMetadata no esta en Kubernetes)
   - Port: `5432`
   - Username: `om_demo`
   - Password: `om_demo`
   - Database: `opendata_demo`
4) Guardar el servicio.
5) Crear una Ingestion Pipeline para ese servicio y ejecutarla.

## Resultado esperado

Tras la ejecucion:
- Aparecen los schemas `bronze`, `silver`, `gold`.
- Aparecen las tablas y columnas definidas en `sql/opendata_demo_init.sql`.

