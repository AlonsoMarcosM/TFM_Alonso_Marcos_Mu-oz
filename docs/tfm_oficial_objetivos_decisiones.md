# Decisiones de alcance e implementación

Este documento ya no reproduce ni resume la ficha oficial. La fuente oficial íntegra queda congelada en `docs/tfe_ficha_oficial_uclm.txt`.

Reglas:

- `docs/tfe_ficha_oficial_uclm.txt` es la copia canónica literal de la ficha UCLM.
- Este archivo contiene únicamente decisiones, justificaciones y trazabilidad técnica del repositorio.
- Si alguna decisión de implementación parece contradecir la ficha oficial, prevalece la ficha oficial.
- Cualquier cambio de alcance debe documentarse aquí, no editando la ficha oficial.

## Cómo se concreta el enunciado en este repositorio

El enunciado oficial habla de `DCAT-AP`. El repositorio no altera ese marco. Lo que hace es concretarlo con un perfil operativo verificable:

- usa `DCAT-AP-ES` como perfil de trabajo;
- activa el caso `HVD` en la PoC;
- trabaja sobre metadatos, no sobre explotación analítica de datos;
- prioriza una salida interoperable validable en `JSON-LD`.

Lectura correcta:

- `DCAT-AP` es el marco académico oficial;
- `DCAT-AP-ES` es la concreción operativa aplicada;
- la extensión `HVD` se activa en la PoC como hipótesis de diseño para cubrir también esa parte del perfil español.

## Decisiones justificadas de alcance

### 1. DCAT-AP-ES como perfil real de validación

- Justificación: `DCAT-AP-ES` es el perfil que combina `DCAT-AP 2.1.1`, `DCAT-AP HVD 2.2.0` y restricciones españolas adicionales.
- Decisión: la PoC valida contra `DCAT-AP-ES` y adopta el caso `hvd` como caso activo del repositorio.
- Evidencia: `docs/dcat_mapping.md`, `README.md`, `tfm_ingestor/src/tfm_ingestor/shacl_validation.py`.

### 2. Activación explícita de HVD en la PoC

- Justificación: se ha decidido que la memoria y el repositorio contemplen el perfil español completo con la extensión HVD activa, sin dejarla como trabajo futuro.
- Decisión: los datasets `gold` se tratan como datasets HVD de la PoC y se exportan con `dcatap:hvdCategory`, `dcatap:applicableLegislation`, `Distribution` HVD y `DataService`.
- Matiz académico: esta activación HVD es una hipótesis de diseño y validación dentro del entorno demo. No equivale por sí sola a una declaración jurídica sobre datasets reales externos a la PoC.
- Evidencia: `docs/dcat_mapping.md`, `tfm_ingestor/config/governance_defaults.yaml`, `tfm_ingestor/src/tfm_ingestor/dcat_export.py`.

### 3. Metadatos, no datos de negocio

- Justificación: OpenMetadata y DCAT gobiernan activos y metadatos.
- Decisión: la PoC valida completitud, trazabilidad e interoperabilidad del metadato, no calidad fila a fila.
- Evidencia: `docs/dcat_mapping.md`, `docs/diagramas_mermaid.md`.

### 4. Solo capa gold como ámbito de publicación

- Justificación: el SQL demo define `bronze`, `silver` y `gold`, pero solo `gold` representa datasets publicables.
- Decisión: el gobierno funcional DCAT-AP-ES se aplica solo a las tablas `gold` de `sql/opendata_demo_init.sql`.
- Evidencia: `sql/opendata_demo_init.sql`, `tfm_ingestor/config/mapping_rules.yaml`, `docs/gobierno_funcional_gold.md`.

### 5. Gobierno mínimo en OpenMetadata

- Justificación: se ha decidido no alargar el modelo con custom metadata no imprescindibles.
- Decisión: en OpenMetadata solo se gobiernan `displayName`, `description`, `dcat_publisher_name`, `dcat_hvd_category`, `dcat_access_url` y tags `dcat_theme.*`.
- Efecto: el resto del perfil activo se deriva por configuración del sistema en el momento de exportación.
- Evidencia: `docs/custom_properties_openmetadata.md`, `docs/gobierno_funcional_gold.md`.

### 6. Distribution y DataService activas

- Justificación: al activar HVD, el perfil no puede cerrarse solo con `Catalog`, `Dataset` y `Distribution`. La PoC necesita además modelar `DataService` y sus vínculos con `servesDataset` y `accessService`.
- Decisión: el exportador genera una `Distribution` por dataset y un `DataService` HVD derivado por dataset.
- Evidencia: `docs/dcat_mapping.md`, `tfm_ingestor/src/tfm_ingestor/dcat_export.py`.

### 7. Hoja funcional para una persona no técnica

- Justificación: si cada dataset exige tocar código o YAML técnico, el mantenimiento no escala.
- Decisión: la curación funcional se concentra en `tfm_ingestor/config/gold_governance.csv`.
- Campos editables por la persona responsable del catálogo: `publicar`, `titulo_dataset`, `descripcion_dataset`, `publicador`, `tematica_dcat`, `categoria_hvd` y `access_url_distribucion`.
- Evidencia: `docs/gobierno_funcional_gold.md`, `tfm_ingestor/src/tfm_ingestor/governance_sheet.py`.

### 8. CKAN como enriquecimiento complementario

- Justificación: el TFM pide harvesting desde fuente externa, pero la defensa no debe depender al cien por cien de esa fuente.
- Decisión: PostgreSQL demo aporta reproducibilidad y CKAN aporta realismo interoperable como complemento.
- Evidencia: `docs/postgres_demo.md`, `tfm_ingestor/src/tfm_ingestor/harvest_ckan.py`.

### 9. JSON-LD como formato de validación actual

- Justificación: el enunciado admite RDF, JSON-LD o equivalente.
- Decisión: la validación formal del repositorio se centra en JSON-LD y SHACL.
- Evidencia: `tfm_ingestor/src/tfm_ingestor/dcat_export.py`, `tfm_ingestor/src/tfm_ingestor/shacl_validation.py`.

### 10. Validación integrada en el sistema

- Justificación: las comprobaciones no deben quedar como ejecución manual aislada del agente.
- Decisión: se mantienen tests versionados, CLI `validate-dcat`, CLI `validate-runtime`, scripts reproducibles y shapes oficiales vendorizadas dentro del paquete, sin descarga en ejecución.
- Evidencia: `tfm_ingestor/tests`, `scripts/infra/validate_live_dcat.ps1`, `scripts/infra/run_validation_suite.ps1`, `tfm_ingestor/src/tfm_ingestor/resources/shacl/`, `tfm_ingestor/src/tfm_ingestor/resources/shacl/manifest.json`.
- Congelación SHACL: árbol oficial `datosgobes/DCAT-AP-ES/shacl/1.0.0` del commit `f2c8a88868b89239c9f54bffdf621cded2401b9f`, fijado localmente el `2026-04-13`.

### 11. Consola web operativa

- Justificación: la web no debe duplicar el TFM ni crear un núcleo paralelo; debe hacer más cómodo ejecutar las capacidades ya versionadas.
- Decisión: la app web se limita a orquestar CLI y scripts existentes, editar la hoja funcional y mostrar evidencias reproducibles. La pantalla de gobierno usa listas controladas para `tematica_dcat` y `categoria_hvd`.
- Alcance de vocabularios: `tematica_dcat` usa los sectores NTI-RISP enumerados en las SHACL locales congeladas; `categoria_hvd` usa las seis categorías superiores del vocabulario europeo HVD.
- Operación de demo: la pantalla `Infraestructura` centraliza prerrequisitos, estado, backup/restore, reset conservando estado, reset limpio y flujo completo reproducible.
- Resultado de ejecución: cada botón crea un job persistido con estado, log, mensaje final, duración, código de salida, resumen de la salida JSON y visualización de artefactos generados. Esto permite demostrar desde la web qué se ha hecho sin depender únicamente de leer el log bruto.
- Evidencia: `docs/app_web.md`, `web/`, `scripts/infra/reset_poc_clean.ps1`, `tfm_ingestor/src/tfm_ingestor/governance_sheet.py`, `tfm_ingestor/src/tfm_ingestor/mapping.py`.

### 12. Estado y calendario canónicos en GitHub Projects

- Justificación: mantener `Estado TFM` y `Status` como campos separados duplica la misma información y dificulta las vistas de seguimiento.
- Decisión: el estado del roadmap se sincroniza sobre el campo nativo `Status`; el campo `Estado TFM` queda como legado eliminable por el script de bootstrap.
- Decisión: cada tarea declara `fecha_inicio` y `fecha_fin` en `scripts/planning/github_project_mvp.json` para alimentar vistas de roadmap/Gantt reproducibles.
- Evidencia: `scripts/planning/github_project_mvp.json`, `scripts/planning/bootstrap_github_project.py`, `docs/github_projects_mvp.md`.

### 13. Nomenclatura y estructura estable del repositorio

- Justificación: en esta fase conviene maximizar legibilidad sin introducir cambios de rutas que rompan comandos, imports, tests o documentación ya consolidada.
- Decisión: se mantienen como canónicos los nombres técnicos `om_dcat_sync`, `tfm_ingestor`, `workflow`, `runtime`, `governance`, `mapping`, `export` y los YAML actuales porque encajan con Python, OpenMetadata, DCAT y el ecosistema de despliegue.
- Decisión: la documentación, los textos de app y la explicación de carpetas se redactan en español; los nombres físicos se traducen solo cuando no forman parte de un contrato técnico.
- Decisión: no se crean directorios paralelos en español para código o configuración, porque duplicarían fuentes de verdad. La claridad se resuelve con `docs/estructura_repositorio.md`.
- Evidencia: `docs/estructura_repositorio.md`, `README.md`, `.gitignore`.

## Trazabilidad con la ficha oficial

La ficha oficial completa se consulta en `docs/tfe_ficha_oficial_uclm.txt`. Esta tabla no reescribe sus objetivos; solo enlaza cada objetivo parcial con la evidencia de implementación.

| Objetivo parcial | Evidencia principal |
| --- | --- |
| 1 | `docs/dcat_mapping.md`, `docs/tfm_oficial_objetivos_decisiones.md` |
| 2 | `docs/dcat_mapping.md` |
| 3 | `docs/custom_properties_openmetadata.md`, `scripts/infra/bootstrap_governance.py` |
| 4 | `tfm_ingestor/src/tfm_ingestor/harvest_ckan.py`, `tfm_ingestor/config/ckan_harvest.yaml` |
| 5 | `tfm_ingestor/src/tfm_ingestor/dcat_export.py`, `tfm_ingestor/src/tfm_ingestor/shacl_validation.py` |
| 6 | `docs/tfm_oficial_objetivos_decisiones.md`, `docs/dcat_mapping.md`, `docs/gobierno_funcional_gold.md` |

## Riesgos y limitaciones asumidos

- `Dataset` DCAT no equivale exactamente a una tabla SQL.
- La clasificación HVD de la PoC es una hipótesis de demostración controlada.
- La PoC genera una única `Distribution` y un único `DataService` por dataset.
- El `DataService` exportado modela metadatos de acceso reproducibles de la PoC; no sustituye a una API productiva completa.
- La validación se centra en metadatos e interoperabilidad, no en profiling del contenido.
- La curación funcional depende de una hoja mantenida por una persona responsable del catálogo.
- La conformidad estricta sin `Warning` no es objetivo de esta iteración; el repositorio prioriza obligatorios y consistencia reproducible.

## Beneficios obtenidos en la PoC

- Un único workflow canónico sirve para operador técnico, ETL y app web.
- La app web operativa usa ese mismo workflow y scripts cerrados sin crear un núcleo paralelo.
- La validación queda versionada dentro del repositorio y deja artefactos reproducibles.
- El gobierno funcional se desacopla del código gracias a `gold_governance.csv`.
- La PoC mantiene un modelo OpenMetadata corto y defensible, derivando por configuración lo que no conviene gobernar manualmente.
- La estructura del repositorio queda documentada con nombres canónicos y distinción explícita entre rutas versionables, rutas locales y artefactos generados.
