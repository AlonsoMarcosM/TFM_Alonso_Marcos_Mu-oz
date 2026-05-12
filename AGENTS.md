# AGENTS.md

Instrucciones para agentes Codex trabajando en este repositorio.

`CLAUDE.md` es el equivalente local para Claude Code y debe mantenerse coherente con este archivo. Si se cambia una regla aquí que aplique a cualquier agente, actualizar también `CLAUDE.md`.

## Objetivo

TFM de 6 ECTS. Prioridad absoluta: **simpleza**, coherencia y reproducibilidad.

Adicionalmente, para portfolio, intenta que todo lo que se haga sea **replicable** y fácilmente **desplegable en un VPS o cloud**. No es requisito imprescindible, pero guía las decisiones de arquitectura.

## Principios De Trabajo Del Agente

Estos principios se aplican antes de escribir código, documentación o automatizaciones. Si entran en conflicto con una petición explícita del usuario, se prioriza la petición del usuario y después la solución más simple que siga siendo correcta.

### 1. Pensar Antes De Codificar

- No asumir requisitos silenciosamente.
- Explicitar supuestos cuando afecten al diseño, la arquitectura o el alcance.
- Si hay varias interpretaciones razonables, exponerlas brevemente antes de elegir una.
- Si algo importante no está claro y la ambigüedad cambia la solución, parar y preguntar.
- Si existe una vía más simple que cumple el objetivo, preferirla y decirlo.

### 2. Simpleza Primero

- Implementar el mínimo cambio que resuelva el problema.
- No añadir funcionalidades, abstracciones o configurabilidad no pedidas.
- Evitar “future-proofing” especulativo.
- Evitar manejo de errores para escenarios imposibles o irrelevantes para este TFM.
- Si una solución crece demasiado para el valor que aporta, simplificarla.

### 3. Edición Quirúrgica

- Tocar solo los archivos y líneas necesarios para la petición.
- No refactorizar código adyacente por iniciativa propia.
- Respetar el estilo y patrones ya presentes en el repositorio.
- Si se detecta deuda técnica no relacionada, mencionarla, pero no mezclarla en el mismo cambio.
- Limpiar únicamente los restos generados por el propio cambio, como imports, variables o funciones que queden sin uso.

Prueba rápida de calidad del diff: **cada línea modificada debe poder trazarse directamente a la petición actual o a una consecuencia técnica necesaria de esa petición**.

### 4. Ejecución Guiada Por Objetivos

Antes de empezar una tarea no trivial, traducirla a un objetivo verificable.

Ejemplos:

- “Corregir un bug” -> reproducirlo o aislarlo, aplicar el cambio, verificar que deja de ocurrir.
- “Añadir validación” -> escribir o ajustar tests para entradas inválidas y hacerlos pasar.
- “Refactorizar” -> mantener comportamiento verificable antes y después.

Para tareas de varios pasos, trabajar con esta secuencia:

1. Definir el objetivo y el criterio de éxito.
2. Aplicar el cambio mínimo necesario.
3. Verificar con tests, comandos o comprobaciones concretas.

No dar una tarea por terminada con criterios vagos como “parece funcionar”.

## Terminología Canónica

- El nombre funcional del software desarrollado en este TFM es **Plataforma de Gobierno del Dato**.
- La prueba ejecutada ante el tribunal y documentada en la memoria debe denominarse **caso de uso de validación**.
- Evitar `PoC`, `MVP` y `demo` en documentación, interfaz, configuración y textos de apoyo del proyecto.
- Solo se admiten `PoC`, `MVP` o `demo` cuando formen parte de un identificador técnico heredado, una URL literal, un nombre de servicio ya consolidado o una referencia externa que no convenga romper sin necesidad.

## Redacción Y Codificación De Documentación

- En archivos `.md`: usar **UTF-8** siempre.
- Redactar en español correcto, con tildes y `ñ` cuando corresponda.
- Evitar caracteres corruptos, como signos de interrogación o secuencias mojibake dentro de palabras.
- No modificar texto dentro de bloques de código, comandos o URLs al corregir redacción.
- La ficha oficial UCLM del TFE está congelada en `docs/tfe_ficha_oficial_uclm.txt`; no modificarla ni resumirla dentro de ese archivo.
- Las decisiones de alcance, riesgos o cambios durante la implementación deben ir en `docs/tfm_oficial_objetivos_decisiones.md`.
- La memoria debe justificar el cambio de alcance del objetivo de harvesting desde CKAN: CKAN se trata como catálogo de publicación e intercambio de metadatos, no como fuente técnica adecuada para generar gobierno operativo en OpenMetadata.
- Al redactar la memoria, usar argumentos DAMA siempre que ayuden: gobierno de datos, gestión de metadatos, linaje, propiedad, calidad, trazabilidad, separación entre datos y metadatos, y generación de metadatos desde sistemas fuente.
- No presentar CKAN como origen canónico, fuente externa activa ni vía operativa principal del TFM. La fuente técnica canónica del caso de uso de validación es PostgreSQL de referencia con varias tablas `gold` gobernadas en OpenMetadata.
- Si se altera accidentalmente la ficha oficial, debe restaurarse el contenido literal y pasar el test de integridad `test_official_tfe_file_is_unchanged`.

## Principios De Arquitectura

- Infra declarativa y portable:
  - Kubernetes + Helm como vía canónica para OpenMetadata.
  - PostgreSQL dummy dentro del mismo cluster Kubernetes.
- Config por YAML/env vars, sin hardcode:
  - URLs, tokens y credenciales deben ir por variables de entorno o secretos.
- Idempotencia:
  - Los scripts deben poder ejecutarse múltiples veces sin duplicar tags, owners, issues, Project items ni asignaciones.
- Evidencias reproducibles:
  - Comandos copy/paste en `docs/`.
  - Tests mínimos para reglas, mapeo y configuración.
- Origen canónico de metadatos:
  - El caso de uso de validación gobierna metadatos generados a partir de activos técnicos reales en OpenMetadata.
  - PostgreSQL de referencia es la fuente técnica reproducible para demostrar descubrimiento, gobierno, exportación DCAT-AP-ES y validación.
  - CKAN queda descartado como origen operativo porque cosechar un catálogo externo solo replica metadatos ya publicados y no demuestra adecuadamente gobierno, linaje técnico ni generación de metadatos desde sistemas fuente.
- Núcleo único de lógica:
  - Toda regla de gobierno vive en la capa de servicios Python (`workflow_service.py`, `governance_service.py`, `governance_sheet.py`, `dcat_export.py`).
  - El CLI `om_dcat_sync`, los scripts PowerShell y la app web son envoltorios finos que invocan ese núcleo. No duplican reglas.

## App Web Operativa

- Ruta: `web/` (Next.js + React + TypeScript).
- Rol: consola que ejecuta una lista cerrada de operaciones versionadas y muestra resultados, logs y artefactos. No habla con OpenMetadata directamente; lanza el CLI canónico o scripts.
- Pantallas canónicas: `Infraestructura`, `Ingesta`, `Preparación`, `Gobierno`, `Workflow`, `DCAT`, `Runtime`, `SHACL`, `Validación`, `Artefactos`, `Ejecuciones`.
- Cada ejecución persiste un job en `state/web_jobs/` con estado, mensaje, código de salida, duración y resumen JSON.
- La pantalla `Gobierno` edita el mismo `tfm_ingestor/config/gold_governance.csv` que consume el workflow Python; no existen vías paralelas de edición.
- Reglas duras: no añadir lógica de negocio en TypeScript, no exponer comandos arbitrarios, no pedir tokens en formularios, no implementar login.

## GitHub Y Credenciales

- Nunca pedir al usuario su contraseña de GitHub.
- Nunca escribir tokens en archivos del repo, documentación, logs permanentes o commits.
- No usar nombres de agentes, bots ni líneas `Co-authored-by` de agentes en commits, PRs o contribuciones. GitHub debe reflejar solo la identidad Git configurada del proyecto/VS Code para `alonso.marcos@alu.uclm.es`.
- Para operar contra GitHub usar únicamente variables de entorno: `GITHUB_TOKEN` o `GH_TOKEN`.
- Se aceptan tres modos: token temporal definido por el usuario en la sesión actual, token persistente definido por el usuario como variable de entorno de Windows a nivel `User`, o `.env` local cargado con `scripts/load_env.ps1`.
- Si el token persistente existe en el ordenador, Codex puede usarlo de forma autónoma en futuras sesiones sin volver a pedirlo.
- `.env` está ignorado por Git; `.env.example` es la plantilla versionable.
- `scripts/planning/bootstrap_github_project.py` carga `.env` automáticamente y, si no hay token en variables de entorno, intenta usar `gh auth token`.
- Si no existe token en el entorno, no intentar actualizar GitHub: explicar el comando necesario y ejecutar solo `dry-run`.
- Para sincronizar el Project real del TFM usar:

```powershell
python .\scripts\planning\bootstrap_github_project.py --apply --project-number 6
```

- El tablero canónico es `https://github.com/users/AlonsoMarcosM/projects/6`.
- La configuración local canónica del roadmap es `scripts/planning/github_project_planificacion.json`.
- El script `scripts/planning/bootstrap_github_project.py` es idempotente y puede crear o actualizar labels, milestones, issues, Project items y campos del Project.

## No Objetivos

- Alta disponibilidad.
- Hardening avanzado.
- NetworkPolicies.
- SSO/LDAP.
- RBAC avanzado.
- Cifrado avanzado.
- Backups productivos.
- Escalado.
- Observabilidad avanzada.
- Harvesting CKAN como flujo operativo activo.

## Higiene Git

- Nunca subir carpetas locales no publicables.
- Antes de cualquier `push`: ejecutar `pytest` y revisar `git status --ignored`.
- No revertir cambios de usuario sin autorización explícita.
