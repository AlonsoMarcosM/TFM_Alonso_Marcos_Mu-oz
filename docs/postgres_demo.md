# Fuente técnica dummy: PostgreSQL (`bronze/silver/gold`)

## Por qué es el origen canónico de la plataforma

PostgreSQL de referencia sustituye al planteamiento inicial de cosechar desde CKAN como fuente externa activa.

La razón principal es metodológica: OpenMetadata está pensado para gobernar activos de datos y los metadatos que se descubren, curan y validan alrededor de esos activos. Un portal CKAN sirve para publicar y federar catálogos de metadatos; cosecharlo permite copiar metadatos ya publicados, pero no evidencia bien la generación de metadatos técnicos desde un sistema fuente ni el ciclo de gobierno dentro de OpenMetadata.

Desde DAMA, esta decisión es más coherente con:

- gobierno de datos: asignar responsabilidades, reglas y control sobre activos concretos;
- gestión de metadatos: capturar metadatos técnicos desde sistemas fuente y completarlos con metadatos funcionales;
- linaje y trazabilidad: relacionar esquemas, tablas, columnas, propietario funcional, temática y publicación DCAT;
- calidad de metadatos: validar completitud y coherencia sobre activos reproducibles;
- arquitectura de datos: separar el sistema fuente del catálogo de publicación interoperable.

La secuencia de gobierno defendida en el caso de uso de validación es:

1. sistema fuente reproducible en PostgreSQL;
2. descubrimiento técnico en OpenMetadata;
3. curación funcional de los datasets `gold`;
4. derivación de metadatos interoperables `DCAT-AP-ES`;
5. validación formal con SHACL.

Esta secuencia permite explicar gobierno, linaje y trazabilidad desde activos técnicos controlados. Frente a una comparación con plataformas comerciales de datos abiertos, el valor diferencial del TFM no es disponer de más funcionalidad editorial, sino evidenciar de forma reproducible cómo se genera, gobierna y valida el metadato antes de llegar al catálogo publicable.

## Ventajas para el TFM

- Da una base técnica estable para ingesta y pruebas repetibles.
- Permite evidenciar descubrimiento técnico real: `service`, `database`, `schema`, `table` y `column`.
- Evita depender de la disponibilidad, estructura o contenido coyuntural de un catálogo externo.
- Permite explicar varias tablas y capas (`bronze`, `silver`, `gold`) sin introducir complejidad empresarial innecesaria.
- Facilita desplegar la plataforma en local, VPS o cloud con Kubernetes y Helm.

CKAN queda documentado como alternativa analizada y descartada para este alcance. No se usa como origen canónico ni como fuente externa activa de metadatos del TFM.

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
