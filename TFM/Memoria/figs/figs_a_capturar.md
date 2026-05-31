# Figuras a capturar para la memoria

Guía operativa para producir todas las figuras que la memoria referencia con
`\figuraMemoria{...}`. Mientras una figura no exista, el documento muestra un
recuadro «Captura pendiente» con el nombre del archivo esperado.

## Reglas comunes

- **Carpeta destino**: guardar cada imagen en `TFM/Memoria/figs/`.
- **Formato**: PNG.
- **Nombre exacto**: usar literalmente el nombre indicado en la columna
  «Archivo» (sin cambiar mayúsculas, guiones bajos ni extensión). El nombre es
  el contrato con el `.tex`; si no coincide, la figura no se incrustará.
- **Idioma y privacidad**: interfaz en español si es posible; no debe verse
  ningún token JWT ni secreto en las capturas.
- **Recorte**: capturar la zona útil (no toda la pantalla del sistema
  operativo). Resolución alta y legible.

## Prerrequisitos para capturar

- Consola web levantada: `http://localhost:3000` (en `web/`, `node node_modules/next/dist/bin/next dev`).
- OpenMetadata accesible: `http://localhost:8585` (usuario `admin@open-metadata.org`, contraseña `admin`).
- Infraestructura arrancada (`launch_infra.ps1`) y doble ingesta ejecutada para que haya datos visibles.

---

## A) Capturas de la consola web — `http://localhost:3000`

| Archivo | Pantalla / menú exacto | Qué debe verse |
| --- | --- | --- |
| `fig_web_home.png` | Página inicial (raíz `/`) | Cabecera «Plataforma de Gobierno del Dato» y el *sidebar* con todas las secciones. |
| `fig_web_pantalla_infraestructura.png` | Sección **Infraestructura** | Botón «Comprobar prerrequisitos» y opciones de reset; resultado de un job con estado `correcto`. |
| `fig_web_pantalla_ingesta.png` | Sección **Ingesta** | Servicios `postgres_demo_service` y `postgres_validation_service` y las tablas `gold` descubiertas. |
| `fig_web_pantalla_gobierno.png` | Sección **Gobierno** | Tabla editable de `gold_governance.csv` con las listas controladas de `tematica_dcat` y `categoria_hvd`. |
| `fig_web_pantalla_workflow.png` | Sección **Workflow** | Resultado de `Dry-run` y de `Aplicar workflow` con el resumen de cambios aplicados. |
| `fig_web_pantalla_dcat.png` | Sección **DCAT** | Exportación del catálogo y previsualización del `web_catalog.jsonld`. |
| `fig_web_pantalla_validacion.png` | Sección **Validación** | Pulsa **Suite completa → Ejecutar** y espera al estado `correcto`. Captura el bloque **Resultado** (muestra conformidad de estado vivo, idempotencia y SHACL, duración y código de salida) junto con la lista de artefactos generados, incluidos `validation_report.html` y `validation_report.pdf`. |
| `fig_web_pantalla_shacl.png` | Sección **SHACL** | Esta pantalla muestra el **manifiesto de las shapes DCAT-AP-ES congeladas** (`manifest.json`): evidencia de que la validación no descarga shapes en tiempo de ejecución. Captura la previsualización del manifiesto. *(El informe SHACL con severidades es el artefacto `*_shacl_report.ttl`; se ve en **Artefactos**, no aquí.)* |
| `fig_web_pantalla_artefactos.png` | Sección **Artefactos** | Tabla de evidencias (ruta, estado, tamaño, fecha). Pulsa **Ver** sobre `web_catalog.jsonld` (o `validation_suite_catalog.jsonld`) y captura con la **previsualización del JSON-LD** abierta debajo de la tabla. |

> Sugerencia: tras pulsar `Generar informe HTML/PDF` en **Validación**, los
> artefactos `validation_report.html` y `validation_report.pdf` aparecen en
> **Artefactos**; es un buen estado para capturar `fig_web_pantalla_validacion.png`.

## B) Capturas de OpenMetadata — `http://localhost:8585`

| Archivo | Menú exacto | Qué debe verse |
| --- | --- | --- |
| `fig_postgres_schemas.png` | **Settings → Services → Databases →** `postgres_demo_service` **→** base `opendata_demo` | Los tres esquemas `bronze`, `silver` y `gold`. |
| `fig_om_services.png` | **Settings → Services → Databases** (listado) | Los dos servicios PostgreSQL ingeridos: `postgres_demo_service` y `postgres_validation_service`. |
| `fig_om_tabla_propiedades.png` | **Explore →** tabla `gold` (p. ej. `gold.agenda_cultural_publica`) **→ pestaña Custom Properties** y panel de **Tags** | Estado de gobierno tras ejecutar el flujo completo: las propiedades DCAT `dcat_publisher_name`, `dcat_hvd_category`, `dcat_access_url` con valor, y las etiquetas `dcat_theme.*` aplicadas a la tabla. Esta figura evidencia qué metadatos lleva cada tabla en OpenMetadata después del workflow. |

## C) Capturas de Docker y Kubernetes

| Archivo | Dónde | Qué debe verse |
| --- | --- | --- |
| `fig_docker_containers.png` | Docker Desktop → **Containers**, o terminal con `docker ps` | El contenedor `tfm-om-control-plane` (nodo del clúster Kind) en ejecución. |
| `fig_pods_kubernetes.png` | Terminal: `kubectl get pods -o wide` | Los pods `openmetadata`, `mysql`, `opensearch` y `postgres-demo` en estado `Running`. |

## D) Estructura del paquete Python

| Archivo | Dónde | Qué debe verse |
| --- | --- | --- |
| `fig_modulos_python.png` | Explorador de VS Code expandido en `tfm_ingestor/src/tfm_ingestor/` | Los módulos principales: `workflow_service.py`, `governance_service.py`, `governance_sheet.py`, `om_api.py`, `dcat_export.py`, `shacl_validation.py`, `report_render.py`, `config.py`, `operational_profile.py`, `runtime_validation.py`, `main.py`. |

---

## E) Figuras generadas por Mermaid (NO son capturas)

Estas figuras se producen automáticamente desde los bloques ```mermaid``` de
`docs/diagramas_mermaid.md`. No hay que fotografiarlas: se regeneran con

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\quality\render_mermaid_diagrams.ps1 -RepoRoot (Get-Location).Path
```

Requiere Node.js y `mmdc` (Mermaid CLI) en el `PATH`. Archivos que produce y que
la memoria referencia:

- `fig_arquitectura_logica_capas.png` (bloque 1)
- `fig_flujo_operativo_validacion.png` (bloque 2)
- `fig_pipeline_metadatos.png` (bloque 3)
- `fig_mapeo_activo_dcat_openmetadata.png` (bloque 4)
- `fig_kubernetes_reproducible.png` (bloque 8)
- `fig_arquitectura_logica_detalle.png` (bloque 10)
- `fig_arquitectura_fisica.png` (bloque 11)

## F) Figuras que añade el autor manualmente

- `fig_gantt_planificacion.png`: diagrama de Gantt del roadmap (lo aporta el autor).
- `fig_kanban_board.png`: vista Kanban del GitHub Project al cierre de la fase 05 (lo aporta el autor).

---

## Checklist rápido de archivos pendientes en `TFM/Memoria/figs/`

Capturas manuales (A–D):

- [ ] `fig_web_home.png`
- [ ] `fig_web_pantalla_infraestructura.png`
- [ ] `fig_web_pantalla_ingesta.png`
- [ ] `fig_web_pantalla_gobierno.png`
- [ ] `fig_web_pantalla_workflow.png`
- [ ] `fig_web_pantalla_dcat.png`
- [ ] `fig_web_pantalla_validacion.png`
- [ ] `fig_web_pantalla_shacl.png`
- [ ] `fig_web_pantalla_artefactos.png`
- [ ] `fig_postgres_schemas.png`
- [ ] `fig_om_services.png`
- [ ] `fig_om_tabla_propiedades.png`
- [ ] `fig_docker_containers.png`
- [ ] `fig_pods_kubernetes.png`
- [ ] `fig_modulos_python.png`

Generadas por script Mermaid (E) y por el autor (F): ver secciones anteriores.
