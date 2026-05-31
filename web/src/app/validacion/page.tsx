import { ArtifactViewer } from "@/components/ArtifactViewer";
import { OperationGrid } from "@/components/OperationGrid";
import { operations } from "@/server/operations";

export default function ValidacionPage() {
  return (
    <div className="stack">
      <header>
        <h1 className="page-title">Validación</h1>
        <p className="lead">
          Ejecuta la suite completa o el script live DCAT y revisa los informes generados para cerrar evidencias del
          caso de uso de validación.
        </p>
      </header>
      <section className="panel">
        <h2>Evidencia final</h2>
        <p className="muted">
          La suite comprueba estado vivo, idempotencia, exportación JSON-LD, validación SHACL y tests. Los artefactos
          sirven para justificar que el catálogo gobernado es reproducible y validable.
        </p>
      </section>
      <OperationGrid operations={operations.filter((operation) => ["run-validation-suite", "render-validation-report", "validate-live-dcat"].includes(operation.id))} />
      <ArtifactViewer initialPath="tmp_pytest/validation_suite_summary.json" />
    </div>
  );
}
