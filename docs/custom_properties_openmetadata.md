# OpenMetadata: custom properties necesarias (DCAT-like) y como crearlas (API)

El ingestor (`tfm_ingestor`) rellena custom properties en `Table.extension.customProperties`.
Para que OpenMetadata las acepte, primero deben existir como **custom properties** en la entidad `table`.

## Propiedades usadas en esta PoC

Claves (todas tipo `string`):
- `dcat_publisher_name`
- `dcat_contact_email`
- `dct_spatial`
- `dct_language`
- `dct_license`
- `dct_accrual_periodicity`
- `tfm_layer`

## Creacion via API (resumen)

1) Obtener el id del tipo de entidad `table`:
- GET `http://localhost:8585/api/v1/metadata/types?limit=10000`
- Buscar el objeto con `"name": "table"` y anotar su `id`.

2) Obtener el id del tipo de campo `string`:
- GET `http://localhost:8585/api/v1/metadata/types?category=field&limit=10000`
- Buscar `"name": "string"` y anotar su `id`.

3) Crear cada custom property (una a una) en la entidad `table`:
- PUT `http://localhost:8585/api/v1/metadata/types/<TABLE_TYPE_ID>`
- Body (ejemplo):

```json
{
  "description": "DCAT publisher name",
  "name": "dcat_publisher_name",
  "propertyType": {
    "id": "<STRING_FIELD_TYPE_ID>",
    "type": "string"
  }
}
```

Nota: en OpenMetadata, la gestion de tipos y custom properties puede variar segun version; si tu instancia no acepta este flujo, ajusta el endpoint/metodo segun la documentacion oficial de tu version.

## Automatizacion recomendada

En este repositorio se incluye un script que crea:
- Clasificaciones/tags DCAT de la PoC
- Custom properties de tabla requeridas por `tfm_ingestor`

```powershell
$job = Start-Job -ScriptBlock { kubectl port-forward deployment/openmetadata 8585:8585 }
Start-Sleep -Seconds 3
$token = python .\scripts\infra\generate_om_jwt.py --ttl-hours 2
python .\scripts\infra\bootstrap_governance.py --base-url http://localhost:8585/api/v1 --token $token
Stop-Job $job; Remove-Job $job -Force
```
