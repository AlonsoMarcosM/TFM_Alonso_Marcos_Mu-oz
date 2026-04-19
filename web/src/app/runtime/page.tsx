import { ArtifactViewer } from "@/components/ArtifactViewer";
import { OperationGrid } from "@/components/OperationGrid";
import { operations } from "@/server/operations";

export default function RuntimePage() {
  return (
    <div className="stack">
      <header>
        <h1 className="page-title">Estado vivo</h1>
        <p className="lead">Valida el estado técnico y de gobierno contra el contrato de demo.</p>
      </header>
      <OperationGrid operations={operations.filter((operation) => operation.id === "validate-runtime")} />
      <ArtifactViewer initialPath="tmp_pytest/web_runtime_report.json" />
    </div>
  );
}
