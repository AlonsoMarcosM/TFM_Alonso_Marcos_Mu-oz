# Anexos de instalación replicables

Estos anexos documentan el despliegue de la PoC para que pueda repetirse desde cero.

Orden recomendado:

1. `A01_prerrequisitos.md`
2. `A02_despliegue_infra_desde_repo.md`
3. `A03_ingesta_tecnica_postgres.md`
4. `A04_custom_properties_tags_dry_run.md`

Documento conceptual complementario:

- `../openmetadata_k8s.md`: explicación de la infraestructura para memoria, defensa y portfolio.

Objetivo de arquitectura:

- Ejecutar todo desde la raíz del repo.
- Mantener despliegue portable en local, VPS o cloud con Kubernetes.
- Separar claramente aplicación, dependencias y base de datos demo.

Atajo de ejecución total:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\run_full_flow.ps1
```

Atajo de validación completa:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\run_validation_suite.ps1
```
