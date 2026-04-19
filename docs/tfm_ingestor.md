# `om_dcat_sync` (alias `tfm_ingestor`)

CLI para enriquecer, exportar y validar metadatos `DCAT-AP-ES` desde OpenMetadata.

## Nombre y alcance del CLI

Nombre recomendado en documentación nueva:

- `om_dcat_sync`

Nombre conservado por compatibilidad:

- `tfm_ingestor`

La diferencia es deliberada. `om_dcat_sync` describe mejor el objetivo actual: sincronizar gobierno entre OpenMetadata y una salida DCAT-AP-ES validable. `tfm_ingestor` se mantiene como paquete Python e import path histórico para no romper tests, instalación editable ni ejecuciones anteriores.

No se renombran ahora módulos como `workflow_service.py`, `governance_service.py`, `dcat_export.py` o `runtime_validation.py` porque son nombres técnicos claros, coherentes con Python y alineados con los comandos del CLI. La explicación funcional se da en español en la documentación.

## Qué hace y qué no hace

- Sí: trabaja sobre metadatos de catálogo en entidades `Table/View`.
- Sí: aplica cambios idempotentes por API REST.
- Sí: gobierna los obligatorios activos del perfil `DCAT-AP-ES` con el caso `hvd`.
- Sí: mantiene `dcat_publisher_name`, `dcat_hvd_category` y `dcat_access_url` como custom properties activas.
- Sí: usa `dcat_theme.*` como familia de tags gestionadas.
- Sí: permite usar una hoja CSV para que una persona no técnica mantenga título, descripción, publicador, temática, categoría HVD y URL de acceso.
- Sí: exporta `Catalog`, `Dataset`, `Distribution`, `DataService` y `Agent`.
- No: no implementa GeoDCAT-AP ni HealthDCAT-AP.
- No: no sustituye a una API productiva real; el `DataService` de la PoC es una representación metadata reproducible del canal de acceso.

## Instalación

```powershell
python -m pip install -r requirements-dev.txt
```

Alternativa si solo quieres instalar el módulo Python y sus extras:

```powershell
python -m pip install -e tfm_ingestor[dev,infra,validation]
```

## Configuración base

Archivos principales:

- `tfm_ingestor/config/operational_profile.yaml`
- `tfm_ingestor/config/governance_defaults.yaml`
- `tfm_ingestor/config/mapping_rules.yaml`
- `tfm_ingestor/config/ckan_harvest.yaml`
- `tfm_ingestor/config/gold_governance.csv`

Estos nombres quedan como contrato técnico estable. En castellano equivalen a: perfil operativo, defaults de gobierno, reglas de mapeo, configuración CKAN y hoja de gobierno gold. La traducción se usa en texto, no en el nombre físico del fichero, para no duplicar rutas ni romper automatización.

Prerequisitos en OpenMetadata:

- custom property `dcat_publisher_name`
- custom property `dcat_hvd_category`
- custom property `dcat_access_url`
- tags `dcat_theme.*`

## Autenticación

```powershell
$env:OPENMETADATA_BASE_URL = "http://localhost:8585/api/v1"
$env:OPENMETADATA_JWT_TOKEN = python .\scripts\infra\generate_om_jwt.py --ttl-hours 2
```

## Workflow canónico

El punto de entrada principal para operador técnico y automatización es:

```powershell
python -m om_dcat_sync workflow run --dry-run
```

Comportamiento esperado:

- carga el perfil operativo de `tfm_ingestor/config/operational_profile.yaml`;
- descubre automáticamente las tablas `gold` visibles en OpenMetadata;
- genera o refresca `tfm_ingestor/config/gold_governance.csv`;
- conserva la curación manual previa;
- serializa un plan reproducible cuando se usa `--plan-output`;
- si la hoja aún no cumple obligatorios editoriales, devuelve `sheet_valid=false` y el motivo exacto sin aplicar cambios.

Aplicación completa:

```powershell
python -m om_dcat_sync workflow run --allow-warnings
```

## Flujo recomendado con hoja de gobierno

### 1) Primera ejecución canónica

```powershell
python -m om_dcat_sync workflow run --dry-run
```

Esto refresca la hoja y deja claro si la curación funcional está completa o no.

### 2) Edición funcional

La persona de gobierno puede abrir `tfm_ingestor/config/gold_governance.csv` en Excel o LibreOffice y editar:

- `publicar`
- `titulo_dataset`
- `descripcion_dataset`
- `publicador`
- `tematica_dcat`
- `categoria_hvd`
- `access_url_distribucion`

No debería tocar:

- `schema_name`
- `table_name`
- `table_fqn`

Valores temáticos admitidos en la PoC demo:

- los sectores NTI-RISP definidos en las SHACL locales congeladas, usando alias de hoja en `snake_case`;
- ejemplos: `transporte`, `cultura_ocio`, `medio_ambiente`, `sector_publico`.

Valores HVD admitidos en la PoC demo:

- las seis categorías superiores del vocabulario europeo HVD;
- ejemplos: `movilidad`, `estadisticas`, `geoespacial`, `observacion_de_la_tierra_y_medio_ambiente`.

### 3) Simular cambios con el mismo workflow

```powershell
python -m om_dcat_sync workflow run --dry-run
```

### 4) Aplicar cambios reales, exportar y validar

```powershell
python -m om_dcat_sync workflow run --allow-warnings
```

Qué sincroniza en OpenMetadata:

- `displayName`
- `description`
- `dcat_publisher_name`
- `dcat_hvd_category`
- `dcat_access_url`
- `dcat_theme.*`
- limpieza de metadatos heredados gestionados que ya no forman parte del perfil activo

Comandos detallados de bajo nivel:

```powershell
python -m om_dcat_sync generate-governance-sheet
python -m om_dcat_sync --sheet tfm_ingestor/config/gold_governance.csv --dry-run
python -m om_dcat_sync --sheet tfm_ingestor/config/gold_governance.csv
```

## Harvesting CKAN

Uso opcional:

```powershell
python -m om_dcat_sync harvest-ckan --dry-run
python -m om_dcat_sync harvest-ckan
```

Puede completar:

- `displayName`
- `description`
- `dcat_publisher_name`
- `dcat_hvd_category` si la temática CKAN mapea a una categoría HVD configurada
- `dcat_access_url`
- temática

## Exportación DCAT-AP-ES

```powershell
python -m om_dcat_sync export-dcat --output dcat_catalog.jsonld
```

La exportación activa genera:

- `dcat:Catalog`
- `dcat:Dataset`
- `dcat:Distribution`
- `dcat:DataService`
- `foaf:Agent`

## Validación SHACL

El validador usa las shapes locales vendorizadas en `tfm_ingestor/src/tfm_ingestor/resources/shacl`. Ese directorio replica `shacl/1.0.0` del repositorio oficial `datosgobes/DCAT-AP-ES`, congelado en el commit `f2c8a88868b89239c9f54bffdf621cded2401b9f`. En ejecución no se descargan shapes remotas.

Validar un JSON-LD ya exportado:

```powershell
python -m om_dcat_sync validate-dcat --input dcat_catalog.jsonld --profile-case hvd --report-output dcat_validation_report.ttl
```

Validar exportando desde OpenMetadata en el mismo paso:

```powershell
python -m om_dcat_sync validate-dcat --profile-case hvd --export-output dcat_catalog.jsonld --allow-warnings --report-output dcat_validation_report.ttl
```

La vía recomendada sigue siendo:

```powershell
python -m om_dcat_sync workflow run --allow-warnings
```

Notas:

- la validación usa shapes oficiales versionadas dentro del repositorio;
- `--profile-case hvd` activa la carga del caso base, la shape base de `DataService` y las shapes HVD;
- `--allow-warnings` permite considerar conforme el caso en que no existan `Violation` y solo aparezcan `Warning`.

## Tests

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"; python -m pytest
```

## Validación estructural del estado vivo

Validar la instancia real de OpenMetadata contra el contrato técnico del SQL demo y la hoja funcional:

```powershell
python -m om_dcat_sync validate-runtime --strict --output tmp_pytest/runtime_validation_report.json
```

Qué comprueba:

- `service`, `database`, `schema`, `table` y `column` esperados según `sql/opendata_demo_init.sql`;
- metadatos de gobierno aplicados en los datasets `gold` publicados;
- ausencia de drift en custom properties heredadas gestionadas.

## Suite de validación de fase

Comando recomendado para cerrar las validaciones vivas del sistema:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\run_validation_suite.ps1
```

La suite ejecuta:

- `validate-runtime`;
- `workflow run --allow-warnings`;
- segunda ejecución idempotente del workflow;
- `pytest`;
- revisión reproducible de higiene Git.

Resultado observado en este entorno tras la última ejecución versionada de la suite:

- `runtime_conforms: true`
- `technical_conforms: true`
- `governance_conforms: true`
- `first_applied: 2`
- `tables_exported: 2`
- `preview_dataset_count: 2`
- `shacl_conforms: true`
- `shacl_warnings: 22`
- `second_applied: 0`
- `second_planned: 0`

Artefacto canónico:

- `tmp_pytest/validation_suite_summary.json`

## Compatibilidad legacy

El alias anterior sigue funcionando:

```powershell
python -m tfm_ingestor --dry-run
python -m tfm_ingestor
```
