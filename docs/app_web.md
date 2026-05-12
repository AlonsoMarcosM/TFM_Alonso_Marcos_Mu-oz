# App web operativa de la plataforma

## Propósito

La app web es una consola simple para operar la **Plataforma de Gobierno del Dato** sin memorizar comandos. Su usuario principal es un operario de negocio o una persona responsable del catálogo que necesita ejecutar el caso de uso de validación, revisar metadatos, lanzar el flujo completo y consultar evidencias.

La app no sustituye al núcleo Python ni a los scripts versionados. Ejecuta una lista cerrada de operaciones ya disponibles en el repositorio, muestra logs y artefactos, y edita únicamente las fuentes funcionales controladas.

La ruta física `web/` se mantiene por convención del ecosistema Node/Next.js. En la documentación se denomina consola web operativa.

## Proceso completo para operador de negocio

El flujo se entiende de izquierda a derecha: primero se conectan activos técnicos a OpenMetadata, después se completan metadatos de gobierno y finalmente se exporta un catálogo RDF serializado en JSON-LD conforme a `DCAT-AP-ES`.

| Pantalla | Acción del operario | Qué ejecuta por detrás | Resultado visible | Utilidad de negocio |
| --- | --- | --- | --- | --- |
| `Infraestructura` | Comprobar prerequisitos o recrear la plataforma limpia. | Scripts PowerShell de `scripts/infra/` para Kind, Helm, OpenMetadata y PostgreSQL de referencia. | Job con log, duración y estado. | Asegura un entorno reproducible antes de gobernar metadatos. |
| `Ingesta` | Ingestar PostgreSQL de referencia y preparar tags/custom properties. | Metadata ingest oficial de OpenMetadata y bootstrap de gobierno. | Servicio, base de datos, esquemas, tablas y propiedades disponibles en OpenMetadata. | Convierte servicios conectados en activos catalogables y gobernables. |
| `Gobierno` | Revisar o editar la hoja `gold_governance.csv`. | API interna Next.js que lee/escribe el CSV; validación autoritativa en Python. | Tabla editable, validación y mensajes de campos obligatorios. | Permite definir título, descripción, publicador, temática, HVD y URL de acceso sin tocar código. |
| `Workflow` | Ejecutar `Dry-run` y después `Aplicar workflow`. | `python -m om_dcat_sync workflow run`. | Plan reproducible, cambios aplicados, catálogo exportado e informe SHACL. | Sincroniza OpenMetadata con el contrato funcional y genera el catálogo UCLM gobernado. |
| `DCAT` | Repetir exportación o validación del catálogo. | `export-dcat` y `validate-dcat --profile-case hvd`. | `web_catalog.jsonld` y `web_shacl_report.ttl`. | Comprueba interoperabilidad con `DCAT-AP-ES` y preparación para federación. |
| `Estado vivo` | Validar OpenMetadata frente al contrato esperado. | `validate-runtime --strict`. | Informe JSON de estado técnico y de gobierno. | Detecta drift entre OpenMetadata, SQL de referencia y hoja funcional. |
| `Validación` | Ejecutar suite completa o validación live DCAT. | `run_validation_suite.ps1` o `validate_live_dcat.ps1`. | Resumen de conformidad, catálogo JSON-LD e informe SHACL. | Deja evidencia reproducible para memoria, defensa y operación. |
| `Artefactos` / `Ejecuciones` | Revisar ficheros y jobs generados. | Lectura segura de `tmp_pytest/` y `state/web_jobs/`. | Vista previa de JSON, JSON-LD, TTL, YAML o CSV. | Permite auditar qué se ejecutó y qué evidencias produjo. |

## Backend, frontend y núcleo de negocio

La app web está construida con `Next.js + React + TypeScript`, pero no contiene reglas de gobierno. Su backend interno crea jobs y lanza procesos cerrados definidos en `web/src/server/operations.ts`.

Esos jobs invocan:

- scripts PowerShell para infraestructura, ingesta y validación de entorno;
- el CLI `python -m om_dcat_sync` para gobierno, exportación DCAT y validación;
- el mismo núcleo Python que usan los comandos manuales: `workflow_service.py`, `governance_service.py`, `governance_sheet.py`, `dcat_export.py` y `shacl_validation.py`.

No existe endpoint para ejecutar comandos arbitrarios. La web tampoco habla directamente con OpenMetadata: los scripts y el CLI son los responsables de usar la API de OpenMetadata.

## Catálogo UCLM y gobierno DCAT-AP-ES

Cada servicio conectado a OpenMetadata aporta activos técnicos al catálogo de la plataforma. En el caso de uso de validación, el servicio principal es PostgreSQL de referencia con esquemas `bronze`, `silver` y `gold`.

La capa `gold` se trata como el conjunto de datasets publicables. La pantalla `Gobierno` trabaja sobre `tfm_ingestor/config/gold_governance.csv`, que contiene la curación funcional por dataset:

- `publicar`;
- `titulo_dataset`;
- `descripcion_dataset`;
- `publicador`;
- `tematica_dcat`;
- `categoria_hvd`;
- `access_url_distribucion`.

El fichero `tfm_ingestor/config/governance_defaults.yaml` fija las propiedades globales del catálogo UCLM: publicador, URI de organismo, página principal, licencia, idioma, taxonomía temática, legislación HVD, contacto y URLs base de servicio. Con esa combinación se genera un catálogo RDF serializado en JSON-LD validable frente a `DCAT-AP-ES` y preparado para publicación o federación hacia `datos.gob.es` y ecosistemas europeos compatibles.

La plataforma no publica automáticamente en un CKAN externo ni certifica aceptación por un portal externo en esta iteración. La salida queda preparada y validada para ese tipo de integración.

## Gobierno gold y HVD

El campo `publicar` significa:

- `si`: la tabla `gold` entra en el catálogo DCAT exportado como dataset publicable de la plataforma;
- `no`: la fila puede existir como referencia, pero no entra en el contrato publicable ni se le exigen los obligatorios funcionales.

La hoja cubre los campos funcionales por dataset. El resto de obligatorios HVD se deriva desde `governance_defaults.yaml` y `dcat_export.py`: catálogo, legislación aplicable, licencias, `DataService`, `contactPoint`, documentación y vínculos `accessService` / `servesDataset`.

En la web, `tematica_dcat` y `categoria_hvd` se editan mediante listas cerradas:

- `tematica_dcat`: sectores NTI-RISP enumerados en las SHACL locales congeladas, por ejemplo `transporte`, `cultura_ocio`, `medio_ambiente` o `sector_publico`;
- `categoria_hvd`: categorías superiores del vocabulario europeo HVD, como `movilidad`, `estadisticas` o `geoespacial`.

La app muestra ayuda de rellenado junto a la tabla y ofrece un botón `Autorrellenar vacíos`. Ese botón solo completa campos vacíos con valores de validación; no sobreescribe lo que el operador ya haya escrito.

La formulación correcta para defensa es: la hoja no es todo `DCAT-AP-ES HVD`; es el contrato funcional por dataset. El sistema completo, formado por hoja, configuración global, OpenMetadata, exportador y validación SHACL, cubre el perfil activo de la plataforma.

## Preparación del caso de uso de validación

Antes de abrir la app, la infraestructura debe estar levantada. Si `OPENMETADATA_BASE_URL` apunta a `localhost`, deja activo el port-forward para que los comandos Python directos puedan hablar con OpenMetadata. La ingesta técnica puede lanzarse desde la pantalla `Ingesta`.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\launch_infra.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\infra\port_forward_openmetadata.ps1
```

El fichero `.env` del root debe existir y contener las variables necesarias. La app acepta `OPENMETADATA_JWT_TOKEN` o `OPENMETADATA_TOKEN`; si existe solo `OPENMETADATA_TOKEN`, lo pasa al CLI como `OPENMETADATA_JWT_TOKEN` en memoria. Si no hay token, intenta usar el generador existente `scripts/infra/generate_om_jwt.py` para el job en curso. No escribe ni muestra el token.

## Arranque local

```powershell
cd .\web
npm install
npm run dev
```

Abrir `http://localhost:3000`.

Tests de la app:

```powershell
npm test
```

## Flujo operativo recomendado

1. Abrir `Infraestructura` y ejecutar `Comprobar prerrequisitos`.
2. Si se quiere partir de cero, ejecutar `Reset limpio y recrear la plataforma`.
3. Abrir `Ingesta` y ejecutar `Ingestar PostgreSQL de referencia`.
4. Ejecutar `Preparar tags y custom properties`.
5. Abrir `Gobierno` y ejecutar `Refrescar hoja gold desde OpenMetadata`.
6. Revisar o editar datasets `gold`, usar `Autorrellenar vacíos` si procede y guardar.
7. Ejecutar `Validar hoja gold`.
8. Abrir `Workflow` y ejecutar `Dry-run del workflow`.
9. Ejecutar `Aplicar workflow`.
10. Abrir `DCAT`, `Estado vivo` y `Validación` para repetir validaciones o generar evidencias independientes.
11. Abrir `Artefactos` y `Ejecuciones` para revisar JSON, JSON-LD, TTL, logs y resumen de jobs.

## Resultado visible por ejecución

Cada botón `Ejecutar` crea un job persistido en `state/web_jobs/`. Al terminar, la web muestra una respuesta de resultado junto al log:

- estado final en español: `correcto` o `error`;
- mensaje explícito de éxito o fallo;
- resumen de la salida JSON del comando cuando el script o CLI devuelve JSON;
- duración y código de salida;
- número de artefactos esperados y generados;
- resumen de cada artefacto generado;
- vista previa corta de JSON, JSON-LD, TTL, YAML y CSV;
- enlace a la pantalla `Artefactos` cuando el fichero forma parte de la lista segura de evidencias consultables.

Esto cubre tanto operaciones de CLI Python como scripts PowerShell. Si un script no genera un artefacto persistente, la web sigue dejando evidencia visible mediante el estado, el mensaje final, la duración, el código de salida y el log completo.

## Comandos equivalentes

La UI ejecuta una lista cerrada de comandos:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\check_prereqs.ps1 -Strict
powershell -ExecutionPolicy Bypass -File .\scripts\infra\status_infra.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\infra\backup_openmetadata_state.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\infra\restore_openmetadata_state.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\infra\deploy_postgres_k8s.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\infra\launch_infra.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\infra\delete_cluster_preserve_state.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\infra\reset_platform_clean.ps1 -RunFullFlow -SkipPipInstall
powershell -ExecutionPolicy Bypass -File .\scripts\infra\run_full_flow.ps1 -SkipPipInstall
python -m om_dcat_sync validate-governance-sheet --sheet .\tfm_ingestor\config\gold_governance.csv
powershell -ExecutionPolicy Bypass -File .\scripts\infra\clear_openmetadata_postgres_source.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\infra\ingest_postgres.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\infra\bootstrap_governance_from_env.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\infra\refresh_governance_sheet_from_env.ps1 -SkipPipInstall
python -m om_dcat_sync workflow run --skip-export --skip-validate
python -m om_dcat_sync workflow run --dry-run --plan-output .\tmp_pytest\web_workflow_plan.json
python -m om_dcat_sync workflow run --allow-warnings --export-output .\tmp_pytest\web_catalog.jsonld --report-output .\tmp_pytest\web_shacl_report.ttl
python -m om_dcat_sync export-dcat --output .\tmp_pytest\web_catalog.jsonld
python -m om_dcat_sync validate-dcat --input .\tmp_pytest\web_catalog.jsonld --profile-case hvd --allow-warnings --report-output .\tmp_pytest\web_shacl_report.ttl
python -m om_dcat_sync validate-runtime --strict --output .\tmp_pytest\web_runtime_report.json
powershell -ExecutionPolicy Bypass -File .\scripts\infra\run_validation_suite.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\infra\validate_live_dcat.ps1
```

`port_forward_openmetadata.ps1` no se expone como job normal porque es un proceso persistente. La app abre port-forward temporal dentro de los scripts que lo necesitan y el comando manual sigue documentado en `Preparación`.

## Artefactos principales

- `tmp_pytest/web_workflow_plan.json`
- `tmp_pytest/web_catalog.jsonld`
- `tmp_pytest/web_shacl_report.ttl`
- `tmp_pytest/web_runtime_report.json`
- `tmp_pytest/prereqs_report.json`
- `tmp_pytest/live_dcat_catalog.jsonld`
- `tmp_pytest/live_dcat_validation_report.ttl`
- `tmp_pytest/validation_suite_summary.json`
- `tmp_pytest/validation_suite_catalog.jsonld`
- `tmp_pytest/validation_suite_shacl_report.ttl`
- `tmp_pytest/workflow_first_plan.json`
- `tmp_pytest/workflow_second_plan.json`

## Despliegue básico

La ruta recomendada para el caso de uso de validación es local con `npm run dev`. Se incluye `web/Dockerfile` como base para VPS o contenedor controlador, asumiendo que el repositorio completo se monta o copia en `/workspace` y que la infraestructura ya está disponible.

## Trabajo futuro

- Ejecutar el workflow con Airflow u otro planificador para exportar periódicamente el catálogo y subirlo a un CKAN externo cuando exista un portal de publicación real.
- Enviar por correo el informe de validación RDF/SHACL a responsables de catálogo.
- Generar informes presentables en PDF o HTML además de JSON y TTL.
- Añadir autenticación, permisos y auditoría avanzada si la app pasa de consola local a herramienta multiusuario.
