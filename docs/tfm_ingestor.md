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
- Crear los tags usados en `tfm_ingestor/config/mapping_rules.yaml` (si no existen, la asignacion de tags fallara).

Autenticacion (ejemplo):
- Exportar un token JWT en `OPENMETADATA_JWT_TOKEN`
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
python -m pytest
```
