import { ArtifactViewer } from "@/components/ArtifactViewer";
import { OperationGrid } from "@/components/OperationGrid";
import { operations } from "@/server/operations";

export default function RuntimePage() {
  return (
    <div className="stack">
      <header>
        <h1 className="page-title">Estado vivo</h1>
        <p className="lead">
          Valida el estado técnico y de gobierno contra el contrato de referencia: SQL reproducible, hoja gold y
          metadatos aplicados en OpenMetadata.
        </p>
      </header>
      <section className="panel">
        <h2>Qué comprueba</h2>
        <p className="muted">
          Detecta si faltan servicios, esquemas, tablas, columnas o metadatos de gobierno esperados. Es la comprobación
          de que el catálogo vivo coincide con lo que documenta el caso de uso.
        </p>
      </section>
      <OperationGrid operations={operations.filter((operation) => operation.id === "validate-runtime")} />
      <ArtifactViewer initialPath="tmp_pytest/web_runtime_report.json" />
    </div>
  );
}
