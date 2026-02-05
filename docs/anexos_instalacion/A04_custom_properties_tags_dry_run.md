# A04 - Custom properties, tags y dry-run del ingestor

## 1) Crear custom properties (tipo `string`) en entidad `table`

Claves usadas por la PoC:
- `dcat_publisher_name`
- `dcat_contact_email`
- `dct_spatial`
- `dct_language`
- `dct_license`
- `dct_accrual_periodicity`
- `tfm_layer`

Detalle del procedimiento:
- Ver `docs/custom_properties_openmetadata.md`

## 2) Crear tags requeridos en OpenMetadata

Segun `tfm_ingestor/config/mapping_rules.yaml`:
- `dcat_theme.transport`
- `dcat_theme.society`
- `dcat_keyword.bici`
- `dcat_keyword.eventos`

## Alternativa automatizada para 1) y 2)

```powershell
$job = Start-Job -ScriptBlock { kubectl port-forward deployment/openmetadata 8585:8585 }
Start-Sleep -Seconds 3
$token = python .\scripts\infra\generate_om_jwt.py --ttl-hours 2
python .\scripts\infra\bootstrap_governance.py --base-url http://localhost:8585/api/v1 --token $token
Stop-Job $job; Remove-Job $job -Force
```

## 3) Ejecutar dry-run del enriquecimiento

Instalar dependencias:

```powershell
python -m pip install -e tfm_ingestor[dev]
```

Variables de entorno (ejemplo):

```powershell
$env:OPENMETADATA_BASE_URL="http://localhost:8585/api/v1"
$env:OPENMETADATA_JWT_TOKEN="<TOKEN_JWT>"
```

Dry-run:

```powershell
python -m tfm_ingestor --dry-run
```

El resultado esperado es un JSON con:
- `dry_run: true`
- `planned`: operaciones PATCH planificadas por tabla
- `applied: 0`

## 4) Aplicacion real (sin dry-run)

```powershell
python -m tfm_ingestor
```

## Flujo completo (todos los pasos naturales en orden)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\run_full_flow.ps1
```
