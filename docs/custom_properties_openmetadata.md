# OpenMetadata: custom properties activas

`om_dcat_sync` escribe metadatos de gobierno en `Table.extension` solo cuando son imprescindibles para representar el perfil activo y OpenMetadata no los modela de forma nativa en `Table`.

## Objetivo

Mantener activas únicamente las custom properties necesarias para construir un `dcat:Dataset` HVD y su `dcat:Distribution` mínima, sin alargar artificialmente el modelo.

## Custom properties activas

Tipo `string` sobre entidad `table`:

- `dcat_publisher_name`
- `dcat_hvd_category`
- `dcat_access_url`

Uso:

- `dcat_publisher_name`: nombre del agente publicador exportado en `dct:publisher`.
- `dcat_hvd_category`: URI o alias normalizado de `dcatap:hvdCategory`.
- `dcat_access_url`: `dcat:accessURL` de la distribución.

## Qué no forma parte del contrato activo

Estas propiedades no forman parte del contrato vivo de la plataforma:

- `dct_license`
- `tfm_layer`
- `dcat_contact_email`
- `dct_spatial`
- `dct_language`
- `dcat_download_url`
- `dcat_endpoint_url`
- `dct_issued`
- `dct_modified`
- `dct_temporal`
- `dct_accrual_periodicity`
- `dcat_landing_page`
- `dct_identifier`

Interpretación:

- `dct:license` sigue siendo obligatoria en `Catalog` y en el caso HVD se aplica también a `Distribution` y `DataService`, pero se gobierna por configuración global del sistema, no por tabla;
- `dcat_access_url` sí permanece activa porque es obligatoria a través de `Distribution`;
- `dcat_hvd_category` permanece activa porque la plataforma ha activado el caso HVD;
- `dcat_endpoint_url` no se guarda en OpenMetadata porque el `DataService` se deriva por configuración del publicador.

## Creación vía API

1. Obtener ID del tipo `table`.
2. Obtener ID del tipo `string`.
3. Crear cada custom property en `table`.

Ejemplo:

```json
{
  "description": "Categoría HVD DCAT-AP-ES activa para el dataset",
  "name": "dcat_hvd_category",
  "propertyType": {
    "id": "<STRING_FIELD_TYPE_ID>",
    "type": "string"
  }
}
```

## Automatización recomendada

```powershell
$job = Start-Job -ScriptBlock { kubectl port-forward deployment/openmetadata 8585:8585 }
Start-Sleep -Seconds 3
$token = python .\scripts\infra\generate_om_jwt.py --ttl-hours 2
python .\scripts\infra\bootstrap_governance.py --base-url http://localhost:8585/api/v1 --token $token
Stop-Job $job; Remove-Job $job -Force
```

Validación del estado resultante:

```powershell
python -m om_dcat_sync validate-runtime --strict --output tmp_pytest/runtime_validation_report.json
```
