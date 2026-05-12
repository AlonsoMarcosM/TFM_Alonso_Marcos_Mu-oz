import { OperationGrid } from "@/components/OperationGrid";
import { operations } from "@/server/operations";

export default function WorkflowPage() {
  return (
    <div className="stack">
      <header>
        <h1 className="page-title">Workflow</h1>
        <p className="lead">
          Ejecuta el dry-run y aplica el gobierno usando el comando canónico del repo. Es el paso que conecta hoja
          funcional, defaults globales, OpenMetadata, exportación DCAT y validación SHACL.
        </p>
      </header>
      <section className="grid">
        <article className="card">
          <h2>Dry-run</h2>
          <p className="muted">
            Genera un plan sin aplicar cambios. Sirve para revisar qué datasets se gobernarán y qué metadatos se
            sincronizarán antes de tocar OpenMetadata.
          </p>
        </article>
        <article className="card">
          <h2>Aplicar workflow</h2>
          <p className="muted">
            Aplica cambios idempotentes en OpenMetadata, exporta el catálogo UCLM en JSON-LD y valida el resultado
            contra las SHACL locales.
          </p>
        </article>
      </section>
      <OperationGrid operations={operations.filter((operation) => ["workflow-dry-run", "workflow-apply"].includes(operation.id))} />
    </div>
  );
}
