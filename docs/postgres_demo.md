# Fuente dummy: PostgreSQL (`bronze/silver/gold`)

## Por qué existe en el TFM

PostgreSQL dummy no sustituye a CKAN: lo complementa.

- Da una base técnica estable para ingesta y pruebas repetibles.
- Evita depender de una instantánea externa puntual de CKAN.
- Permite demostrar el flujo completo en cualquier máquina.

CKAN se usa después para enriquecer metadatos (harvesting), no para bootstrap técnico inicial.

## Arranque en Kubernetes

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\deploy_postgres_k8s.ps1
```

Parámetros por defecto:
- Host: `postgres-demo.default.svc.cluster.local`
- Puerto: `5432`
- DB: `opendata_demo`
- Usuario: `om_demo`
- Password: `om_demo`

Inicialización:
- SQL de esquema + inserts: `sql/opendata_demo_init.sql`
- Se aplica vía ConfigMap al arrancar `postgres-demo`.

## Nota de privacidad

Los datos de esta base son sintéticos/anonimizados para uso docente.
El TFM no persigue análisis de contenido, sino gestión de metadatos.
