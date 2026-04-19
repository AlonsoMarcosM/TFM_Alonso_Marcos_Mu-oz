import { GovernanceEditor } from "@/components/GovernanceEditor";
import { OperationGrid } from "@/components/OperationGrid";
import { operations } from "@/server/operations";

export default function GobiernoPage() {
  return (
    <div className="stack">
      <header>
        <h1 className="page-title">Gobierno funcional gold</h1>
        <p className="lead">
          Edita los metadatos funcionales de los datasets gold concretos de la PoC. La hoja cubre los campos
          por dataset que decide una persona responsable del catálogo; los demás obligatorios HVD se derivan
          desde la configuración global y el exportador DCAT.
        </p>
      </header>
      <section className="grid">
        <article className="card">
          <h2>Qué significa publicar</h2>
          <p className="muted">
            <strong>si</strong> significa que la tabla gold entra en el catálogo DCAT exportado y debe tener
            título, descripción, publicador, temática, categoría HVD y URL de acceso. <strong>no</strong> deja
            la tabla fuera del contrato publicable de la PoC.
          </p>
        </article>
        <article className="card">
          <h2>Cobertura HVD</h2>
          <p className="muted">
            La hoja no contiene todo DCAT-AP-ES HVD. Contiene la curación funcional por dataset. Catalog,
            legislation, licencias, DataService, contactPoint y páginas de documentación se generan desde
            <code> governance_defaults.yaml</code> y <code> dcat_export.py</code>.
          </p>
        </article>
        <article className="card">
          <h2>Listas controladas</h2>
          <p className="muted">
            <code>tematica_dcat</code> usa los sectores NTI-RISP enumerados en las SHACL congeladas.{" "}
            <code>categoria_hvd</code> usa las seis categorías superiores del vocabulario europeo HVD.
          </p>
        </article>
      </section>
      <GovernanceEditor />
      <OperationGrid operations={operations.filter((operation) => operation.id === "validate-governance-sheet")} />
    </div>
  );
}
