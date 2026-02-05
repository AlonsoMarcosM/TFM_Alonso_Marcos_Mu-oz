# Guia centralizada (leer primero)

Objetivo: que no tengas que saltar por demasiados archivos.

## Ruta minima (3 comandos)

Desde la raiz del repo:

```powershell
# 1) Levantar toda la PoC
powershell -ExecutionPolicy Bypass -File .\scripts\infra\run_full_flow.ps1

# 2) Ver estado de stack
powershell -ExecutionPolicy Bypass -File .\scripts\infra\status_infra.ps1

# 3) Ver plan de gobierno sin aplicar cambios
python -m tfm_ingestor --dry-run
```

## Que hace exactamente el flujo completo

`run_full_flow.ps1` ejecuta en orden:
1. PostgreSQL dummy dentro de Kubernetes (`postgres-demo`)
2. despliegue K8s + Helm de OpenMetadata
3. ingesta tecnica de PostgreSQL
4. creacion de custom properties y tags
5. `tfm_ingestor --dry-run`

## Documentacion (orden recomendado)

1. `README.md` (vision general + portfolio)
2. `docs/guia_centralizada.md` (esta guia operativa)
3. `docs/anexos_instalacion/README.md` (evidencia paso a paso para memoria)

Solo si necesitas detalle:
- `docs/openmetadata_k8s.md`
- `docs/ingesta_tecnica_postgres.md`
- `docs/custom_properties_openmetadata.md`
- `docs/tfm_ingestor.md`
