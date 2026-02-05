# Diagramas Mermaid (memoria y portfolio)

Este documento centraliza diagramas Mermaid reutilizables en:
- README del repositorio
- anexos de memoria
- presentacion/defensa

## 1) Arquitectura general de la PoC

```mermaid
flowchart LR
  A[PostgreSQL dummy<br/>bronze/silver/gold] -->|Ingesta tecnica| B[OpenMetadata]
  B --> C[Entidades tecnicas<br/>Service/DB/Schema/Table/Column]
  D[tfm_ingestor<br/>Python API] -->|Enriquecimiento| B
  B --> E[Metadatos de gobierno<br/>tags + domains + custom properties]
```

## 2) Flujo operativo de extremo a extremo

```mermaid
sequenceDiagram
  autonumber
  participant U as Usuario
  participant S as Scripts infra
  participant K as Kubernetes
  participant OM as OpenMetadata
  participant PG as PostgreSQL
  participant GI as tfm_ingestor

  U->>S: run_full_flow.ps1
  S->>K: Helm upgrade/install
  S->>K: Deploy postgres-demo
  S->>OM: Crear/verificar DatabaseService
  S->>K: Ejecutar pod de metadata ingest
  K->>PG: Leer metadatos tecnicos
  K->>OM: Publicar entidades
  S->>OM: Crear tags/custom properties
  GI->>OM: --dry-run (plan de PATCH)
```

## 3) Stack de despliegue (local reproducible)

```mermaid
flowchart TB
  subgraph Host["Host Windows"]
    D[Docker Engine]
    C[Kind cluster]
  end

  subgraph K8s["Kubernetes namespace default"]
    PG[(postgres-demo)]
    OM[openmetadata]
    MY[mysql]
    OS[opensearch]
  end

  D --> C
  C --> K8s
  OM --> MY
  OM --> OS
  OM -. metadata ingest .-> PG
```

## 4) Mapeo simplificado DCAT-AP-ES -> OpenMetadata

```mermaid
flowchart LR
  DC1[DCAT Catalogo] --> OM1[Domain + Service + custom fields]
  DC2[DCAT Dataset] --> OM2[Table/View + description + tags]
  DC3[DCAT Distribucion] --> OM3[custom properties\naccessURL/downloadURL]
  DC4[DCAT DataService] --> OM4[custom property endpoint]
```

## Nota para memoria en LaTeX

LaTeX no renderiza Mermaid de forma nativa. Recomendacion:
1) mantener estos bloques como fuente documental,
2) exportar a SVG/PNG con `mmdc` para insertar en `main.tex`.
