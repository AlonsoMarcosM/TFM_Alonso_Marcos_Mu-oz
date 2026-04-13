# A04 - Custom properties, tags y dry-run de gobierno

## 1) Custom properties mínimas de la PoC

En entidad `table` (tipo `string`):

- `dcat_publisher_name`
- `dcat_hvd_category`
- `dcat_access_url`

Detalle:

- `docs/custom_properties_openmetadata.md`

## 2) Tags requeridos

Según `tfm_ingestor/config/mapping_rules.yaml`:

- `dcat_theme.transporte`
- `dcat_theme.cultura_ocio`

## 3) Bootstrap automático

```powershell
$job = Start-Job -ScriptBlock { kubectl port-forward deployment/openmetadata 8585:8585 }
Start-Sleep -Seconds 3
$token = python .\scripts\infra\generate_om_jwt.py --ttl-hours 2
python .\scripts\infra\bootstrap_governance.py --base-url http://localhost:8585/api/v1 --token $token
Stop-Job $job; Remove-Job $job -Force
```

## 4) Dry-run del enriquecimiento

```powershell
python -m pip install -r requirements-dev.txt
$env:OPENMETADATA_BASE_URL="http://localhost:8585/api/v1"
$env:OPENMETADATA_JWT_TOKEN="<TOKEN_JWT>"
python -m om_dcat_sync workflow run --dry-run
```

Resultado esperado:

- `workflow.dry_run: true`
- `workflow.sheet_refreshed: true`
- `workflow.sheet_valid: true` o `false` si aún faltan metadatos funcionales
- `sync.planned`: operaciones PATCH por tabla cuando la hoja ya es válida
- `sync.applied: 0`

## 5) Aplicación real

```powershell
python -m om_dcat_sync workflow run --allow-warnings
```

## 6) Validación integral del sistema

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\run_validation_suite.ps1
```

Artefactos esperados:

- `tmp_pytest/runtime_validation_report.json`
- `tmp_pytest/validation_suite_summary.json`
- `tmp_pytest/validation_suite_catalog.jsonld`
- `tmp_pytest/validation_suite_shacl_report.ttl`
