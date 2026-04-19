# App web operativa de la PoC

## Propósito

La app web es una consola simple para demostrar la PoC sin memorizar comandos. No sustituye al núcleo Python ni a los scripts versionados: ejecuta operaciones concretas ya disponibles en el repositorio y muestra logs, resultados, resúmenes y artefactos.

La ruta física `web/` se mantiene por convención del ecosistema Node/Next.js. En la documentación se denomina consola web operativa.

## Alcance

La app permite:

- comprobar prerrequisitos y estado de infraestructura;
- levantar infraestructura con los scripts canónicos;
- hacer backup/restore del estado OpenMetadata;
- resetear infraestructura conservando snapshot;
- resetear la PoC limpia y recrearla desde cero;
- ejecutar la ingesta técnica de PostgreSQL demo en OpenMetadata;
- preparar tags y custom properties de gobierno;
- editar `tfm_ingestor/config/gold_governance.csv`;
- validar la hoja gold;
- ejecutar dry-run del workflow;
- aplicar el workflow;
- exportar DCAT JSON-LD;
- validar DCAT con las SHACL locales congeladas;
- validar runtime;
- ejecutar la suite de validación;
- consultar artefactos de `tmp_pytest/`;
- consultar el manifiesto SHACL congelado.

Queda fuera de alcance:

- GitHub Project;
- login y permisos;
- pedir tokens en formularios;
- editar reglas YAML avanzadas;
- crear flujos dinámicos nuevos.

## Gobierno gold y HVD

La pantalla `Gobierno` trabaja sobre `tfm_ingestor/config/gold_governance.csv`.

El campo `publicar` significa:

- `si`: la tabla `gold` entra en el catálogo DCAT exportado como dataset publicable de la PoC;
- `no`: la fila puede existir como referencia, pero no entra en el contrato publicable ni se le exigen los obligatorios funcionales.

La hoja cubre los campos funcionales por dataset: título, descripción, publicador, temática, categoría HVD y URL de acceso. El resto de obligatorios HVD se deriva desde `governance_defaults.yaml` y `dcat_export.py`: catálogo, legislación aplicable, licencias, `DataService`, `contactPoint`, documentación y vínculos `accessService` / `servesDataset`.

En la web, `tematica_dcat` y `categoria_hvd` se editan mediante listas cerradas para evitar valores inválidos:

- `tematica_dcat`: los 22 sectores NTI-RISP enumerados en `tfm_ingestor/src/tfm_ingestor/resources/shacl/shacl_common_shapes.ttl`, por ejemplo `transporte`, `cultura_ocio`, `medio_ambiente` o `sector_publico`.
- `categoria_hvd`: las seis categorías superiores del vocabulario europeo HVD `http://data.europa.eu/bna/asd487ae75`: `geoespacial`, `observacion_de_la_tierra_y_medio_ambiente`, `meteorologia`, `estadisticas`, `sociedades_y_propiedad_de_sociedades` y `movilidad`.

La app muestra ayuda de rellenado junto a la tabla y ofrece un botón `Autorrellenar vacíos`. Ese botón solo completa campos vacíos con valores demo validables; no sobreescribe lo que el operador ya haya escrito.

La formulación correcta para defensa es: la hoja no es todo DCAT-AP-ES HVD; es el contrato funcional por dataset. El sistema completo, formado por hoja, configuración global, OpenMetadata, exportador y validación SHACL, cubre el perfil activo de la PoC.

## Preparación de demo

Antes de abrir la app, la infraestructura debe estar levantada. Si `OPENMETADATA_BASE_URL` apunta a `localhost`, deja activo el port-forward para que los comandos Python directos puedan hablar con OpenMetadata. La ingesta técnica puede lanzarse ya desde la pantalla `Ingesta`.

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

## Flujo de demostración

1. Abrir `Infraestructura` y ejecutar `Comprobar prerrequisitos`.
2. Para demo desde cero, ejecutar `Reset limpio y recrear PoC`.
3. Abrir `Ingesta`, ejecutar `Ingestar PostgreSQL demo` si se quiere repetir solo la ingesta técnica.
4. Ejecutar `Preparar tags y custom properties`.
5. Abrir `Gobierno`, revisar o editar los datasets gold.
6. Guardar la hoja y ejecutar `Validar hoja gold`.
7. Abrir `Workflow` y ejecutar `Dry-run`.
8. Ejecutar `Aplicar workflow`.
9. Abrir `DCAT`, exportar JSON-LD y validar DCAT.
10. Abrir `Estado vivo` y validar el estado runtime.
11. Abrir `Validación` y ejecutar la suite completa.
12. Abrir `Artefactos` para revisar JSON, JSON-LD y TTL generados.

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

Esto cubre tanto operaciones de CLI Python como scripts PowerShell. Si un script no genera un artefacto persistente, la web sigue dejando evidencia visible mediante el estado, el mensaje final, la duración, el código de salida y el log completo. Los scripts que producen evidencias de validación escriben además ficheros en `tmp_pytest/`.

Ejemplos de resúmenes mostrados:

- `workflow-dry-run`: tablas descubiertas, filas de hoja cargadas, validez de la hoja y cambios planificados.
- `workflow-apply`: cambios aplicados, datasets exportados y conformidad SHACL.
- `validate-runtime`: conformidad técnica y de gobierno del estado vivo.
- `run-validation-suite`: conformidad runtime, idempotencia, SHACL y pre-push checks.
- `ingest-postgres`: servicio usado, base de datos y tablas detectadas en OpenMetadata.

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
powershell -ExecutionPolicy Bypass -File .\scripts\infra\reset_poc_clean.ps1 -RunFullFlow -SkipPipInstall
powershell -ExecutionPolicy Bypass -File .\scripts\infra\run_full_flow.ps1 -SkipPipInstall
python -m om_dcat_sync validate-governance-sheet --sheet .\tfm_ingestor\config\gold_governance.csv
powershell -ExecutionPolicy Bypass -File .\scripts\infra\ingest_postgres.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\infra\bootstrap_governance_from_env.ps1
python -m om_dcat_sync workflow run --dry-run --plan-output .\tmp_pytest\web_workflow_plan.json
python -m om_dcat_sync workflow run --allow-warnings --export-output .\tmp_pytest\web_catalog.jsonld --report-output .\tmp_pytest\web_shacl_report.ttl
python -m om_dcat_sync export-dcat --output .\tmp_pytest\web_catalog.jsonld
python -m om_dcat_sync validate-dcat --input .\tmp_pytest\web_catalog.jsonld --profile-case hvd --allow-warnings --report-output .\tmp_pytest\web_shacl_report.ttl
python -m om_dcat_sync validate-runtime --strict --output .\tmp_pytest\web_runtime_report.json
powershell -ExecutionPolicy Bypass -File .\scripts\infra\run_validation_suite.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\infra\validate_live_dcat.ps1
```

`port_forward_openmetadata.ps1` no se expone como job normal porque es un proceso persistente. La app abre port-forward temporal dentro de los scripts que lo necesitan y el comando manual sigue documentado en `Preparación`.

No existe endpoint para ejecutar comandos arbitrarios.

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

La ruta recomendada para demo es local con `npm run dev`. Se incluye `web/Dockerfile` como base para VPS o contenedor controlador, asumiendo que el repositorio completo se monta o copia en `/workspace` y que la infraestructura ya está disponible.

## Trabajo futuro

- autenticación;
- multiusuario;
- GitHub Project;
- base de datos propia;
- edición avanzada de YAML;
- nuevos datasets dinámicos;
- auditoría avanzada.
