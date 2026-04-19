import { ArtifactViewer } from "@/components/ArtifactViewer";

export default function ShaclPage() {
  return (
    <div className="stack">
      <header>
        <h1 className="page-title">SHACL congeladas</h1>
        <p className="lead">Manifiesto local usado por la validación. No se descargan shapes remotas en runtime.</p>
      </header>
      <ArtifactViewer initialPath="tfm_ingestor/src/tfm_ingestor/resources/shacl/manifest.json" />
    </div>
  );
}
