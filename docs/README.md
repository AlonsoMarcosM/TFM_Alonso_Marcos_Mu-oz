# Documentación

- `guia_centralizada.md`: punto ?nico recomendado para ejecutar y entender el flujo.
- `anexos_instalacion/`: anexos paso a paso para reproducir la instalacion (memoria).
- `openmetadata_k8s.md`: detalle de despliegue local de OpenMetadata en Kubernetes con Helm.
- `ingesta_tecnica_postgres.md`: detalle de ingesta técnica PostgreSQL.
- `custom_properties_openmetadata.md`: custom properties (DCAT-like) y automatizacion.
- `tfm_ingestor.md`: ejecución del script de enriquecimiento + tests.
- `diagramas_mermaid.md`: diagramas Mermaid para memoria, README y defensa.
- `dcat_mapping.md`: mapeo DCAT-AP-ES -> OpenMetadata (PoC simple).
- `postgres_demo.md`: fuente dummy PostgreSQL (bronze/silver/gold) para la PoC.
- `planificacion_kanban.md`: enfoque de planificacion/seguimiento (Kanban).
- `github_projects_mvp.md`: MVP automatizable para llevar fases y avance del TFM en GitHub Projects.
- `tfm_oficial_objetivos_decisiones.md`: enunciado oficial + alineacion con alcance real + decisiones técnicas (riesgos/mitigacion).
- `../AGENTS.md`: principios para mantener el repo replicable y (si se quiere) desplegable en VPS/cloud.
- `../scripts/infra/`: scripts para levantar y verificar infraestructura desde la raiz del repo (`launch_infra.ps1`, `deploy_postgres_k8s.ps1`, `ingest_postgres.ps1`, `run_full_flow.ps1`, `helm.ps1`).
  - Persistencia local de estado OpenMetadata: `backup_openmetadata_state.ps1`, `restore_openmetadata_state.ps1`, `delete_cluster_preserve_state.ps1`.
