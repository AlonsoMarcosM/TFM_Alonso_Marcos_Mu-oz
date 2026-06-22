# Fixtures del modo demo (solo lectura)

Esta carpeta reproduce la estructura del repositorio con artefactos **congelados de una
ejecución real previa** del caso de uso de validación. Cuando la consola web se ejecuta con
`TFM_DEMO=1`, `repoRoot()` apunta aquí y todas las lecturas (`/api/status`, `/api/artifacts`,
`/api/governance`, `/api/config`, `/api/jobs`) sirven estos datos, sin Kubernetes ni OpenMetadata.

Contenido:

- `tmp_pytest/` — artefactos de salida: catálogo JSON-LD DCAT-AP-ES, informe SHACL HVD, resumen
  de validación, informe HTML/PDF, planes de workflow, reportes de estado vivo.
- `tfm_ingestor/config/` — hoja gold (`gold_governance.csv`) y YAML editables (defaults DCAT/HVD,
  reglas de mapeo, perfil operativo).
- `tfm_ingestor/src/tfm_ingestor/resources/shacl/manifest.json` — manifiesto del bundle SHACL.
- `state/web_jobs/` — historial curado de ejecuciones (un job de éxito por operación), con rutas
  locales del autor saneadas.

Estos ficheros están versionados a propósito: el `.gitignore` raíz los re-incluye con negaciones
pese a ignorar `tmp_pytest/` y `state/` en el resto del repositorio. Ver el detalle de despliegue
en [`docs/app_web.md`](../../docs/app_web.md).
