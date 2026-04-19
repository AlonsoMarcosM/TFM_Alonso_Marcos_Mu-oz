import { OperationGrid } from "@/components/OperationGrid";
import { operations } from "@/server/operations";

export default function WorkflowPage() {
  return (
    <div className="stack">
      <header>
        <h1 className="page-title">Workflow</h1>
        <p className="lead">Ejecuta el dry-run y aplica el gobierno usando el comando canónico del repo.</p>
      </header>
      <OperationGrid operations={operations.filter((operation) => ["workflow-dry-run", "workflow-apply"].includes(operation.id))} />
    </div>
  );
}
