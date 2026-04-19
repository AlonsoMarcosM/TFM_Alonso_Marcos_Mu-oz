# Guía centralizada

Objetivo: ejecutar el flujo completo sin dispersarse y con el orden correcto.

## Principio clave

Primero se ingieren metadatos técnicos en OpenMetadata. Después se enriquecen con metadatos de gobierno `DCAT-AP-ES` y finalmente se exportan y validan con SHACL.

Perfil activo de la PoC:

- solo tablas `gold` como datasets publicables;
- caso `hvd` activo;
- gobierno manual mínimo en OpenMetadata;
- `DataService` derivado por configuración del sistema.

Nombres y rutas canónicas:

- CLI recomendado: `om_dcat_sync`.
- Paquete Python conservado por compatibilidad: `tfm_ingestor`.
- Hoja funcional: `tfm_ingestor/config/gold_governance.csv`.
- Mapa de estructura y nomenclatura: `docs/estructura_repositorio.md`.

## Ruta mínima recomendada

Desde la raíz del repo:

### 0) Instalar dependencias Python

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\check_prereqs.ps1 -Strict
python -m pip install -r requirements-dev.txt
```

### 1) Levantar stack base

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\run_full_flow.ps1
```

### 2) Ver estado

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\status_infra.ps1
```

### 3) Preparar acceso API

Terminal A:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\port_forward_openmetadata.ps1
```

Terminal B:

```powershell
$env:OPENMETADATA_BASE_URL = "http://localhost:8585/api/v1"
$env:OPENMETADATA_JWT_TOKEN = python .\scripts\infra\generate_om_jwt.py --ttl-hours 2
```

### 4) Ejecutar el workflow canónico en dry-run

```powershell
python -m om_dcat_sync workflow run --dry-run
```

### 5) Curación funcional

Editar `tfm_ingestor/config/gold_governance.csv` con Excel o LibreOffice.

Columnas funcionales:

- `publicar`
- `titulo_dataset`
- `descripcion_dataset`
- `publicador`
- `tematica_dcat`
- `categoria_hvd`
- `access_url_distribucion`

### 6) Revisar de nuevo el plan con el mismo workflow

```powershell
python -m om_dcat_sync workflow run --dry-run
```

### 7) Aplicar, exportar y validar

```powershell
python -m om_dcat_sync workflow run --allow-warnings
```

Si quieres ejecutar la validación completa contra la infra real:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\validate_live_dcat.ps1
```

Si quieres ejecutar la validación integral de fases 04-05:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\run_validation_suite.ps1
```

## Ruta equivalente con app web

La misma ruta puede ejecutarse desde `web/`, usando botones sobre los scripts versionados:

```powershell
cd .\web
npm install
npm run dev
```

Abrir `http://localhost:3000` y seguir:

1. `Infraestructura`: comprobar prerrequisitos y, si procede, ejecutar `Reset limpio y recrear PoC`.
2. `Ingesta`: ejecutar `Ingestar PostgreSQL demo` y `Preparar tags y custom properties`.
3. `Gobierno`: revisar, autorrellenar si se quiere para demo y guardar `gold_governance.csv`.
4. `Workflow`: ejecutar `Dry-run del workflow` y después `Aplicar workflow`.
5. `DCAT`, `Estado vivo` y `Validación`: exportar, validar y cerrar evidencias.
6. `Artefactos` y `Ejecuciones`: revisar resultados, logs, resúmenes y ficheros generados.

Cada ejecución desde la web queda registrada como job en `state/web_jobs/` y muestra un resultado visible: mensaje final, duración, código de salida, resumen de la salida JSON y artefactos generados.

## Harvesting CKAN

Opcional:

```powershell
python -m om_dcat_sync harvest-ckan --dry-run
python -m om_dcat_sync harvest-ckan
```

Comandos detallados para depuración o uso avanzado:

```powershell
python -m om_dcat_sync generate-governance-sheet
python -m om_dcat_sync --sheet tfm_ingestor/config/gold_governance.csv --dry-run
python -m om_dcat_sync --sheet tfm_ingestor/config/gold_governance.csv
python -m om_dcat_sync export-dcat --output dcat_catalog.jsonld
python -m om_dcat_sync validate-dcat --profile-case hvd --input dcat_catalog.jsonld --allow-warnings --report-output dcat_validation_report.ttl
```

La validación SHACL usa exclusivamente el bundle local `tfm_ingestor/src/tfm_ingestor/resources/shacl`, congelado desde `datosgobes/DCAT-AP-ES/shacl/1.0.0` en el commit `f2c8a88868b89239c9f54bffdf621cded2401b9f`.

## Validación reproducible

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"; python -m pytest
```

Chequeo pre-push reproducible:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\quality\pre_push_checks.ps1
```

Resumen esperado de la suite viva en el entorno actual:

- `runtime_conforms: true`
- `technical_conforms: true`
- `governance_conforms: true`
- `shacl_conforms: true`
- `idempotence_conforms: true`
- `first_applied: 2`
- `second_applied: 0`
- `tables_exported: 2`

## Documentos clave

- `docs/gobierno_funcional_gold.md`
- `docs/dcat_mapping.md`
- `docs/tfm_ingestor.md`
- `docs/tfm_oficial_objetivos_decisiones.md`
- `docs/diagramas_mermaid.md`
