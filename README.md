# TFM - OpenMetadata + DCAT-AP-ES

Repositorio del Trabajo Fin de Máster:

- Título oficial (ES): `DISEÑO Y CONFIGURACIÓN DE UN MODELO DE METADATOS EN OPENMETADATA CONFORME AL ESTÁNDAR DCAT-AP PARA LA INTEROPERABILIDAD DE CATÁLOGOS DE DATOS`.
- Título oficial (EN): `Design and Configuration of a Metadata Model in OpenMetadata According to the DCAT-AP Standard for Data Catalog Interoperability`.
- Ficha oficial UCLM literal: `docs/tfe_ficha_oficial_uclm.txt`.

## Qué demuestra este proyecto

- Despliegue reproducible de OpenMetadata en Kubernetes + Helm.
- Flujo de metadatos gobernados sobre PostgreSQL demo y OpenMetadata.
- Exportación DCAT-AP-ES en JSON-LD.
- Validación SHACL reproducible incluida en el propio repositorio.
- Shapes SHACL oficiales vendorizadas en `tfm_ingestor/src/tfm_ingestor/resources/shacl`, congeladas desde `datosgobes/DCAT-AP-ES/shacl/1.0.0` en el commit `f2c8a88868b89239c9f54bffdf621cded2401b9f`.

## Alcance funcional

Este TFM trabaja sobre **metadatos**, no sobre datos de negocio.

- Los activos técnicos proceden del PostgreSQL demo `bronze/silver/gold`.
- Solo la capa `gold` entra en el catálogo publicable de la PoC.
- El perfil activo del repositorio es `DCAT-AP-ES` con el caso `HVD` activado para los datasets `gold`.

Importante:

- En la memoria del TFM, `DCAT-AP` sigue siendo el marco oficial del enunciado.
- En la implementación, la PoC usa `DCAT-AP-ES = DCAT-AP 2.1.1 + DCAT-AP HVD 2.2.0 + especificaciones adicionales`.
- La calificación HVD en la PoC se usa como **hipótesis de diseño y validación** para ejercitar la extensión HVD dentro del entorno demo. No debe interpretarse como una calificación jurídica automática de datasets reales fuera de la PoC.

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

## Orden correcto del flujo

1. Levantar infraestructura.
2. Ingestar metadatos técnicos en OpenMetadata.
3. Crear tags y custom properties mínimas.
4. Ejecutar `om_dcat_sync workflow run --dry-run` para refrescar la hoja funcional y generar un plan reproducible.
5. Curar funcionalmente `gold_governance.csv` cuando el workflow indique que faltan obligatorios editoriales.
6. Volver a ejecutar `workflow run --dry-run` para revisar el plan.
7. Ejecutar `workflow run --allow-warnings` para aplicar, exportar y validar.

## Ejecución rápida

Desde la raíz del repo:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\check_prereqs.ps1 -Strict
python -m pip install -r requirements-dev.txt
powershell -ExecutionPolicy Bypass -File .\scripts\infra\run_full_flow.ps1
```

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
- `docs/guia_centralizada.md`
