# Despliegue local de OpenMetadata en Kubernetes

Objetivo: levantar OpenMetadata en Kubernetes local de la forma más simple posible para una plataforma de TFM, manteniendo una ruta razonablemente portable hacia un VPS o cloud.

Este documento también sirve como explicación de infraestructura para defensa, memoria y portfolio. Está escrito pensando en una persona que llega al repositorio sin experiencia previa en DevOps.

## Idea principal

La infraestructura no es un único contenedor Docker con todo dentro. Son varias capas:

```text
Windows + repositorio
  |
  | comandos: docker, kind, kubectl, helm, python
  v
Docker Desktop
  |
  | ejecuta un contenedor especial creado por kind
  v
Nodo Kubernetes local: tfm-om-control-plane
  |
  | dentro vive el clúster Kubernetes
  v
Pods de Kubernetes
  |
  | openmetadata, mysql, opensearch, postgres-demo
  v
Aplicación y flujo del TFM
```

Traducción sencilla:

- Docker pone la "máquina" local.
- Kind crea un Kubernetes pequeño dentro de Docker.
- Kubernetes ejecuta los componentes como pods.
- Helm instala OpenMetadata y sus dependencias en Kubernetes.
- El repositorio contiene los scripts y YAML para repetir el despliegue.

## Qué es cada pieza

### Docker Desktop

Docker Desktop es la base local. Permite ejecutar contenedores en el portátil.

En este proyecto Docker no ejecuta directamente todos los servicios de la plataforma, como ocurriría con un `docker-compose.yml`. Aquí Docker ejecuta principalmente el nodo de Kind.

Comprobación:

```powershell
docker ps
```

Salida esperada aproximada:

```text
tfm-om-control-plane   kindest/node:...   Up ...
```

Ese contenedor es el nodo local de Kubernetes.

### Kind

Kind significa `Kubernetes in Docker`.

Sirve para crear un clúster Kubernetes local sin tener que contratar cloud, instalar servidores ni preparar una infraestructura compleja. Es una opción adecuada para este TFM porque:

- es simple;
- es reproducible;
- usa Kubernetes real;
- evita depender de un proveedor cloud concreto;
- se puede borrar y recrear rápido;
- permite probar Helm igual que en un entorno más profesional.

En este repositorio el clúster se llama:

```text
tfm-om
```

El contexto de `kubectl` queda como:

```text
kind-tfm-om
```

Comprobación:

```powershell
kubectl config current-context
kubectl get nodes
```

### Kubernetes

Kubernetes es el orquestador. Su trabajo es ejecutar y conectar servicios.

En vez de pensar en "programas abiertos", aquí se piensa en objetos:

- `Pod`: una unidad en ejecución. Normalmente contiene uno o varios contenedores.
- `Deployment`: regla para mantener uno o varios pods funcionando.
- `StatefulSet`: parecido a un Deployment, pero pensado para servicios con estado, como bases de datos.
- `Service`: nombre estable para acceder a un pod dentro del clúster.
- `Secret`: credenciales o claves.
- `ConfigMap`: configuración no secreta.

Comandos útiles:

```powershell
kubectl get pods
kubectl get svc
kubectl get deployments,statefulsets
kubectl get secrets
kubectl get configmaps
```

### Helm

Helm es el instalador de aplicaciones para Kubernetes.

No hay que entenderlo como un servicio que se queda corriendo dentro del clúster. Helm se ejecuta desde el portátil, lee una receta de instalación llamada `chart` y crea objetos dentro de Kubernetes.

En este proyecto se usan dos releases Helm:

```text
openmetadata-dependencies
openmetadata
```

`openmetadata-dependencies` instala dependencias de OpenMetadata, principalmente:

- MySQL;
- OpenSearch.

`openmetadata` instala la aplicación principal OpenMetadata.

Comprobación:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\helm.ps1 ls -A
```

## Stack desplegado

El stack final esperado dentro del clúster local es:

```text
openmetadata
mysql
opensearch
postgres-demo
```

### OpenMetadata

Es la aplicación principal del TFM. Proporciona:

- interfaz web;
- API REST;
- catálogo de metadatos;
- entidades técnicas como servicios, bases de datos, esquemas, tablas y columnas;
- tags y custom properties usados para el modelo DCAT-AP-ES.

Acceso local:

```text
http://localhost:8585
```

Credenciales de referencia:

```text
admin@open-metadata.org / admin
```

### MySQL

MySQL es la base de datos interna de OpenMetadata.

Guarda el estado funcional de OpenMetadata:

- usuarios;
- servicios registrados;
- tablas ingeridas;
- tags;
- custom properties;
- descripciones;
- owners;
- metadatos enriquecidos.

No debe confundirse con el PostgreSQL de referencia.

### OpenSearch

OpenSearch es el motor de búsqueda usado por OpenMetadata.

OpenMetadata guarda su estado en MySQL, pero usa OpenSearch para buscar entidades de forma eficiente en la interfaz y en algunas operaciones internas.

### PostgreSQL de referencia

`postgres-demo` es una base de datos de referencia creada por el repositorio.

Su función es actuar como fuente técnica de datos para la plataforma. OpenMetadata la ingiere como si fuera una fuente real.

El SQL inicial está en:

```text
sql/opendata_demo_init.sql
```

El despliegue está automatizado en:

```text
scripts/infra/deploy_postgres_k8s.ps1
```

Resumen conceptual:

```text
PostgreSQL de referencia = fuente de datos que se cataloga
OpenMetadata = catálogo donde se registran los metadatos
MySQL = base interna de OpenMetadata
OpenSearch = buscador interno de OpenMetadata
```

## Qué hace el script de infraestructura

Comando recomendado:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\launch_infra.ps1
```

Este script hace lo siguiente:

1. Comprueba comandos necesarios: `docker`, `kubectl`, `kind` y Helm 3.
2. Crea o reutiliza el clúster Kind `tfm-om`.
3. Cambia el contexto activo de `kubectl` a `kind-tfm-om`.
4. Despliega `postgres-demo` dentro de Kubernetes.
5. Crea secretos mínimos para OpenMetadata.
6. Instala `openmetadata-dependencies` con Helm.
7. Restaura el snapshot local de MySQL si existe.
8. Instala `openmetadata` con Helm.
9. Muestra el estado de los pods.

Valores locales usados por Helm:

```text
k8s/openmetadata-dependencies.values.yaml
k8s/openmetadata.values.yaml
```

## Por qué Kind y no otro clúster

Para este TFM, Kind es una decisión pragmática.

El objetivo no es cubrir alta disponibilidad ni operación avanzada de plataforma. El objetivo es evidenciar un flujo reproducible de metadatos con OpenMetadata, PostgreSQL, DCAT-AP-ES y validación SHACL.

Kind encaja porque permite usar Kubernetes y Helm sin añadir coste ni complejidad innecesaria.

Alternativas posibles:

- Docker Compose: más simple, pero no cubre Kubernetes + Helm.
- Kubernetes de Docker Desktop: válido, pero menos portable como receta explícita del repo.
- Minikube: también válido, parecido a Kind, aunque suele añadir más superficie de configuración.
- k3s en VPS: buena evolución si se quiere desplegar fuera del portátil.
- Clúster gestionado cloud: opción habitual en empresas, pero excesiva para una plataforma de 6 ECTS.

## Cómo lo haría una empresa

En una empresa normalmente no se ejecutaría OpenMetadata en Kind en un portátil como entorno principal.

Lo habitual sería:

- un clúster Kubernetes gestionado, por ejemplo AKS, EKS, GKE u OpenShift;
- o un Kubernetes ligero en servidores propios, por ejemplo k3s o RKE2;
- despliegues con Helm, GitOps o pipelines CI/CD;
- secretos gestionados por una herramienta corporativa;
- almacenamiento persistente real;
- backups;
- monitorización;
- ingress corporativo;
- control de acceso y autenticación integrada.

La plataforma de este repositorio conserva la parte transferible:

- Kubernetes como plataforma;
- Helm como mecanismo de despliegue;
- configuración por YAML;
- scripts reproducibles;
- separación entre aplicación, dependencias y fuente de referencia;
- evidencias ejecutables.

Lo que no se incluye por alcance del TFM:

- alta disponibilidad;
- hardening avanzado;
- NetworkPolicies;
- SSO/LDAP;
- RBAC avanzado;
- backups productivos;
- observabilidad avanzada;
- escalado.

## Trabajo futuro de contenerización

La plataforma actual no necesita un `Dockerfile` propio porque no se construye una imagen personalizada. Kind utiliza la imagen estándar `kindest/node` para crear el nodo Kubernetes local, y OpenMetadata, MySQL y OpenSearch se despliegan desde charts Helm e imágenes ya existentes.

Como evolución futura, sí tendría sentido añadir contenerización propia en estos casos:

- crear una aplicación web propia para operar el flujo de gobierno desde navegador;
- empaquetar `om_dcat_sync` como imagen Docker;
- ejecutar `om_dcat_sync` como `Job` o `CronJob` de Kubernetes;
- incluir scripts y dependencias del TFM en una imagen versionada;
- ejecutar el workflow completo dentro del clúster en vez de lanzarlo desde el portátil;
- preparar un despliegue más cercano a VPS/cloud o CI/CD.

Esta evolución permitiría que el flujo operativo fuese más autónomo: el clúster no solo tendría OpenMetadata y sus dependencias, sino también el proceso de sincronización, exportación y validación ejecutándose como carga de trabajo Kubernetes.

## Cómo replicarlo en otro portátil

Caso esperado: copiar o clonar el repositorio en otro portátil y recrear la infraestructura.

Pasos:

1. Instalar requisitos base:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\check_prereqs.ps1 -Strict
```

Si falta algo, instalar:

- Docker Desktop;
- `kubectl`;
- `kind`;
- Python 3.10+;
- Helm 3 opcional, porque el repo puede descargar una copia local.

2. Instalar dependencias Python:

```powershell
python -m pip install -r requirements-dev.txt
```

3. Levantar infraestructura:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\launch_infra.ps1
```

4. Abrir acceso local a OpenMetadata:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\port_forward_openmetadata.ps1
```

5. Entrar en:

```text
http://localhost:8585
```

6. Verificar estado:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\status_infra.ps1
```

## Persistencia portable del estado OpenMetadata

El estado funcional de OpenMetadata vive en MySQL. Si se borra el clúster Kind, ese estado puede perderse salvo que se exporte.

Para conservarlo dentro de la carpeta del proyecto:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\backup_openmetadata_state.ps1
```

Snapshot local:

```text
state/openmetadata/mysql/openmetadata_db.sql
```

Para borrar el clúster conservando el snapshot:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\delete_cluster_preserve_state.ps1
```

Al volver a ejecutar:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\launch_infra.ps1
```

el script restaura automáticamente el snapshot si existe.

## Exposición local de la UI

OpenMetadata está dentro de Kubernetes. Para verlo desde el navegador se usa un `port-forward`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\infra\port_forward_openmetadata.ps1
```

Esto conecta:

```text
localhost:8585 -> servicio openmetadata dentro de Kubernetes
```

## Comprobaciones rápidas

```powershell
kubectl get pods
kubectl get svc
kubectl logs deployment/openmetadata --tail=100
powershell -ExecutionPolicy Bypass -File .\scripts\infra\status_infra.ps1
```

## Frase útil para memoria o tribunal

La plataforma utiliza Kind para disponer de un clúster Kubernetes local, reproducible y de bajo coste. Sobre ese clúster se despliega OpenMetadata mediante Helm, junto con sus dependencias mínimas, MySQL y OpenSearch. Además, se despliega un PostgreSQL de referencia dentro del mismo clúster como fuente técnica de datos. Esta arquitectura no pretende cubrir requisitos productivos avanzados, sino evidenciar un flujo portable de despliegue, ingesta, gobierno de metadatos, exportación DCAT-AP-ES y validación SHACL.
