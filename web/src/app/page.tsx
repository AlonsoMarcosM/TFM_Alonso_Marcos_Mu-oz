import { OperationGrid } from "@/components/OperationGrid";
import { listArtifacts } from "@/server/artifacts";
import { envStatus } from "@/server/env";
import { operations } from "@/server/operations";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const env = envStatus();
  const artifacts = await listArtifacts();
  const quick = operations.filter((operation) =>
    [
      "ingest-postgres",
      "bootstrap-governance",
      "refresh-governance-sheet",
      "validate-governance-sheet",
      "workflow-dry-run",
      "workflow-apply",
      "run-validation-suite",
    ].includes(operation.id),
  );

  return (
    <div className="stack">
      <header>
        <h1 className="page-title">Plataforma de Gobierno del Dato sobre OpenMetadata</h1>
        <p className="lead">
          Consola operativa para ejecutar el caso de uso de validación: conectar activos técnicos, gobernar datasets
          gold, exportar el catálogo UCLM en JSON-LD DCAT-AP-ES y revisar evidencias.
        </p>
      </header>
      <section className="grid">
        <article className="card">
          <h2>Qué hace la consola</h2>
          <p className="muted">
            Cada botón lanza una operación cerrada del repositorio: scripts PowerShell o <code>python -m om_dcat_sync</code>.
            La web no ejecuta comandos arbitrarios ni habla directamente con OpenMetadata.
          </p>
        </article>
        <article className="card">
          <h2>Resultado de negocio</h2>
          <p className="muted">
            Los servicios conectados a OpenMetadata forman un catálogo gobernado. La hoja gold aporta la curación por
            dataset y los defaults globales completan las propiedades DCAT-AP-ES/HVD del catálogo UCLM.
          </p>
        </article>
        <article className="card">
          <h2>Configuración</h2>
          <p>.env: {env.exists ? "detectado" : "no detectado"}</p>
          {env.required.map((item) => (
            <p key={item.name} className="muted">
              {item.name}: {item.present ? "presente" : "falta"}
            </p>
          ))}
        </article>
        <article className="card">
          <h2>Evidencias recientes</h2>
          {artifacts.filter((artifact) => artifact.exists).slice(0, 5).map((artifact) => (
            <p key={artifact.path} className="muted">{artifact.path}</p>
          ))}
        </article>
      </section>
      <section>
        <h2>Acciones principales del caso de uso</h2>
        <OperationGrid operations={quick} />
      </section>
    </div>
  );
}
