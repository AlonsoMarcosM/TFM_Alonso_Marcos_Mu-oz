# Guia centralizada (leer primero)

Objetivo: que no tengas que saltar por demasiados archivos.

## Ruta mínima (4 comandos)

Desde la raiz del repo:

```powershell
# 1) Levantar toda la PoC
powershell -ExecutionPolicy Bypass -File .\scripts\infra\run_full_flow.ps1

# 2) Ver estado de stack
powershell -ExecutionPolicy Bypass -File .\scripts\infra\status_infra.ps1

# 3) Preparar acceso API (port-forward + token JWT)
# Terminal A (dejar abierto):
powershell -ExecutionPolicy Bypass -File .\scripts\infra\port_forward_openmetadata.ps1

# Terminal B:
$env:OPENMETADATA_BASE_URL = "http://localhost:8585/api/v1"
$env:OPENMETADATA_JWT_TOKEN = python .\scripts\infra\generate_om_jwt.py --ttl-hours 2

# 4) Ver plan de gobierno sin aplicar cambios
python -m tfm_ingestor --dry-run
```

Si sale `401 Not Authorized! Token not present`, falta `OPENMETADATA_JWT_TOKEN` en esa terminal
o el token ya expiró (vuelve a generarlo).

## Si vas a borrar el cluster y conservar estado

```powershell
# Backup del estado OpenMetadata (tags/dominios/config metadata) a carpeta del proyecto
powershell -ExecutionPolicy Bypass -File .\scripts\infra\backup_openmetadata_state.ps1

# Borrar cluster conservando snapshot
powershell -ExecutionPolicy Bypass -File .\scripts\infra\delete_cluster_preserve_state.ps1

# Volver a levantar (restaura snapshot automaticamente)
powershell -ExecutionPolicy Bypass -File .\scripts\infra\launch_infra.ps1
```

## Que hace exactamente el flujo completo

`run_full_flow.ps1` ejecuta en orden:
1. PostgreSQL dummy dentro de Kubernetes (`postgres-demo`)
2. despliegue K8s + Helm de OpenMetadata
3. ingesta técnica de PostgreSQL
4. creación de custom properties y tags
5. `tfm_ingestor --dry-run`

## Documentación (orden recomendado)

1. `README.md` (vision general + portfolio)
2. `docs/tfm_oficial_objetivos_decisiones.md` (enunciado oficial + alcance real + decisiones)
3. `docs/guia_centralizada.md` (esta guia operativa)
4. `docs/anexos_instalacion/README.md` (evidencia paso a paso para memoria)

Solo si necesitas detalle:
- `docs/openmetadata_k8s.md`
- `docs/ingesta_tecnica_postgres.md`
- `docs/custom_properties_openmetadata.md`
- `docs/tfm_ingestor.md`
