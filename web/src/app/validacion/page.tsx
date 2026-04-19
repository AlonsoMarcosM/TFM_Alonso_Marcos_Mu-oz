import { ArtifactViewer } from "@/components/ArtifactViewer";
import { OperationGrid } from "@/components/OperationGrid";
import { operations } from "@/server/operations";

export default function ValidacionPage() {
  return (
    <div className="stack">
      <header>
        <h1 className="page-title">Validación</h1>
        <p className="lead">Ejecuta la suite completa o el script live DCAT y revisa los informes generados.</p>
      </header>
      <OperationGrid operations={operations.filter((operation) => ["run-validation-suite", "validate-live-dcat"].includes(operation.id))} />
      <ArtifactViewer initialPath="tmp_pytest/validation_suite_summary.json" />
    </div>
  );
}
