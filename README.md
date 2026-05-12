# TFM - OpenMetadata + DCAT-AP-ES

Repositorio del Trabajo Fin de Máster:

- Título oficial (ES): `DISEÑO Y CONFIGURACIÓN DE UN MODELO DE METADATOS EN OPENMETADATA CONFORME AL ESTÁNDAR DCAT-AP PARA LA INTEROPERABILIDAD DE CATÁLOGOS DE DATOS`.
- Título oficial (EN): `Design and Configuration of a Metadata Model in OpenMetadata According to the DCAT-AP Standard for Data Catalog Interoperability`.
- Ficha oficial UCLM literal: `docs/tfe_ficha_oficial_uclm.txt`.

## Qué valida este proyecto

- Despliegue reproducible de OpenMetadata en Kubernetes + Helm.
- Flujo de metadatos gobernados sobre PostgreSQL de referencia y OpenMetadata.
- Exportación DCAT-AP-ES en JSON-LD.
- Validación SHACL reproducible incluida en el propio repositorio.
- Shapes SHACL oficiales vendorizadas en `tfm_ingestor/src/tfm_ingestor/resources/shacl`, congeladas desde `datosgobes/DCAT-AP-ES/shacl/1.0.0` en el commit `f2c8a88868b89239c9f54bffdf621cded2401b9f`.

## Alcance funcional

Este TFM trabaja sobre **metadatos**, no sobre datos de negocio.

- Los activos técnicos proceden del PostgreSQL de referencia `bronze/silver/gold`.
- Solo la capa `gold` entra en el catálogo publicable de la plataforma.
- El perfil activo del repositorio es `DCAT-AP-ES` con el caso `HVD` activado para los datasets `gold`.

Los servicios conectados a OpenMetadata forman el catálogo técnico gobernado de la plataforma. En el caso de uso de validación, ese catálogo se publica funcionalmente como catálogo UCLM: `gold_governance.csv` define la curación por dataset y `governance_defaults.yaml` completa publicador, URI de organismo, licencias, contacto, legislación HVD y URLs base. La salida es RDF serializado en JSON-LD, preparado para interoperar con `datos.gob.es` y catálogos europeos compatibles.

Importante:

- En la memoria del TFM, `DCAT-AP` sigue siendo el marco oficial del enunciado.
- En la implementación, la plataforma usa `DCAT-AP-ES = DCAT-AP 2.1.1 + DCAT-AP HVD 2.2.0 + especificaciones adicionales`.
- La calificación HVD en la plataforma se usa como **hipótesis de diseño y validación** para ejercitar la extensión HVD dentro del caso de uso de validación. No debe interpretarse como una calificación jurídica automática de datasets reales fuera de la plataforma.

## Perfil activo del repositorio

Clases activas:

- `dcat:Catalog`
- `dcat:Dataset`
- `dcat:Distribution`
- `dcat:DataService`
- `foaf:Agent`

Metadatos gobernados activos en OpenMetadata:

- `displayName`
- `description`
- custom property `dcat_publisher_name`
- custom property `dcat_hvd_category`
- custom property `dcat_access_url`
- tags `dcat_theme.*`

Metadatos derivados por configuración y exportador:

- `dcatap:applicableLegislation`
- `dct:license` de `Distribution` y `DataService`
- `dct:accessRights` de `DataService`
- `dcat:endpointURL`
- `dcat:endpointDescription`
- `foaf:page`
- `dcat:contactPoint`
- `dcat:servesDataset`

## Estructura del repositorio

El mapa de carpetas, nombres canónicos y criterio de nomenclatura queda documentado en `docs/estructura_repositorio.md`.

Resumen:

- `docs/`: documentación operativa, decisiones y anexos para memoria/defensa.
- `tfm_ingestor/`: paquete Python y núcleo del workflow `om_dcat_sync`.
- `web/`: consola web operativa en Next.js.
- `scripts/`: scripts reproducibles de infraestructura, planificación y calidad.
- `k8s/`: configuración declarativa Helm/Kubernetes.
- `sql/`: PostgreSQL de referencia reproducible.

Se mantienen nombres técnicos en inglés cuando forman parte de comandos, paquetes o convenciones del ecosistema. La documentación y los textos visibles de la app se redactan en español.

## Orden correcto del flujo

1. Levantar infraestructura.
2. Ingestar metadatos técnicos en OpenMetadata.
3. Crear tags y custom properties mínimas.
4. Ejecutar `om_dcat_sync workflow run --dry-run` para refrescar la hoja funcional y generar un plan reproducible.
5. Curar funcionalmente `gold_governance.csv` cuando el workflow indique que faltan obligatorios editoriales; esa hoja es la fuente canónica de sincronización para los datasets `gold`.
6. Volver a ejecutar `workflow run --dry-run` para revisar el plan.
7. Ejecutar `workflow run --allow-warnings` para aplicar, exportar y validar.

## Ejecución rápida

Desde la raíz del repo:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\check_prereqs.ps1 -Strict
python -m pip install -r requirements-dev.txt
powershell -ExecutionPolicy Bypass -File .\scripts\infra\run_full_flow.ps1
```

## App web operativa

La plataforma incluye una consola web en `web/` para ejecutar el flujo sin memorizar comandos. La app no reimplementa el núcleo: lanza la lista cerrada de scripts y comandos versionados, edita `tfm_ingestor/config/gold_governance.csv` y muestra el resultado de cada ejecución.

Para un operador de negocio, el recorrido es: comprobar infraestructura, ingestar activos técnicos, revisar la hoja de gobierno, ejecutar el workflow, exportar DCAT-AP-ES, validar SHACL y revisar evidencias. Cada botón corresponde a un script PowerShell o a `python -m om_dcat_sync`; no existen comandos arbitrarios ni conexión directa desde el frontend a OpenMetadata.

Arranque local:

```powershell
cd .\web
npm install
npm run dev
```

Abrir `http://localhost:3000`.

Cada botón de ejecución crea un job con:

- estado visible (`pendiente`, `en ejecución`, `correcto` o `error`);
- mensaje final de éxito o error;
- resumen de lo ejecutado a partir de la salida JSON del comando;
- duración y código de salida;
- artefactos generados con resumen y vista previa cuando son JSON, JSON-LD, TTL, YAML o CSV;
- historial consultable en la pantalla `Ejecuciones`.

Documentación específica: `docs/app_web.md`.

CLI principal canónico:

```powershell
python -m om_dcat_sync workflow run --dry-run
python -m om_dcat_sync workflow run --allow-warnings
```

Comandos avanzados o de bajo nivel:

```powershell
python -m om_dcat_sync generate-governance-sheet
python -m om_dcat_sync --sheet tfm_ingestor/config/gold_governance.csv --dry-run
python -m om_dcat_sync --sheet tfm_ingestor/config/gold_governance.csv
python -m om_dcat_sync export-dcat --output dcat_catalog.jsonld
python -m om_dcat_sync validate-dcat --profile-case hvd --allow-warnings --report-output tmp_pytest/dcat_validation_report.ttl
```

Compatibilidad legacy:

```powershell
python -m tfm_ingestor --dry-run
python -m tfm_ingestor
```

## Validación reproducible

Tests:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"; python -m pytest
```

Tests de la app web:

```powershell
cd .\web
npm test
```

Validación SHACL del catálogo exportado:

```powershell
python -m om_dcat_sync workflow run --allow-warnings
```

Validación contra la infra real:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\validate_live_dcat.ps1
```

Suite completa de validación hasta fase `05_Validacion`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\run_validation_suite.ps1
```

Esta suite deja artefactos reproducibles en `tmp_pytest/`:

- `runtime_validation_report.json`
- `validation_suite_summary.json`
- `validation_suite_catalog.jsonld`
- `validation_suite_shacl_report.ttl`
- `pre_push_checks.json`

Comprobaciones cubiertas por la suite:

- inventario técnico ingerido (`service`, `database`, `schema`, `table`, `column`) frente a `sql/opendata_demo_init.sql`;
- metadatos de gobierno aplicados frente a `tfm_ingestor/config/gold_governance.csv`;
- exportación y validación SHACL HVD;
- idempotencia del workflow canónico en segunda ejecución;
- `pytest` y revisión de higiene Git.

## Entorno Python

Instalación recomendada:

```powershell
python -m pip install -r requirements-dev.txt
```

Solo ejecución:

```powershell
python -m pip install -r requirements.txt
```

`tfm_ingestor/pyproject.toml` es la configuración canónica del paquete Python. No se añade `setup.py` porque el repo ya usa empaquetado moderno basado en `pyproject.toml`.

El perfil operativo principal del workflow queda concentrado en `tfm_ingestor/config/operational_profile.yaml`.

## Documentación principal

- `docs/dcat_mapping.md`
- `docs/tfe_ficha_oficial_uclm.txt`
- `docs/tfm_oficial_objetivos_decisiones.md`
- `docs/gobierno_funcional_gold.md`
- `docs/custom_properties_openmetadata.md`
- `docs/tfm_ingestor.md`
- `docs/estructura_repositorio.md`
- `docs/guia_centralizada.md`
- `docs/app_web.md`
