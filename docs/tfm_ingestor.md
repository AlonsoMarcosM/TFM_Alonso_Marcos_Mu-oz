# `tfm_ingestor`: enriquecimiento de metadatos (gobierno) via API OpenMetadata

Objetivo: aplicar reglas simples e idempotentes sobre las entidades creadas por la ingesta tecnica (Postgres):
- Domain por esquema (`bronze/silver/gold`)
- Tags por convencion de nombres (prefijos)
- Custom properties "DCAT-like" con defaults

Comportamiento:
- Si un Domain configurado no existe, el script intenta crearlo (PoC).

## Instalacion (modo editable)

```powershell
python -m pip install -e tfm_ingestor[dev]
```

## Configuracion

Ficheros de ejemplo:
- `tfm_ingestor/config/governance_defaults.yaml`
- `tfm_ingestor/config/mapping_rules.yaml`

Prerequisito en OpenMetadata:
- Crear las custom properties usadas por la PoC (ver `docs/custom_properties_openmetadata.md`).
- Crear los tags usados en `tfm_ingestor/config/mapping_rules.yaml`.

Automatizacion recomendada (desde la raiz):

```powershell
# Requiere OpenMetadata levantado y accesible por port-forward
$job = Start-Job -ScriptBlock { kubectl port-forward deployment/openmetadata 8585:8585 }
Start-Sleep -Seconds 3
$token = python .\scripts\infra\generate_om_jwt.py --ttl-hours 2
python .\scripts\infra\bootstrap_governance.py --base-url http://localhost:8585/api/v1 --token $token
Stop-Job $job; Remove-Job $job -Force
```

Autenticacion (ejemplo):
- Exportar un token JWT en `OPENMETADATA_JWT_TOKEN` (obtenido desde OpenMetadata, p.ej. desde perfil/usuario admin o API de login segun version)
- Base URL en `OPENMETADATA_BASE_URL` (por defecto `http://localhost:8585/api/v1`)

## Ejecucion

Dry-run (no aplica cambios):

```powershell
python -m tfm_ingestor --dry-run
```

Aplicar cambios:

```powershell
python -m tfm_ingestor
```

## Tests

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
python -m pytest tfm_ingestor/tests
```

## Flujo completo en un comando

Si quieres ejecutar todo el flujo (infra + ingesta tecnica + bootstrap gobierno + dry-run):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\run_full_flow.ps1
```
