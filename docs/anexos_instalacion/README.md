# Anexos de instalacion (replicables)

Estos anexos documentan el despliegue de la PoC para que pueda repetirse desde cero.

Orden recomendado:
1. `A01_prerrequisitos.md`
2. `A02_despliegue_infra_desde_repo.md`
3. `A03_ingesta_tecnica_postgres.md`
4. `A04_custom_properties_tags_dry_run.md`

Objetivo de arquitectura:
- Ejecutar todo desde la raiz del repo.
- Mantener despliegue portable (local, VPS o cloud con Kubernetes).

Atajo de ejecucion total:
- `powershell -ExecutionPolicy Bypass -File .\scripts\infra\run_full_flow.ps1`
